import os

from dagster import AssetKey, RunRequest, SkipReason, check, sensor
from dagster.core.definitions.pipeline_sensor import (
    PipelineFailureSensorContext,
    pipeline_failure_sensor,
)
from slack import WebClient


def get_directory_files(directory_name, since=None):
    check.str_param(directory_name, "directory_name")
    if not os.path.isdir(directory_name):
        return []

    try:
        since = float(since)
    except (TypeError, ValueError):
        since = None

    files = []
    for filename in os.listdir(directory_name):
        filepath = os.path.join(directory_name, filename)
        if not os.path.isfile(filepath):
            continue
        fstats = os.stat(filepath)
        if not since or fstats.st_mtime > since:
            files.append((filename, fstats.st_mtime))

    return files


def get_toys_sensors():

    directory_name = os.environ.get("DAGSTER_TOY_SENSOR_DIRECTORY")

    @sensor(pipeline_name="log_file_pipeline")
    def toy_file_sensor(context):
        if not directory_name:
            yield SkipReason(
                "No directory specified at environment variable `DAGSTER_TOY_SENSOR_DIRECTORY`"
            )
            return

        if not os.path.isdir(directory_name):
            yield SkipReason(f"Directory {directory_name} not found")
            return

        directory_files = get_directory_files(directory_name, context.cursor)
        if not directory_files:
            yield SkipReason(f"No new files found in {directory_name} (after {context.cursor})")
            return

        for filename, mtime in directory_files:
            yield RunRequest(
                run_key="{}:{}".format(filename, str(mtime)),
                run_config={
                    "solids": {
                        "read_file": {"config": {"directory": directory_name, "filename": filename}}
                    }
                },
            )

    @sensor(pipeline_name="log_asset_pipeline")
    def toy_asset_sensor(context):
        events = context.instance.events_for_asset_key(
            AssetKey(["model"]), after_cursor=context.cursor, ascending=False, limit=1
        )

        if not events:
            return

        record_id, event = events[0]  # take the most recent materialization
        from_pipeline = event.pipeline_name

        yield RunRequest(
            run_key=str(record_id),
            run_config={
                "solids": {
                    "read_materialization": {
                        "config": {"asset_key": ["model"], "pipeline": from_pipeline}
                    }
                }
            },
        )

        context.update_cursor(str(record_id))

    bucket = os.environ.get("DAGSTER_TOY_SENSOR_S3_BUCKET")

    from dagster_aws.s3.sensor import get_s3_keys

    @sensor(pipeline_name="log_s3_pipeline")
    def toy_s3_sensor(context):
        if not bucket:
            raise Exception(
                "S3 bucket not specified at environment variable `DAGSTER_TOY_SENSOR_S3_BUCKET`."
            )

        new_s3_keys = get_s3_keys(bucket, since_key=context.last_run_key)
        if not new_s3_keys:
            yield SkipReason(f"No s3 updates found for bucket {bucket}.")
            return

        for s3_key in new_s3_keys:
            yield RunRequest(
                run_key=s3_key,
                run_config={
                    "solids": {"read_s3_key": {"config": {"bucket": bucket, "s3_key": s3_key}}}
                },
            )

    @pipeline_failure_sensor
    def slack_on_pipeline_failure(context: PipelineFailureSensorContext):

        base_url = "http://localhost:3000"

        # TBD: support resources?
        slack_client = WebClient(token=os.environ["SLACK_DAGSTER_ETL_BOT_TOKEN"])

        run_page_url = f"{base_url}/instance/runs/{context.pipeline_run.run_id}"
        channel = "#yuhan-test"
        message = "\n".join(
            [
                f'Pipeline "{context.pipeline_run.pipeline_name}" failed.',
                f"error: {context.failure_event.message}",
                f"mode: {context.pipeline_run.mode}",
                f"run_page_url: {run_page_url}",
            ]
        )

        slack_client.chat_postMessage(
            channel=channel,
            blocks=[{"type": "section", "text": {"type": "mrkdwn", "text": message}}],
        )

    return [toy_file_sensor, toy_asset_sensor, toy_s3_sensor, slack_on_pipeline_failure]
