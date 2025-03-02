"""isort:skip_file"""

from dagster import repository, SkipReason


# start_sensor_pipeline_marker
from dagster import solid, pipeline


@solid(config_schema={"filename": str})
def process_file(context):
    filename = context.solid_config["filename"]
    context.log.info(filename)


@pipeline
def log_file_pipeline():
    process_file()


# end_sensor_pipeline_marker

MY_DIRECTORY = "./"

# start_directory_sensor_marker
import os
from dagster import sensor, RunRequest


@sensor(pipeline_name="log_file_pipeline")
def my_directory_sensor(_context):
    for filename in os.listdir(MY_DIRECTORY):
        filepath = os.path.join(MY_DIRECTORY, filename)
        if os.path.isfile(filepath):
            yield RunRequest(
                run_key=filename,
                run_config={"solids": {"process_file": {"config": {"filename": filename}}}},
            )


# end_directory_sensor_marker


# start_sensor_testing_no_context
from dagster import validate_run_config


@sensor(pipeline_name="log_file_pipeline")
def sensor_to_test(_context):
    yield RunRequest(
        run_key="foo",
        run_config={"solids": {"process_file": {"config": {"filename": "foo"}}}},
    )


def test_sensor():
    for run_request in sensor_to_test(None):
        assert validate_run_config(log_file_pipeline, run_request.run_config)


# end_sensor_testing_no_context


def isolated_run_request():
    filename = "placeholder"

    # start_run_request_marker

    yield RunRequest(
        run_key=filename,
        run_config={"solids": {"process_file": {"config": {"filename": filename}}}},
    )

    # end_run_request_marker


# start_interval_sensors_maker


@sensor(pipeline_name="my_pipeline", minimum_interval_seconds=30)
def sensor_A(_context):
    yield RunRequest(run_key=None, run_config={})


@sensor(pipeline_name="my_pipeline", minimum_interval_seconds=45)
def sensor_B(_context):
    yield RunRequest(run_key=None, run_config={})


# end_interval_sensors_maker


# start_cursor_sensors_marker
@sensor(pipeline_name="log_file_pipeline")
def my_directory_sensor_cursor(context):
    last_mtime = float(context.cursor) if context.cursor else 0

    max_mtime = last_mtime
    for filename in os.listdir(MY_DIRECTORY):
        filepath = os.path.join(MY_DIRECTORY, filename)
        if os.path.isfile(filepath):
            fstats = os.stat(filepath)
            file_mtime = fstats.st_mtime
            if file_mtime <= last_mtime:
                continue

            # the run key should include mtime if we want to kick off new runs based on file modifications
            run_key = f"{filename}:{str(file_mtime)}"
            run_config = {"solids": {"process_file": {"config": {"filename": filename}}}}
            yield RunRequest(run_key=run_key, run_config=run_config)
            max_mtime = max(max_mtime, file_mtime)

    context.update_cursor(str(max_mtime))


# end_cursor_sensors_marker

# start_sensor_testing_with_context
from dagster import build_sensor_context


def test_my_directory_sensor_cursor():
    context = build_sensor_context(cursor="0")
    for run_request in my_directory_sensor_cursor(context):
        assert validate_run_config(log_file_pipeline, run_request.run_config)


# end_sensor_testing_with_context


# start_skip_sensors_marker
@sensor(pipeline_name="log_file_pipeline")
def my_directory_sensor_with_skip_reasons(_context):
    has_files = False
    for filename in os.listdir(MY_DIRECTORY):
        filepath = os.path.join(MY_DIRECTORY, filename)
        if os.path.isfile(filepath):
            yield RunRequest(
                run_key=filename,
                run_config={"solids": {"process_file": {"config": {"filename": filename}}}},
            )
            has_files = True
    if not has_files:
        yield SkipReason(f"No files found in {MY_DIRECTORY}.")


# end_skip_sensors_marker

# start_asset_sensors_marker
from dagster import AssetKey


@sensor(pipeline_name="my_pipeline")
def my_asset_sensor(context):
    events = context.instance.events_for_asset_key(
        AssetKey("my_table"), after_cursor=context.cursor, ascending=False, limit=1
    )
    if not events:
        return

    record_id, event = events[0]  # take the most recent materialization
    yield RunRequest(
        run_key=str(record_id), run_config={}, tags={"source_pipeline": event.pipeline_name}
    )
    context.update_cursor(str(record_id))


# end_asset_sensors_marker


# start_s3_sensors_marker
from dagster_aws.s3.sensor import get_s3_keys


@sensor(pipeline_name="my_pipeline")
def my_s3_sensor(context):
    new_s3_keys = get_s3_keys("my_s3_bucket", since_key=context.last_run_key)
    if not new_s3_keys:
        yield SkipReason("No new s3 files found for bucket my_s3_bucket.")
        return
    for s3_key in new_s3_keys:
        yield RunRequest(run_key=s3_key, run_config={})


# end_s3_sensors_marker


@pipeline
def my_pipeline():
    pass


@repository
def my_repository():
    return [my_pipeline, log_file_pipeline, my_directory_sensor, sensor_A, sensor_B]
