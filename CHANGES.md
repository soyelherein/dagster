# Changelog

# 0.11.15

### New

- The Python GraphQL client now includes a shutdown_repository_location API call that shuts down a gRPC server. This is useful in situations where you want Kubernetes to restart your server and re-create your repository definitions, even though the underlying Python code hasn’t changed (for example, if your pipelines are loaded programatically from a database)
- io_manager_key and root_manager_key is disallowed on composite solids’ InputDefinitions and OutputDefinitions. Instead, custom IO managers on the solids inside composite solids will be respected:

  ```python
  @solid(input*defs=[InputDefinition("data", dagster_type=str, root_manager_key="my_root")])
  def inner_solid(*, data):
    return data

  @composite_solid
  def my_composite():
    return inner_solid()
  ```

- Schedules can now be directly invoked. This is intended to be used for testing. To learn more, see https://docs.dagster.io/master/concepts/partitions-schedules-sensors/schedules#testing-schedules

### Bugfixes

- Dagster libraries (for example, `dagster-postgres` or `dagster-graphql`) are now pinned to the same version as the core `dagster` package. This should reduce instances of issues due to backwards compatibility problems between Dagster packages.
- Due to a recent regression, when viewing a launched run in Dagit, the Gantt chart would inaccurately show the run as queued well after it had already started running. This has been fixed, and the Gantt chart will now accurately reflect incoming logs.
- In some cases, navigation in Dagit led to overfetching a workspace-level GraphQL query that would unexpectedly reload the entire app. The excess fetches are now limited more aggressively, and the loading state will no longer reload the app when workspace data is already available.
- Previously, execution would fail silently when trying to use memoization with a root input manager. The error message now more clearly states that this is not supported.

### Breaking Changes

- Invoking a generator solid now yields a generator, and output objects are not unpacked.

  ```python
  @solid
  def my_solid():
    yield Output("hello")

  assert isinstance(list(my_solid())[0], Output)
  ```

### Experimental

- Added an experimental [`EcsRunLauncher`](https://github.com/dagster-io/dagster/commit/cb07e82a7bf9a46880359fcffd63e17f6da9bae1#diff-9bf38a50da8f0c910296ba4257fb174d34297d6844031476e9c368c07eae6fba). This creates a new ECS Task Definition and launches a new ECS Task for each run. You can use the new [ECS Reference Deployment](https://github.com/dagster-io/dagster/tree/master/examples/deploy_ecs) to experiment with the `EcsRunLauncher`. We’d love your feedback in our [#dagster-ecs](https://dagster.slack.com/archives/C014UDS8LAV) Slack channel!

### Documentation

- Added docs section on testing hooks. https://docs.dagster.io/master/concepts/solids-pipelines/solid-hooks#experimental-testing-hooks

# 0.11.14

### New

- Supplying the "metadata" argument to InputDefinitions and OutputDefinitions is no longer considered experimental.
- The "context" argument can now be omitted for solids that have required resource keys.
- The S3ComputeLogManager now takes a boolean config argument skip_empty_files, which skips uploading empty log files to S3. This should enable a work around of timeout errors when using the S3ComputeLogManager to persist logs to MinIO object storage.
- The Helm subchart for user code deployments now allows for extra manifests.
- Running `dagit` with flag `--suppress-warnings` will now ignore all warnings, such as ExperimentalWarnings.
- PipelineRunStatus, which represents the run status, is now exported in the public API.

### Bugfixes

- The asset catalog now has better backwards compatibility for supporting deprecated Materialization events. Previously, these events were causing loading errors.

### Community Contributions

- Improved documentation of the `dagster-dbt` library with some helpful tips and example code (thanks @makotonium!).
- Fixed the example code in the `dagster-pyspark` documentation for providing and accessing the pyspark resource (thanks @Andrew-Crosby!).
- Helm chart serviceaccounts now allow annotations (thanks @jrouly!).

### Documentation

- Added section on testing resources ([link](https://docs.dagster.io/master/concepts/modes-resources#experimental-testing-resource-initialization)).
- Revamped IO manager testing section to use `build_input_context` and `build_output_context` APIs ([link](https://docs.dagster.io/master/concepts/io-management/io-managers#testing-an-io-manager)).

# 0.11.13

### New

- Added an example that demonstrates what a complete repository that takes advantage of many Dagster features might look like. Includes usage of IO Managers, modes / resources, unit tests, several cloud service integrations, and more! Check it out at [`examples/hacker_news`](https://github.com/dagster-io/dagster/tree/master/examples/hacker_news)!
- `retry_number` is now available on `SolidExecutionContext`, allowing you to determine within a solid function how many times the solid has been previously retried.
- Errors that are surfaced during solid execution now have clearer stack traces.
- When using Postgres or MySQL storage, the database mutations that initialize Dagster tables on startup now happen in atomic transactions, rather than individual SQL queries.
- For versions >=0.11.13, when specifying the `--version` flag when installing the Helm chart, the tags for Dagster-provided images in the Helm chart will now default to the current Chart version. For `--version` <0.11.13, the image tags will still need to be updated properly to use old chart version.
- Removed the `PIPELINE_INIT_FAILURE` event type. A failure that occurs during pipeline initialization will now produce a `PIPELINE_FAILURE` as with all other pipeline failures.

### Bugfixes

- When viewing run logs in Dagit, in the stdout/stderr log view, switching the filtered step did not work. This has been fixed. Additionally, the filtered step is now present as a URL query parameter.
- The `get_run_status` method on the Python GraphQL client now returns a `PipelineRunStatus` enum instead of the raw string value in order to align with the mypy type annotation. Thanks to Dylan Bienstock for surfacing this bug!
- When a docstring on a solid doesn’t match the reST, Google, or Numpydoc formats, Dagster no longer raises an error.
- Fixed a bug where memoized runs would sometimes fail to execute when specifying a non-default IO manager key.

### Experimental

- Added the[`k8s_job_executor`](https://docs.dagster.io/master/_apidocs/libraries/dagster-k8s#dagster_k8s.k8s_job_executor), which executes solids in separate kubernetes jobs. With the addition of this executor, you can now choose at runtime between single pod and multi-pod isolation for solids in your run. Previously this was only configurable for the entire deployment - you could either use the K8sRunLauncher with the default executors (in_process and multiprocess) for low isolation, or you could use the CeleryK8sRunLauncher with the celery_k8s_job_executor for pod-level isolation. Now, your instance can be configured with the K8sRunLauncher and you can choose between the default executors or the k8s_job_executor.
- The `DagsterGraphQLClient` now allows you to specify whether to use HTTP or HTTPS when connecting to the GraphQL server. In addition, error messages during query execution or connecting to dagit are now clearer. Thanks to @emily-hawkins for raising this issue!
- Added experimental hook invocation functionality. Invoking a hook will call the underlying decorated function. For example:

```
  from dagster import build_hook_context

  my_hook(build_hook_context(resources={"foo_resource": "foo"}))
```

- Resources can now be directly invoked as functions. Invoking a resource will call the underlying decorated initialization function.

```
  from dagster import build_init_resource_context

  @resource(config_schema=str)
  def my_basic_resource(init_context):
      return init_context.resource_config

  context = build_init_resource_context(config="foo")
  assert my_basic_resource(context) == "foo"
```

- Improved the error message when a pipeline definition is incorrectly invoked as a function.

### Documentation

- Added a section on testing custom loggers: https://docs.dagster.io/master/concepts/logging/loggers#testing-custom-loggers

# 0.11.12

### Bugfixes

- `ScheduleDefinition` and `SensorDefinition` now carry over properties from functions decorated by `@sensor` and `@schedule`. Ie: docstrings.
- Fixed a bug with configured on resources where the version set on a `ResourceDefinition` was not being passed to the `ResourceDefinition` created by the call to `configured`.
- Previously, if an error was raised in an `IOManager` `handle_output` implementation that was a generator, it would not be wrapped `DagsterExecutionHandleOutputError`. Now, it is wrapped.
- Dagit will now gracefully degrade if websockets are not available. Previously launching runs and viewing the event logs would block on a websocket conection.

### Experimental

- Added an example of run attribution via a [custom run coordinator](https://github.com/dagster-io/dagster/tree/master/examples/run_attribution_example), which reads a user’s email from HTTP headers on the Dagster GraphQL server and attaches the email as a run tag. Custom run coordinator are also now specifiable in the Helm chart, under `queuedRunCoordinator`. See the [docs](https://docs.dagster.io/master/guides/dagster/run-attribution) for more information on setup.
- `RetryPolicy` now supports backoff and jitter settings, to allow for modulating the `delay` as a function of attempt number and randomness.

### Documentation

- Added an overview section on testing schedules. Note that the `build_schedule_context` and `validate_run_config` functions are still in an experimental state. https://docs.dagster.io/master/concepts/partitions-schedules-sensors/schedules#testing-schedules
- Added an overview section on testing partition sets. Note that the `validate_run_config` function is still in an experimental state. https://docs.dagster.io/master/concepts/partitions-schedules-sensors/partitions#experimental-testing-a-partition-set

## 0.11.11

### New

- [Helm] Added `dagit.enableReadOnly` . When enabled, a separate Dagit instance is deployed in `—read-only` mode. You can use this feature to serve Dagit to users who you do not want to able to kick off new runs or make other changes to application state.
- [dagstermill] Dagstermill is now compatible with current versions of papermill (2.x). Previously we required papermill to be pinned to 1.x.
- Added a new metadata type that links to the asset catalog, which can be invoked using `EventMetadata.asset`.
- Added a new log event type `LOGS_CAPTURED`, which explicitly links to the captured stdout/stderr logs for a given step, as determined by the configured `ComputeLogManager` on the Dagster instance. Previously, these links were available on the `STEP_START` event.
- The `network` key on `DockerRunLauncher` config can now be sourced from an environment variable.
- The Workspace section of the Status page in Dagit now shows more metadata about your workspace, including the python file, python package, and Docker image of each of your repository locations.
- In Dagit, settings for how executions are viewed now persist across sessions.

### Breaking Changes

- The `get_execution_data` method of `SensorDefinition` and `ScheduleDefinition` has been renamed to `evaluate_tick`. We expect few to no users of the previous name, and are renaming to prepare for improved testing support for schedules and sensors.

### Community Contributions

- README has been updated to remove typos (thanks @gogi2811).
- Configured API doc examples have been fixed (thanks @jrouly).

### Experimental

- Documentation on testing sensors using experimental `build_sensor_context` API. See [Testing sensors](https://docs.dagster.io/concepts/partitions-schedules-sensors/sensors#testing-sensors).

### Bugfixes

- Some mypy errors encountered when using the built-in Dagster types (e.g., `dagster.Int` ) as type annotations on functions decorated with `@solid` have been resolved.
- Fixed an issue where the `K8sRunLauncher` sometimes hanged while launching a run due to holding a stale Kubernetes client.
- Fixed an issue with direct solid invocation where default config values would not be applied.
- Fixed a bug where resource dependencies to io managers were not being initialized during memoization.
- Dagit can once again override pipeline tags that were set on the definition, and UI clarity around the override behavior has been improved.
- Markdown event metadata rendering in dagit has been repaired.

### Documentation

- Added documentation on how to deploy Dagster infrastructure separately from user code. See [Separately Deploying Dagster infrastructure and User Code](https://docs.dagster.io/deployment/guides/kubernetes/customizing-your-deployment#separately-deploying-dagster-infrastructure-and-user-code).

## 0.11.10

### New

- Sensors can now set a string cursor using `context.update_cursor(str_value)` that is persisted across evaluations to save unnecessary computation. This persisted string value is made available on the context as `context.cursor`. Previously, we encouraged cursor-like behavior by exposing `last_run_key` on the sensor context, to keep track of the last time the sensor successfully requested a run. This, however, was not useful for avoiding unnecessary computation when the sensor evaluation did not result in a run request.
- Dagit may now be run in `--read-only` mode, which will disable mutations in the user interface and on the server. You can use this feature to run instances of Dagit that are visible to users who you do not want to able to kick off new runs or make other changes to application state.
- In `dagster-pandas`, the `event_metadata_fn` parameter to the function `create_dagster_pandas_dataframe_type` may now return a dictionary of `EventMetadata` values, keyed by their string labels. This should now be consistent with the parameters accepted by Dagster events, including the `TypeCheck` event.

```py
# old
MyDataFrame = create_dagster_pandas_dataframe_type(
    "MyDataFrame",
    event_metadata_fn=lambda df: [
        EventMetadataEntry.int(len(df), "number of rows"),
        EventMetadataEntry.int(len(df.columns), "number of columns"),
    ]
)

# new
MyDataFrame = create_dagster_pandas_dataframe_type(
    "MyDataFrame",
    event_metadata_fn=lambda df: {
        "number of rows": len(df),
        "number of columns": len(dataframe.columns),
    },
)
```

- dagster-pandas’ `PandasColumn.datetime_column()` now has a new `tz` parameter, allowing you to constrain the column to a specific timezone (thanks `@mrdavidlaing`!)
- The `DagsterGraphQLClient` now takes in an optional `transport` argument, which may be useful in cases where you need to authenticate your GQL requests:

```py
authed_client = DagsterGraphQLClient(
    "my_dagit_url.com",
    transport=RequestsHTTPTransport(..., auth=<some auth>),
)
```

- Added an `ecr_public_resource` to get login credentials for the AWS ECR Public Gallery. This is useful if any of your pipelines need to push images.
- Failed backfills may now be resumed in Dagit, by putting them back into a “requested” state. These backfill jobs should then be picked up by the backfill daemon, which will then attempt to create and submit runs for any of the outstanding requested partitions . This should help backfill jobs recover from any deployment or framework issues that occurred during the backfill prior to all the runs being launched. This will not, however, attempt to re-execute any of the individual pipeline runs that were successfully launched but resulted in a pipeline failure.
- In the run log viewer in Dagit, links to asset materializations now include the timestamp for that materialization. This will bring you directly to the state of that asset at that specific time.
- The Databricks step launcher now includes a `max_completion_wait_time_seconds` configuration option, which controls how long it will wait for a Databricks job to complete before exiting.

### Experimental

- Solids can now be invoked outside of composition. If your solid has a context argument, the `build_solid_context` function can be used to provide a context to the invocation.

```py
from dagster import build_solid_context

@solid
def basic_solid():
    return "foo"

assert basic_solid() == 5

@solid
def add_one(x):
    return x + 1

assert add_one(5) == 6

@solid(required_resource_keys={"foo_resource"})
def solid_reqs_resources(context):
    return context.resources.foo_resource + "bar"

context = build_solid_context(resources={"foo_resource": "foo"})
assert solid_reqs_resources(context) == "foobar"
```

- `build_schedule_context` allows you to build a `ScheduleExecutionContext` using a `DagsterInstance`. This can be used to test schedules.

```py
from dagster import build_schedule_context

with DagsterInstance.get() as instance:
    context = build_schedule_context(instance)
    my_schedule.get_execution_data(context)
```

- `build_sensor_context` allows you to build a `SensorExecutionContext` using a `DagsterInstance`. This can be used to test sensors.

```py

from dagster import build_sensor_context

with DagsterInstance.get() as instance:
    context = build_sensor_context(instance)
    my_sensor.get_execution_data(context)
```

- `build_input_context` and `build_output_context` allow you to construct `InputContext` and `OutputContext` respectively. This can be used to test IO managers.

```py
from dagster import build_input_context, build_output_context

io_manager = MyIoManager()

io_manager.load_input(build_input_context())
io_manager.handle_output(build_output_context(), val)
```

- Resources can be provided to either of these functions. If you are using context manager resources, then `build_input_context`/`build_output_context` must be used as a context manager.

```py
with build_input_context(resources={"cm_resource": my_cm_resource}) as context:
    io_manager.load_input(context)
```

- `validate_run_config` can be used to validate a run config blob against a pipeline definition & mode. If the run config is invalid for the pipeline and mode, this function will throw an error, and if correct, this function will return a dictionary representing the validated run config that Dagster uses during execution.

```py
validate_run_config(
    {"solids": {"a": {"config": {"foo": "bar"}}}},
    pipeline_contains_a
) # usage for pipeline that requires config

validate_run_config(
    pipeline_no_required_config
) # usage for pipeline that has no required config
```

- The ability to set a `RetryPolicy` has been added. This allows you to declare automatic retry behavior when exceptions occur during solid execution. You can set `retry_policy` on a solid invocation, `@solid` definition, or `@pipeline` definition.

```py
@solid(retry_policy=RetryPolicy(max_retries=3, delay=5))
def fickle_solid(): # ...

@pipeline( # set a default policy for all solids
solid_retry_policy=RetryPolicy()
)
def my_pipeline(): # will use the pipelines policy by default
    some_solid()

    # solid definition takes precedence over pipeline default
    fickle_solid()

    # invocation setting takes precedence over definition
    fickle_solid.with_retry_policy(RetryPolicy(max_retries=2))
```

### Bugfixes

- Previously, asset materializations were not working in dagster-dbt for dbt >= 0.19.0. This has been fixed.
- Previously, using the `dagster/priority` tag directly on pipeline definitions would cause an error. This has been fixed.
- In dagster-pandas, the `create_dagster_pandas_dataframe_type()` function would, in some scenarios, not use the specified `materializer` argument when provided. This has been fixed (thanks `@drewsonne`!)
- `dagster-graphql --remote` now sends the query and variables as post body data, avoiding uri length limit issues.
- In the Dagit pipeline definition view, we no longer render config nubs for solids that do not need them.
- In the run log viewer in Dagit, truncated row contents (including errors with long stack traces) now have a larger and clearer button to expand the full content in a dialog.
- [dagster-mysql] Fixed a bug where database connections accumulated by `sqlalchemy.Engine` objects would be invalidated after 8 hours of idle time due to MySQL’s default configuration, resulting in an `sqlalchemy.exc.OperationalError` when attempting to view pages in Dagit in long-running deployments.

### Documentation

- In 0.11.9, context was made an optional argument on the function decorated by @solid. The solids throughout tutorials and snippets that do not need a context argument have been altered to omit that argument, and better reflect this change.
- In a previous docs revision, a tutorial section on accessing resources within solids was removed. This has been re-added to the site.

## 0.11.9

### New

- In Dagit, assets can now be viewed with an `asOf` URL parameter, which shows a snapshot of the asset at the provided timestamp, including parent materializations as of that time.
- [Dagit] Queries and Mutations now use HTTP instead of a websocket-based connection.

### Bugfixes

- A regression in 0.11.8 where composites would fail to render in the right side bar in Dagit has been fixed.
- A dependency conflict in `make dev_install` has been fixed.
- [dagster-python-client] `reload_repository_location` and `submit_pipeline_execution` have been fixed - the underlying GraphQL queries had a missing inline fragment case.

### Community Contributions

- AWS S3 resources now support named profiles (thanks @deveshi!)
- The Dagit ingress path is now configurable in our Helm charts (thanks @orf!)
- Dagstermill’s use of temporary files is now supported across operating systems (thanks @slamer59!)
- Deploying with Helm documentation has been updated to reflect the correct name for “dagster-user-deployments” (thanks @hebo-yang!)
- Deploying with Helm documentation has been updated to suggest naming your release “dagster” (thanks @orf!)
- Solids documentation has been updated to remove a typo (thanks @dwallace0723!)
- Schedules documentation has been updated to remove a typo (thanks @gdoron!)

## 0.11.8

### New

- The `@solid` decorator can now wrap a function without a `context` argument, if no context information is required. For example, you can now do:

```py
@solid
def basic_solid():
    return 5

@solid
def solid_with_inputs(x, y):
    return x + y

```

however, if your solid requires config or resources, then you will receive an error at definition time.

- It is now simpler to provide structured metadata on events. Events that take a `metadata_entries` argument may now instead accept a `metadata` argument, which should allow for a more convenient API. The `metadata` argument takes a dictionary with string labels as keys and `EventMetadata` values. Some base types (`str`, `int`, `float`, and JSON-serializable `list`/`dict`s) are also accepted as values and will be automatically coerced to the appropriate `EventMetadata` value. For example:

```py
@solid
def old_metadata_entries_solid(df):
   yield AssetMaterialization(
       "my_asset",
       metadata_entries=[
           EventMetadataEntry.text("users_table", "table name"),
           EventMetadataEntry.int(len(df), "row count"),
           EventMetadataEntry.url("http://mysite/users_table", "data url")
       ]
   )

@solid
def new_metadata_solid(df):
    yield AssetMaterialization(
       "my_asset",
       metadata={
           "table name": "users_table",
           "row count": len(df),
           "data url": EventMetadata.url("http://mysite/users_table")
       }
   )

```

- The dagster-daemon process now has a `--heartbeat-tolerance` argument that allows you to configure how long the process can run before shutting itself down due to a hanging thread. This parameter can be used to troubleshoot failures with the daemon process.
- When creating a schedule from a partition set using `PartitionSetDefinition.create_schedule_definition`, the `partition_selector` function that determines which partition to use for a given schedule tick can now return a list of partitions or a single partition, allowing you to create schedules that create multiple runs for each schedule tick.

### Bugfixes

- Runs submitted via backfills can now correctly resolve the source run id when loading inputs from previous runs instead of encountering an unexpected `KeyError`.
- Using nested `Dict` and `Set` types for solid inputs/outputs now works as expected. Previously a structure like `Dict[str, Dict[str, Dict[str, SomeClass]]]` could result in confusing errors.
- Dagstermill now correctly loads the config for aliased solids instead of loading from the incorrect place which would result in empty `solid_config`.
- Error messages when incomplete run config is supplied are now more accurate and precise.
- An issue that would cause `map` and `collect` steps downstream of other `map` and `collect` steps to mysteriously not execute when using multiprocess executors has been resolved.

### Documentation

- Typo fixes and improvements (thanks @elsenorbw (https://github.com/dagster-io/dagster/commits?author=elsenorbw) !)
- Improved documentation for scheduling partitions

## 0.11.7

### New

- For pipelines with tags defined in code, display these tags in the Dagit playground.
- On the Dagit asset list page, use a polling query to regularly refresh the asset list.
- When viewing the Dagit asset list, persist the user’s preference between the flattened list view and the directory structure view.
- Added `solid_exception` on `HookContext` which returns the actual exception object thrown in a failed solid. See the example “[Accessing failure information in a failure hook](https://docs.dagster.io/concepts/solids-pipelines/solid-hooks#accessing-failure-information-in-a-failure-hook)“ for more details.
- Added `solid_output_values` on `HookContext` which returns the computed output values.
- Added `make_values_resource` helper for defining a resource that passes in user-defined values. This is useful when you want multiple solids to share values. See the [example](https://docs.dagster.io/concepts/configuration/config-schema#passing-configuration-to-multiple-solids-in-a-pipeline) for more details.
- StartupProbes can now be set to disabled in Helm charts. This is useful if you’re running on a version earlier than Kubernetes 1.16.

### Bugfixes

- Fixed an issue where partial re-execution was not referencing the right source run and failed to load the correct persisted outputs.
- When running Dagit with `--path-prefix`, our color-coded favicons denoting the success or failure of a run were not loading properly. This has been fixed.
- Hooks and tags defined on solid invocations now work correctly when executing a pipeline with a solid subselection
- Fixed an issue where heartbeats from the dagster-daemon process would not appear on the Status page in dagit until the process had been running for 30 seconds
- When filtering runs, Dagit now suggests all “status:” values and other auto-completions in a scrolling list
- Fixed asset catalog where nested directory structure links flipped back to the flat view structure

### Community Contributions

- [Helm] The Dagit service port is now configurable (thanks @trevenrawr!)
- [Docs] Cleanup & updating visual aids (thanks @keypointt!)

### Experimental

- [Dagster-GraphQL] Added an official Python Client for Dagster’s GraphQL API ([GH issue #2674](https://github.com/dagster-io/dagster/issues/2674)). Docs can be found [here](https://docs.dagster.io/concepts/dagit/graphql-client)

### Documentation

- Fixed a confusingly-worded header on the Solids/Pipelines Testing page

## 0.11.6

### Breaking Changes

- `DagsterInstance.get()` no longer falls back to an ephemeral instance if `DAGSTER_HOME` is not set. We don’t expect this to break normal workflows. This change allows our tooling to be more consistent around it’s expectations. If you were relying on getting an ephemeral instance you can use `DagsterInstance.ephemeral()` directly.
- Undocumented attributes on `HookContext` have been removed. `step_key` and `mode_def` have been documented as attributes.

### New

- Added a permanent, linkable panel in the Run view in Dagit to display the raw compute logs.
- Added more descriptive / actionable error messages throughout the config system.
- When viewing a partitioned asset in Dagit, display only the most recent materialization for a partition, with a link to view previous materializations in a dialog.
- When viewing a run in Dagit, individual log line timestamps now have permalinks. When loading a timestamp permalink, the log table will highlight and scroll directly to that line.
- The default `config_schema` for all configurable objects - solids, resources, IO managers, composite solids, executors, loggers - is now `Any`. This means that you can now use configuration without explicitly providing a `config_schema`. Refer to the docs for more details: https://docs.dagster.io/concepts/configuration/config-schema.
- When launching an out of process run, resources are no longer initialized in the orchestrating process. This should give a performance boost for those using out of process execution with heavy resources (ie, spark context).
- `input_defs` and `output_defs` on `@solid` will now flexibly combine data that can be inferred from the function signature that is not declared explicitly via `InputDefinition` / `OutputDefinition`. This allows for more concise defining of solids with reduced repetition of information.
- [Helm] Postgres storage configuration now supports connection string parameter keywords.
- The Status page in Dagit will now display errors that were surfaced in the `dagster-daemon` process within the last 5 minutes. Previously, it would only display errors from the last 30 seconds.
- Hanging sensors and schedule functions will now raise a timeout exception after 60 seconds, instead of crashing the `dagster-daemon` process.
- The `DockerRunLauncher` now accepts a `container_kwargs` config parameter, allowing you to specify any argument to the run container that can be passed into the Docker containers.run method. See https://docker-py.readthedocs.io/en/stable/containers.html#docker.models.containers.ContainerCollection.run for the full list of available options.
- Added clearer error messages for when a Partition cannot be found in a Partition Set.
- The `celery_k8s_job_executor` now accepts a `job_wait_timeout` allowing you to override the default of 24 hours.

### Bugfixes

- Fixed the raw compute logs in Dagit, which were not live updating as the selected step was executing.
- Fixed broken links in the Backfill table in Dagit when Dagit is started with a `--prefix-path` argument.
- Showed failed status of backfills in the Backfill table in Dagit, along with an error stack trace. Previously, the backfill jobs were stuck in a `Requested` state.
- Previously, if you passed a non-required Field to the `output_config_schema` or `input_config_schema` arguments of `@io_manager`, the config would still be required. Now, the config is not required.
- Fixed nested subdirectory views in the `Assets` catalog, where the view switcher would flip back from the directory view to the flat view when navigating into subdirectories.
- Fixed an issue where the `dagster-daemon` process would crash if it experienced a transient connection error while connecting to the Dagster database.
- Fixed an issue where the `dagster-airflow scaffold` command would raise an exception if a preset was specified.
- Fixed an issue where Dagit was not including the error stack trace in the Status page when a repository failed to load.

## 0.11.5

### New

- Resources in a `ModeDefinition` that are not required by a pipeline no longer require runtime configuration. This should make it easier to share modes or resources among multiple pipelines.
- Dagstermill solids now support retries when a `RetryRequested` is yielded from a notebook using `dagstermill.yield_event`.
- In Dagit, the asset catalog now supports both a flattened view of all assets as well as a hierarchical directory view.
- In Dagit, the asset catalog now supports bulk wiping of assets.

### Bugfixes

- In the Dagit left nav, schedules and sensors accurately reflect the filtered repositories.
- When executing a pipeline with a subset of solids, the config for solids not included in the subset is correctly made optional in more cases.
- URLs were sometimes not prefixed correctly when running Dagit using the `--path-prefix` option, leading to failed GraphQL requests and broken pages. This bug was introduced in 0.11.4, and is now fixed.
- The `update_timestamp` column in the runs table is now updated with a UTC timezone, making it consistent with the `create_timestamp` column.
- In Dagit, the main content pane now renders correctly on ultra-wide displays.
- The partition run matrix on the pipeline partition tab now shows step results for composite solids and dynamically mapped solids. Previously, the step status was not shown at all for these solids.
- Removed dependency constraint of `dagster-pandas` on `pandas`. You can now include any version of pandas. (https://github.com/dagster-io/dagster/issues/3350)
- Removed dependency on `requests` in `dagster`. Now only `dagit` depends on `requests.`
- Removed dependency on `pyrsistent` in `dagster`.

### Documentation

- Updated the “Deploying to Airflow” documentation to reflect the current state of the system.

## 0.11.4

### Community Contributions

- Fix typo in `--config` help message (thanks [@pawelad](https://github.com/pawelad) !)

### Breaking Changes

- Previously, when retrieving the outputs from a run of `execute_pipeline`, the system would use the io manager that handled each output to perform the retrieval. Now, when using `execute_pipeline` with the default in-process executor, the system directly captures the outputs of solids for use with the result object returned by `execute_pipeline`. This may lead to slightly different behavior when retrieving outputs if switching between executors and using custom IO managers.

### New

- The `K8sRunLauncher` and `CeleryK8sRunLauncher` now add a `dagster/image` tag to pipeline runs to document the image used. The `DockerRunLauncher` has also been modified to use this tag (previously it used `docker/image`).
- In Dagit, the left navigation is now collapsible on smaller viewports. You can use the `.` key shortcut to toggle visibility.
- `@solid` can now decorate async def functions.

### Bugfixes

- In Dagit, a GraphQL error on partition sets related to missing fragment `PartitionGraphFragment` has been fixed.
- The compute log manager now handles base directories containing spaces in the path.
- Fixed a bug where re-execution was not working if the initial execution failed, and execution was delegated to other machines/process (e.g. using the multiprocess executor)
- The same solid can now collect over multiple dynamic outputs

## 0.11.3

### Breaking Changes

- Schedules and sensors that target a `pipeline_name` that is not present in the current repository will now error out when the repository is created.

### New

- Assets are now included in Dagit global search. The search bar has also been moved to the top of the app.
- [helm] `generatePostgresqlPasswordSecret` toggle was added to allow the Helm chart to reference an external secret containing the Postgresql password (thanks @PenguinToast !)
- [helm] The Dagster Helm chart is now hosted on [Artifact Hub](https://artifacthub.io/packages/search?page=1&org=dagster).
- [helm] The workspace can now be specified under `dagit.workspace`, which can be useful if you are managing your user deployments in a separate Helm release.

### Bugfixes

- In Dagit, toggling schedules and sensors on or off will now immediately update the green dot in the left navigation, without requiring a refresh.
- When evaluating `dict` values in `run_config` targeting `Permissive` / `dict` config schemas, the ordering is now preserved.
- Integer values for `EventMetadataEntry.int` greater than 32 bits no longer cause `dagit` errors.
- `PresetDefinition.with_additional_config` no longer errors if the base config was empty (thanks @esztermarton !)
- Fixed limitation on gRPC message size when evaluating run requests for sensors, schedules, and backfills. Previously, a gRPC error would be thrown with status code `StatusCode.RESOURCE_EXHAUSTED` for a large number of run requests, especially when the requested run configs were large.
- Changed backfill job status to reflect the number of successful runs against the number of partitions requested instead of the number of runs requested. Normally these two numbers are the same, but they can differ if a pipeline run initiated by the backfill job is re-executed manually.

### Documentation

- Corrections from the community - thanks @mrdavidlaing & @a-cid !

## 0.11.2

**Community Contributions**

- `dagster new project` now scaffolds `setup.py` using your local `dagster` pip version (thanks @taljaards!)
- Fixed an issue where legacy examples were not ported over to the new documentation site (thanks @keypointt!)

**New**

- If a solid-decorated function has a docstring, and no `description` is provided to the solid decorator, the docstring will now be used as the solid’s description.

**Bugfixes**

- In 0.11.0, we introduced the ability to auto-generate Dagster Types from PEP 484 type annotations on solid arguments and return values. However, when clicked on in Dagit, these types would show “Type Not Found” instead of rendering a description. This has been fixed.
- Fixed an issue where the `dagster api execute_step` will mistakenly skip a step and output a non-DagsterEvent log. This affected the `celery_k8s_job_executor`.
- Fixed an issue where NaN floats were not properly handled by Dagit metadata entries.
- Fixed an issue where Dagit run tags were unclickable.
- Fixed an issue where backfills from failures were not able to be scheduled from Dagit.

**Integrations**

- [Helm] A global service account name can now be specified, which will result in the same service account name to be referenced across all parts of the Dagster Kubernetes deployment.
- [Helm] Fixed an issue where user deployments did not update, even if their dependent config maps had changed.

## 0.11.1

**Community Contributions**

- Fixed `dagster new-project`, which broke on the 0.11.0 release (Thank you @saulius!)
- Docs fixes (Thanks @michaellynton and @zuik!)

**New**

- The left navigation in Dagit now allows viewing more than one repository at a time. Click “Filter” to choose which repositories to show.
- In dagster-celery-k8s, you can now specify a custom container image to use for execution in executor config. This image will take precedence over the image used for the user code deployment.

**Bugfixes**

- Previously, fonts were not served correctly in Dagit when using the `--path-prefix option`. Custom fonts and their CSS have now been removed, and system fonts are now used for both normal and monospace text.
- In Dagit, table borders are now visible in Safari.
- Stopping and starting a sensor was preventing future sensor evaluations due to a timezone issue when calculating the minimum interval from the last tick timestamp. This is now fixed.
- The blank state for the backfill table is now updated to accurately describe the empty state.
- Asset catalog entries were returning an error if they had not been recently materialized since (since 0.11.0). Our asset queries are now backwards compatible to read from old materializations.
- Backfills can now successfully be created with step selections even for partitions that did not have an existing run.
- Backfill progress were sometimes showing negative counts for the “Skipped” category, when backfill runs were manually re-executed. This has now been amended to adjust the total run counts to include manually re-executed runs.

## 0.11.0

### Major Changes

- **MySQL is now supported as a backend for storages** you can now run your Dagster Instance on top of MySQL instead of Postgres. See the docs for how to configure MySQL for [Event Log Storage](https://docs.dagster.io/deployment/dagster-instance#mysqleventlogstorage), [Run Storage](https://docs.dagster.io/deployment/dagster-instance#mysqlrunstorage), and [Schedule Storage](https://docs.dagster.io/deployment/dagster-instance#mysqlschedulestorage).
- A new **backfills page** in Dagit lets you monitor and cancel currently running backfills. Backfills are now managed by the Dagster Daemon, which means you can launch backfills over thousands of partitions without risking crashing your Dagit server.
- [Experimental] Dagster now helps you track the **lineage of assets**. You can attach `AssetKeys` to solid outputs through either the `OutputDefinition` or `IOManager`, which allows Dagster to automatically generate asset lineage information for assets referenced in this way. Direct parents of an asset will appear in the Dagit Asset Catalog. See the [asset docs](https://docs.dagster.io/concepts/assets/asset-materializations) to learn more.
- [Experimental] A **collect operation for dynamic orchestration** allows you to run solids that take a set of dynamically mapped outputs as an input. Building on the dynamic orchestration features of `DynamicOutput` and `map` from the last release, this release includes the ability to `collect` over dynamically mapped outputs. You can see an example [here](http://docs.dagster.io/concepts/solids-pipelines/pipelines#dynamic-mapping%E2%80%94collect).
- Dagster has a new **documentation site**. The URL is still [https://docs.dagster.io](https://docs.dagster.io/), but the site has a new design and updated content. If you’re on an older version of Dagster, you can still view pre-0.11.0 documentation at [https://legacy-docs.dagster.io](https://legacy-docs.dagster.io/).
- **dagster new-project** is a new CLI command that generates a Dagster project with skeleton code on your filesystem. [Learn how to use it here.](https://docs.dagster.io/getting-started/create-new-project)

### Additions

#### Core

- Sensors and Schedules
  - Added a `partition_days_offset` argument to the `@daily_schedule` decorator that allows you to customize which partition is used for each execution of your schedule. The default value of this parameter is `1`, which means that a schedule that runs on day N will fill in the partition for day N-1. To create a schedule that uses the partition for the current day, set this parameter to `0`, or increase it to make the schedule use an earlier day’s partition. Similar arguments have also been added for the other partitioned schedule decorators (`@monthly_schedule`, `@weekly_schedule`, and `@hourly_schedule`).ar
  - Both sensors and schedule definitions support a `description` parameter that takes in a human-readable string description and displays it on the corresponding landing page in Dagit.
- Assets
  - [Experimental] `AssetMaterialization` now accepts a `tags` argument. Tags can be used to filter assets in Dagit.
  - Added support for assets to the default SQLite event log storage.
- Daemon
  - The `QueuedRunCoordinator` daemon is now more resilient to errors while dequeuing runs. Previously runs which could not launch would block the queue. They will now be marked as failed and removed from the queue.
  - The `dagster-daemon` process uses fewer resources and spins up fewer subprocesses to load pipeline information. Previously, the scheduler, sensor, and run queue daemon each spun up their own process for this–now they share a single process.
  - The `dagster-daemon` process now runs each of its daemons in its own thread. This allows the scheduler, sensor loop, and daemon for launching queued runs to run in parallel, without slowing each other down.
- Deployment
  - When specifying the location of a gRPC server in your `workspace.yaml` file to load your pipelines, you can now specify an environment variable for the server’s hostname and port.
  - When deploying your own gRPC server for your pipelines, you can now specify that connecting to that server should use a secure SSL connection.
- When a solid-decorated function has a Python type annotation and no Dagster type has been explicitly registered for that Python type, Dagster now automatically constructs a corresponding Dagster type instead of raising an error.
- Added a `dagster run delete` CLI command to delete a run and its associated event log entries.
- `fs_io_manager` now defaults the base directory to `base_dir` via the Dagster instance’s `local_artifact_storage` configuration. Previously, it defaulted to the directory where the pipeline was executed.
- When user code raises an error inside `handle_output`, `load_input`, or a type check function, the log output now includes context about which input or output the error occurred during.
- We have added the `BoolSource` config type (similar to the `StringSource` type). The config value for this type can be a boolean literal or a pointer to an environment variable that is set to a boolean value.
- When trying to run a pipeline where every step has been memoized, you now get a `DagsterNoStepsToExecuteException`.
- The `OutputContext` passed to the `has_output` method of `MemoizableIOManager` now includes a working `log`.

#### Dagit

- After manually reloading the current repository, users will now be prompted to regenerate preset-based or partition-set-based run configs in the Playground view. This helps ensure that the generated run config is up to date when launching new runs. The prompt does not occur when the repository is automatically reloaded.
- Added ability to preview runs for upcoming schedule ticks.
- Dagit now has a global search feature in the left navigation, allowing you to jump quickly to pipelines, schedules, sensors, and partition sets across your workspace. You can trigger search by clicking the search input or with the / keyboard shortcut.
- Timestamps in Dagit have been updated to be more consistent throughout the app, and are now localized based on your browser’s settings.
- In Dagit, a repository location reload button is now available in the header of every pipeline, schedule, and sensor page.
- You can now makes changes to your `workspace.yaml` file without restarting Dagit. To reload your workspace, navigate to the Status page and press the “Reload all” button in the Workspace section.
- When viewing a run in Dagit, log filtering behavior has been improved. `step` and `type` filtering now offers fuzzy search, all log event types are now searchable, and visual bugs within the input have been repaired. Additionally, the default setting for “Hide non-matches” has been flipped to `true`.
- When using a `grpc_server` repository location, Dagit will automatically detect changes and prompt you to reload when the remote server updates.
- When launching a backfill from Dagit, the “Re-execute From Last Run” option has been removed, because it had confusing semantics. “Re-execute From Failure” now includes a tooltip.
- Added a secondary index to improve performance when querying run status.
- The asset catalog now displays a flattened view of all assets, along with a filter field. Tags from AssetMaterializations can be used to filter the catalog view.
- The asset catalog now enables wiping an individual assets from an action in the menu. Bulk wipes of assets is still only supported with the CLI command `dagster asset wipe`.

#### Integrations

- [dagster-snowflake] `snowflake_resource` can now be configured to use the SQLAlchemy connector (thanks @basilvetas!)
- [dagster-pagerduty / dagster-slack] Added built-in hook integrations to create Pagerduty/Slack alerts when solids fail.
- [dagstermill] Users can now specify custom tags & descriptions for notebook solids.
- [dagster-dbt] The dbt commands `seed` and `docs generate` are now available as solids in the library `dagster-dbt`. (thanks [@dehume-drizly](https://github.com/dehume-drizly)!)
- [dagster-spark] - The `dagster-spark` config schemas now support loading values for all fields via environment variables.
- [dagster-gcp] The `gcs_pickle_io_manager` now also retries on 403 Forbidden errors, which previously would only retry on 429 TooManyRequests.

#### Kubernetes/Helm

- Users can set Kubernetes labels on Celery worker deployments
- Users can set environment variables for Flower deployment
- The Redis helm chart is now included as an optional dagster helm chart dependency
- `K8sRunLauncher` and `CeleryK8sRunLauncher` no longer reload the pipeline being executed just before launching it. The previous behavior ensured that the latest version of the pipeline was always being used, but was inconsistent with other run launchers. Instead, to ensure that you’re running the latest version of your pipeline, you can refresh your repository in Dagit by pressing the button next to the repository name.
- Added a flag to the Dagster helm chart that lets you specify that the cluster already has a redis server available, so the Helm chart does not need to create one in order to use redis as a messaging queue. For more information, see the Helm chart’s values.yaml file.
- Celery queues can now be configured with different node selectors. Previously, configuring a node selector applied it to all Celery queues.
- When setting `userDeployments.deployments` in the Helm chart, `replicaCount` now defaults to 1 if not specified.
- Changed our weekly docker image releases (the default images in the helm chart). `dagster/dagster-k8s` and `dagster/dagster-celery-k8s` can be used for all processes which don't require user code (Dagit, Daemon, and Celery workers when using the CeleryK8sExecutor). `user-code-example` can be used for a sample user repository. The prior images (`k8s-dagit`, `k8s-celery-worker`, `k8s-example`) are deprecated.
- All images used in our Helm chart are now fully qualified, including a registry name. If you are encountering rate limits when attempting to pull images from DockerHub, you can now edit the Helm chart to pull from a registry of your choice.
- We now officially use Helm 3 to manage our Dagster Helm chart.
- We are now publishing the `dagster-k8s`, `dagster-celery-k8s`, `user-code-example`, and `k8s-dagit-example` images to a public ECR registry in addition to DockerHub. If you are encountering rate limits when attempting to pull images from DockerHub, you should now be able to pull these images from public.ecr.aws/dagster.
- `.Values.dagsterHome` is now a global variable, available at `.Values.global.dagsterHome`.
- `.Values.global.postgresqlSecretName` has been introduced, for subcharts to access the Dagster Helm chart’s generated Postgres secret properly.
- `.Values.userDeployments` has been renamed `.Values.dagster-user-deployments` to reference the subchart’s values. When using Dagster User Deployments, enabling `.Values.dagster-user-deployments.enabled` will create a `workspace.yaml` for Dagit to locate gRPC servers with user code. To create the actual gRPC servers, `.Values.dagster-user-deployments.enableSubchart` should be enabled. To manage the gRPC servers in a separate Helm release, `.Values.dagster-user-deployments.enableSubchart` should be disabled, and the subchart should be deployed in its own helm release.

### Breaking changes

- Schedules now run in UTC (instead of the system timezone) if no timezone has been set on the schedule. If you’re using a deprecated scheduler like `SystemCronScheduler` or `K8sScheduler`, we recommend that you switch to the native Dagster scheduler. The deprecated schedulers will be removed in the next Dagster release.
- Names provided to `alias` on solids now enforce the same naming rules as solids. You may have to update provided names to meet these requirements.
- The `retries` method on `Executor` should now return a `RetryMode` instead of a `Retries`. This will only affect custom `Executor` classes.

- Submitting partition backfills in Dagit now requires `dagster-daemon` to be running. The instance setting in `dagster.yaml` to optionally enable daemon-based backfills has been removed, because all backfills are now daemon-based backfills.

```
# removed, no longer a valid setting in dagster.yaml
    backfill:
      daemon_enabled: true
```

The corresponding value flag `dagsterDaemon.backfill.enabled` has also been removed from the Dagster helm chart.

- The sensor daemon interval settings in `dagster.yaml` has been removed. The sensor daemon now runs in a continuous loop so this customization is no longer useful.

```
# removed, no longer a valid setting in dagster.yaml
    sensor_settings:
      interval_seconds: 10
```

#### Removal of deprecated APIs

- The `instance` argument to `RunLauncher.launch_run` has been removed. If you have written a custom RunLauncher, you’ll need to update the signature of that method. You can still access the `DagsterInstance` on the `RunLauncher` via the `_instance` parameter.
- The `has_config_entry`, `has_configurable_inputs`, and `has_configurable_outputs` properties of `solid` and `composite_solid` have been removed.
- The deprecated optionality of the `name` argument to `PipelineDefinition` has been removed, and the argument is now required.
- The `execute_run_with_structured_logs` and `execute_step_with_structured_logs` internal CLI entry points have been removed. Use `execute_run` or `execute_step` instead.
- The `python_environment` key has been removed from `workspace.yaml`. Instead, to specify that a repository location should use a custom python environment, set the `executable_path` key within a `python_file`, `python_module`, or `python_package` key. See [the docs](https://docs.dagster.io/concepts/repositories-workspaces/workspaces) for more information on configuring your `workspace.yaml` file.
- [dagster-dask] The deprecated schema for reading or materializing dataframes has been removed. Use the `read` or `to` keys accordingly.

## 0.10.9

**Bugfixes**

- Fixed an issue where postgres databases were unable to initialize the Dagster schema or migrate to a newer version of the Dagster schema. (Thanks [@wingyplus](https://github.com/wingyplus) for submitting the fix!)

## 0.10.8

**Community Contributions**

- [dagster-dbt] The dbt commands `seed` and `docs generate` are now available as solids in the
  library `dagster-dbt`. (thanks [@dehume-drizly](https://github.com/dehume-drizly)!)

**New**

- Dagit now has a global search feature in the left navigation, allowing you to jump quickly to
  pipelines, schedules, and sensors across your workspace. You can trigger search by clicking the
  search input or with the / keyboard shortcut.
- Timestamps in Dagit have been updated to be more consistent throughout the app, and are now
  localized based on your browser’s settings.
- Adding `SQLPollingEventWatcher` for alternatives to filesystem or DB-specific listen/notify
  functionality
- We have added the `BoolSource` config type (similar to the `StringSource` type). The config value for
  this type can be a boolean literal or a pointer to an environment variable that is set to a boolean
  value.
- The `QueuedRunCoordinator` daemon is now more resilient to errors while dequeuing runs. Previously
  runs which could not launch would block the queue. They will now be marked as failed and removed
  from the queue.
- When deploying your own gRPC server for your pipelines, you can now specify that connecting to that
  server should use a secure SSL connection. For example, the following `workspace.yaml` file specifies
  that a secure connection should be used:

  ```yaml
  load_from:
    - grpc_server:
        host: localhost
        port: 4266
        location_name: "my_grpc_server"
        ssl: true
  ```

- The `dagster-daemon` process uses fewer resources and spins up fewer subprocesses to load pipeline
  information. Previously, the scheduler, sensor, and run queue daemon each spun up their own process
  for this–now they share a single process.

**Integrations**

- [Helm] - All images used in our Helm chart are now fully qualified, including a registry name.
  If you are encountering rate limits when attempting to pull images from DockerHub, you can now
  edit the Helm chart to pull from a registry of your choice.
- [Helm] - We now officially use Helm 3 to manage our Dagster Helm chart.
- [ECR] - We are now publishing the `dagster-k8s`, `dagster-celery-k8s`, `user-code-example`, and
  `k8s-dagit-example` images to a public ECR registry in addition to DockerHub. If you are
  encountering rate limits when attempting to pull images from DockerHub, you should now be able to
  pull these images from public.ecr.aws/dagster.
- [dagster-spark] - The `dagster-spark` config schemas now support loading values for all fields via
  environment variables.

**Bugfixes**

- Fixed a bug in the helm chart that would cause a Redis Kubernetes pod to be created even when an
  external Redis is configured. Now, the Redis Kubernetes pod is only created when `redis.internal`
  is set to `True` in helm chart.
- Fixed an issue where the `dagster-daemon` process sometimes left dangling subprocesses running
  during sensor execution, causing excess resource usage.
- Fixed an issue where Dagster sometimes left hanging threads running after pipeline execution.
- Fixed an issue where the sensor daemon would mistakenly mark itself as in an unhealthy state even
  after recovering from an error.
- Tags applied to solid invocations using the `tag` method on solid invocations (as opposed to solid
  definitions) are now correctly propagated during execution. They were previously being ignored.

**Experimental**

- MySQL (via dagster-mysql) is now supported as a backend for event log, run, & schedule storages.
  Add the following to your dagster.yaml to use MySQL for storage:

  ```yaml
  run_storage:
    module: dagster_mysql.run_storage
    class: MySQLRunStorage
    config:
      mysql_db:
        username: { username }
        password: { password }
        hostname: { hostname }
        db_name: { database }
        port: { port }

  event_log_storage:
    module: dagster_mysql.event_log
    class: MySQLEventLogStorage
    config:
      mysql_db:
        username: { username }
        password: { password }
        hostname: { hostname }
        db_name: { db_name }
        port: { port }

  schedule_storage:
    module: dagster_mysql.schedule_storage
    class: MySQLScheduleStorage
    config:
      mysql_db:
        username: { username }
        password: { password }
        hostname: { hostname }
        db_name: { db_name }
        port: { port }
  ```

## 0.10.7

**New**

- When user code raises an error inside handle_output, load_input, or a type check function, the log output now includes context about which input or output the error occurred during.
- Added a secondary index to improve performance when querying run status. Run `dagster instance migrate` to upgrade.
- [Helm] Celery queues can now be configured with different node selectors. Previously, configuring a node selector applied it to all Celery queues.
- In Dagit, a repository location reload button is now available in the header of every pipeline, schedule, and sensor page.
- When viewing a run in Dagit, log filtering behavior has been improved. `step` and `type` filtering now offer fuzzy search, all log event types are now searchable, and visual bugs within the input have been repaired. Additionally, the default setting for “Hide non-matches” has been flipped to `true`.
- After launching a backfill in Dagit, the success message now includes a link to view the runs for the backfill.
- The `dagster-daemon` process now runs faster when running multiple schedulers or sensors from the same repository.
- When launching a backfill from Dagit, the “Re-execute From Last Run” option has been removed, because it had confusing semantics. “Re-execute From Failure” now includes a tooltip.
- `fs_io_manager` now defaults the base directory to `base_dir` via the Dagster instance’s `local_artifact_storage` configuration. Previously, it defaults to the directory where the pipeline is executed.
- Experimental IO managers `versioned_filesystem_io_manager` and `custom_path_fs_io_manager` now require `base_dir` as part of the resource configs. Previously, the `base_dir` defaulted to the directory where the pipeline was executed.
- Added a backfill daemon that submits backfill runs in a daemon process. This should relieve memory / CPU requirements for scheduling large backfill jobs. Enabling this feature requires a schema migration to the runs storage via the CLI command `dagster instance migrate` and configuring your instance with the following settings in `dagster.yaml`:
- backfill:
  daemon_enabled: true

There is a corresponding flag in the Dagster helm chart to enable this instance configuration. See the Helm chart’s `values.yaml` file for more information.

- Both sensors and schedule definitions support a `description` parameter that takes in a human-readable string description and displays it on the corresponding landing page in Dagit.

**Integrations**

- [dagster-gcp] The `gcs_pickle_io_manager` now also retries on 403 Forbidden errors, which previously would only retry on 429 TooManyRequests.

**Bug Fixes**

- The use of `Tuple` with nested inner types in solid definitions no longer causes GraphQL errors
- When searching assets in Dagit, keyboard navigation to the highlighted suggestion now navigates to the correct asset.
- In some cases, run status strings in Dagit (e.g. “Queued”, “Running”, “Failed”) did not accurately match the status of the run. This has been repaired.
- The experimental CLI command `dagster new-repo` should now properly generate subdirectories and files, without needing to install `dagster` from source (e.g. with `pip install --editable`).
- Sensor minimum intervals now interact in a more compatible way with sensor daemon intervals to minimize evaluation ticks getting skipped. This should result in the cadence of sensor evaluations being less choppy.

**Dependencies**

- Removed Dagster’s pin of the `pendulum` datetime/timezone library.

**Documentation**

- Added an example of how to write a user-in-the-loop pipeline

## 0.10.6

**New**

- Added a `dagster run delete` CLI command to delete a run and its associated event log entries.
- Added a `partition_days_offset` argument to the `@daily_schedule` decorator that allows you to customize which partition is used for each execution of your schedule. The default value of this parameter is `1`, which means that a schedule that runs on day N will fill in the partition for day N-1. To create a schedule that uses the partition for the current day, set this parameter to `0`, or increase it to make the schedule use an earlier day’s partition. Similar arguments have also been added for the other partitioned schedule decorators (`@monthly_schedule`, `@weekly_schedule`, and `@hourly_schedule`).
- The experimental `dagster new-repo` command now includes a workspace.yaml file for your new repository.
- When specifying the location of a gRPC server in your `workspace.yaml` file to load your pipelines, you can now specify an environment variable for the server’s hostname and port. For example, this is now a valid workspace:

```
load_from:
  - grpc_server:
      host:
        env: FOO_HOST
      port:
        env: FOO_PORT
```

**Integrations**

- [Kubernetes] `K8sRunLauncher` and `CeleryK8sRunLauncher` no longer reload the pipeline being executed just before launching it. The previous behavior ensured that the latest version of the pipeline was always being used, but was inconsistent with other run launchers. Instead, to ensure that you’re running the latest version of your pipeline, you can refresh your repository in Dagit by pressing the button next to the repository name.
- [Kubernetes] Added a flag to the Dagster helm chart that lets you specify that the cluster already has a redis server available, so the Helm chart does not need to create one in order to use redis as a messaging queue. For more information, see the Helm chart’s values.yaml file.

**Bug Fixes**

- Schedules with invalid cron strings will now throw an error when the schedule definition is loaded, instead of when the cron string is evaluated.
- Starting in the 0.10.1 release, the Dagit playground did not load when launched with the `--path-prefix` option. This has been fixed.
- In the Dagit playground, when loading the run preview results in a Python error, the link to view the error is now clickable.
- When using the “Refresh config” button in the Dagit playground after reloading a pipeline’s repository, the user’s solid selection is now preserved.
- When executing a pipeline with a `ModeDefinition` that contains a single executor, that executor is now selected by default.
- Calling `reconstructable` on pipelines with that were also decorated with hooks no longer raises an error.
- The `dagster-daemon liveness-check` command previously returned false when daemons surfaced non-fatal errors to be displayed in Dagit, leading to crash loops in Kubernetes. The command has been fixed to return false only when the daemon has stopped running.
- When a pipeline definition includes `OutputDefinition`s with `io_manager_key`s, or `InputDefinition`s with `root_manager_key`s, but any of the modes provided for the pipeline definition do not include a resource definition for the required key, Dagster now raises an error immediately instead of when the pipeline is executed.
- dbt 0.19.0 introduced breaking changes to the JSON schema of [dbt Artifacts](https://docs.getdbt.com/reference/artifacts/dbt-artifacts/). `dagster-dbt` has been updated to handle the new `run_results.json` schema for dbt 0.19.0.

**Dependencies**

- The astroid library has been pinned to version 2.4 in dagster, due to version 2.5 causing problems with our pylint test suite.

**Documentation**

- Added an example of how to trigger a Dagster pipeline in GraphQL at https://docs.dagster.io/examples/trigger_pipeline.
- Added better documentation for customizing sensor intervals at https://docs.dagster.io/overview/schedules-sensors/sensors.

## 0.10.5

**Community Contributions**

- Add `/License` for packages that claim distribution under Apache-2.0 (thanks [@bollwyvl](https://github.com/dagster-io/dagster/commits?author=bollwyvl)!)

**New**

- [k8s] Changed our weekly docker image releases (the default images in the helm chart). `dagster/dagster-k8s` and `dagster/dagster-celery-k8s` can be
  used for all processes which don't require user code (Dagit, Daemon, and Celery workers when using the CeleryK8sExecutor). `user-code-example` can
  be used for a sample user repository. The prior images (`k8s-dagit`, `k8s-celery-worker`, `k8s-example`)
  are deprecated.
- `configured` api on solids now enforces name argument as positional. The `name` argument remains a keyword argument on executors. `name` argument has been removed from resources, and loggers to reflect that they are anonymous. Previously, you would receive an error message if the `name` argument was provided to `configured` on resources or loggers.
- [sensors] In addition to the per-sensor `minimum_interval_seconds` field, the overall sensor daemon interval can now be configured in the `dagster.yaml` instance settings with:

```yaml
sensor_settings:
  interval_seconds: 30 # (default)
```

This changes the interval at which the daemon checks for sensors which haven't run within their `minimum_interval_seconds`.

- The message logged for type check failures now includes the description included in the `TypeCheck`
- The `dagster-daemon` process now runs each of its daemons in its own thread. This allows the scheduler, sensor loop, and daemon for launching queued runs to run in parallel, without slowing each other down. The `dagster-daemon` process will shut down if any of the daemon threads crash or hang, so that the execution environment knows that it needs to be restarted.
- `dagster new-repo` is a new CLI command that generates a Dagster repository with skeleton code in your filesystem. This CLI command is experimental and it may generate different files in future versions, even between dot releases. As of 0.10.5, `dagster new-repo` does not support Windows. [See here for official API docs.](http://localhost:3001/_apidocs/cli#dagster-new-repo)
- When using a `grpc_server` repository location, Dagit will automatically detect changes and prompt you to reload when the remote server updates.
- Improved consistency of headers across pages in Dagit.
- Added support for assets to the default SQLite event log storage.

**Integrations**

- [dagster-pandas] - Improved the error messages on failed pandas type checks.
- [dagster-postgres] - postgres_url is now a StringSource and can be loaded by environment variable
- [helm] - Users can set Kubernetes labels on Celery worker deployments
- [helm] - Users can set environment variables for Flower deployment
- [helm] - The redis helm chart is now included as an optional dagster helm chart dependency

**Bugfixes**

- Resolved an error preventing dynamic outputs from being passed to composite_solid inputs
- Fixed the tick history graph for schedules defined in a lazy-loaded repository ([#3626](https://github.com/dagster-io/dagster/issues/3626))
- Fixed performance regression of the Runs page on dagit.
- Fixed Gantt chart on Dagit run view to use the correct start time, repairing how steps are rendered within the chart.
- On Instance status page in Dagit, correctly handle states where daemons have multiple errors.
- Various Dagit bugfixes and improvements.

## 0.10.4

**Bugfixes**

- Fixed an issue with daemon heartbeat backwards compatibility. Resolves an error on Dagit's Daemon Status page

## 0.10.3

**New**

- [dagster] Sensors can now specify a `minimum_interval_seconds` argument, which determines the minimum amount of time between sensor evaluations.
- [dagit] After manually reloading the current repository, users will now be prompted to regenerate preset-based or partition-set based run configs in the Playground view. This helps ensure that the generated run config is up to date when launching new runs. The prompt does not occur when the repository is automatically reloaded.

**Bugfixes**

- Updated the `-n`/`--max_workers` default value for the `dagster api grpc` command to be `None`. When set to `None`, the gRPC server will use the default number of workers which is based on the CPU count. If you were previously setting this value to `1`, we recommend removing the argument or increasing the number.
- Fixed issue loading the schedule tick history graph for new schedules that have not been turned on.
- In Dagit, newly launched runs will open in the current tab instead of a new tab.
- Dagit bugfixes and improvements, including changes to loading state spinners.
- When a user specifies both an intermediate storage and an IO manager for a particular output, we no longer silently ignore the IO manager

## 0.10.2

**Community Contributions**

- [docs] Update URL to telemetry info (thanks @emilmelnikov (https://github.com/dagster-io/dagster/commits?author=emilmelnikov)!)
- [dagster-azure] Fix for listing files on ADL example (thanks @ericct!)

**New**

- [dagstermill] Users can now specify custom tags & descriptions for notebook solids.
- [dagster-pagerduty / dagster-slack] Added built-in hook integrations to create pagerduty/slack alerts when solids fail.
- [dagit] Added ability to preview runs for upcoming schedule ticks.

**Bugfixes**

- Fixed an issue where run start times and end times were displayed in the wrong timezone in Dagit when using Postgres storage.
- Schedules with partitions that weren’t able to execute due to not being able to find a partition will now display the name of the partition they were unable to find on the “Last tick” entry for that schedule.

- Improved timing information display for queued and canceled runs within the Runs table view and on individual Run pages in Dagit.
- Improvements to the tick history view for schedules and sensors.
- Fixed formatting issues on the Dagit instance configuration page.
- Miscellaneous Dagit bugfixes and improvements.
- The dagster pipeline launch command will now respect run concurrency limits if they are applied on your instance.
- Fixed an issue where re-executing a run created by a sensor would cause the daemon to stop executing any additional runs from that sensor.
- Sensor runs with invalid run configuration will no longer create a failed run - instead, an error will appear on the page for the sensor, allowing you to fix the configuration issue.
- General dagstermill housekeeping: test refactoring & type annotations, as well as repinning ipykernel to solve #3401

**Documentation**

- Improved dagster-dbt example.
- Added examples to demonstrate experimental features, including Memoized Development and Dynamic Graph.
- Added a PR template and how to pick an issue for the first time contributors

## 0.10.1

**Community Contributions**

- Reduced image size of `k8s-example` by 25% (104 MB) (thanks @alex-treebeard and @mrdavidlaing!)
- [dagster-snowflake] `snowflake_resource` can now be configured to use the SQLAlchemy connector (thanks @basilvetas!)

**New**

- When setting `userDeployments.deployments` in the Helm chart, `replicaCount` now defaults to 1 if not specified.

**Bugfixes**

- Fixed an issue where the Dagster daemon process couldn’t launch runs in repository locations containing more than one repository.
- Fixed an issue where Helm chart was not correctly templating `env`, `envConfigMaps`, and `envSecrets`.

**Documentation**

- Added new [troubleshooting guide](https://docs.dagster.io/troubleshooting) for problems encountered while using the `QueuedRunCoordinator` to limit run concurrency.
- Added documentation for the sensor command-line interface.

## 0.10.0

### Major Changes

- A **native scheduler** with support for exactly-once, fault tolerant, timezone-aware scheduling.
  A new Dagster daemon process has been added to manage your schedules and sensors with a
  reconciliation loop, ensuring that all runs are executed exactly once, even if the Dagster daemon
  experiences occasional failure. See the
  [Migration Guide](https://github.com/dagster-io/dagster/blob/master/MIGRATION.md) for
  instructions on moving from `SystemCronScheduler` or `K8sScheduler` to the new scheduler.
- **First-class sensors**, built on the new Dagster daemon, allow you to instigate runs based on
  changes in external state - for example, files on S3 or assets materialized by other Dagster
  pipelines. See the [Sensors Overview](http://docs.dagster.io/overview/schedules-sensors/sensors)
  for more information.
- Dagster now supports **pipeline run queueing**. You can apply instance-level run concurrency
  limits and prioritization rules by adding the QueuedRunCoordinator to your Dagster instance. See
  the [Run Concurrency Overview](http://docs.dagster.io/overview/pipeline-runs/limiting-run-concurrency)
  for more information.
- The `IOManager` abstraction provides a new, streamlined primitive for granular control over where
  and how solid outputs are stored and loaded. This is intended to replace the (deprecated)
  intermediate/system storage abstractions, See the
  [IO Manager Overview](http://docs.dagster.io/overview/io-managers/io-managers) for more
  information.
- A new **Partitions page** in Dagit lets you view your your pipeline runs organized by partition.
  You can also **launch backfills from Dagit** and monitor them from this page.
- A new **Instance Status page** in Dagit lets you monitor the health of your Dagster instance,
  with repository location information, daemon statuses, instance-level schedule and sensor
  information, and linkable instance configuration.
- **Resources can now declare their dependencies on other resources** via the
  `required_resource_keys` parameter on `@resource`.
- Our support for deploying on **Kubernetes** is now mature and battle-tested Our Helm chart is
  now easier to configure and deploy, and we’ve made big investments in observability and
  reliability. You can view Kubernetes interactions in the structured event log and use Dagit to
  help you understand what’s happening in your deployment. The defaults in the Helm chart will
  give you graceful degradation and failure recovery right out of the box.
- Experimental support for **dynamic orchestration** with the new `DynamicOutputDefinition` API.
  Dagster can now map the downstream dependencies over a dynamic output at runtime.

### Breaking Changes

**Dropping Python 2 support**

- We’ve dropped support for Python 2.7, based on community usage and enthusiasm for Python 3-native
  public APIs.

**Removal of deprecated APIs**

_These APIs were marked for deprecation with warnings in the 0.9.0 release, and have been removed in
the 0.10.0 release._

- The decorator `input_hydration_config` has been removed. Use the `dagster_type_loader` decorator
  instead.
- The decorator `output_materialization_config` has been removed. Use `dagster_type_materializer`
  instead.
- The system storage subsystem has been removed. This includes `SystemStorageDefinition`,
  `@system_storage`, and `default_system_storage_defs` . Use the new `IOManagers` API instead. See
  the [IO Manager Overview](http://docs.dagster.io/overview/io-managers/io-managers) for more
  information.
- The `config_field` argument on decorators and definitions classes has been removed and replaced
  with `config_schema`. This is a drop-in rename.
- The argument `step_keys_to_execute` to the functions `reexecute_pipeline` and
  `reexecute_pipeline_iterator` has been removed. Use the `step_selection` argument to select
  subsets for execution instead.
- Repositories can no longer be loaded using the legacy `repository` key in your `workspace.yaml`;
  use `load_from` instead. See the
  [Workspaces Overview](https://docs.dagster.io/overview/repositories-workspaces/workspaces) for
  documentation about how to define a workspace.

**Breaking API Changes**

- `SolidExecutionResult.compute_output_event_dict` has been renamed to
  `SolidExecutionResult.compute_output_events_dict`. A solid execution result is returned from
  methods such as `result_for_solid`. Any call sites will need to be updated.
- The `.compute` suffix is no longer applied to step keys. Step keys that were previously named
  `my_solid.compute` will now be named `my_solid`. If you are using any API method that takes a
  step_selection argument, you will need to update the step keys accordingly.
- The `pipeline_def` property has been removed from the `InitResourceContext` passed to functions
  decorated with `@resource`.

**Dagstermill**

- If you are using `define_dagstermill_solid` with the `output_notebook` parameter set to `True`,
  you will now need to provide a file manager resource (subclass of
  `dagster.core.storage.FileManager`) on your pipeline mode under the resource key `"file_manager"`,
  e.g.:

  ```python
  from dagster import ModeDefinition, local_file_manager, pipeline
  from dagstermill import define_dagstermill_solid

  my_dagstermill_solid = define_dagstermill_solid("my_dagstermill_solid", output_notebook=True, ...)

  @pipeline(mode_defs=[ModeDefinition(resource_defs={"file_manager": local_file_manager})])
  def my_dagstermill_pipeline():
      my_dagstermill_solid(...)
  ```

**Helm Chart**

- The schema for the `scheduler` values in the helm chart has changed. Instead of a simple toggle
  on/off, we now require an explicit `scheduler.type` to specify usage of the
  `DagsterDaemonScheduler`, `K8sScheduler`, or otherwise. If your specified `scheduler.type` has
  required config, these fields must be specified under `scheduler.config`.
- `snake_case` fields have been changed to `camelCase`. Please update your `values.yaml` as follows:
  - `pipeline_run` → `pipelineRun`
  - `dagster_home` → `dagsterHome`
  - `env_secrets` → `envSecrets`
  - `env_config_maps` → `envConfigMaps`
- The Helm values `celery` and `k8sRunLauncher` have now been consolidated under the Helm value
  `runLauncher` for simplicity. Use the field `runLauncher.type` to specify usage of the
  `K8sRunLauncher`, `CeleryK8sRunLauncher`, or otherwise. By default, the `K8sRunLauncher` is
  enabled.
- All Celery message brokers (i.e. RabbitMQ and Redis) are disabled by default. If you are using
  the `CeleryK8sRunLauncher`, you should explicitly enable your message broker of choice.
- `userDeployments` are now enabled by default.

### Core

- Event log messages streamed to `stdout` and `stderr` have been streamlined to be a single line
  per event.
- Experimental support for memoization and versioning lets you execute pipelines incrementally,
  selecting which solids need to be rerun based on runtime criteria and versioning their outputs
  with configurable identifiers that capture their upstream dependencies.

  To set up memoized step selection, users can provide a `MemoizableIOManager`, whose `has_output`
  function decides whether a given solid output needs to be computed or already exists. To execute
  a pipeline with memoized step selection, users can supply the `dagster/is_memoized_run` run tag
  to `execute_pipeline`.

  To set the version on a solid or resource, users can supply the `version` field on the definition.
  To access the derived version for a step output, users can access the `version` field on the
  `OutputContext` passed to the `handle_output` and `load_input` methods of `IOManager` and the
  `has_output` method of `MemoizableIOManager`.

- Schedules that are executed using the new `DagsterDaemonScheduler` can now execute in any
  timezone by adding an `execution_timezone` parameter to the schedule. Daylight Savings Time
  transitions are also supported. See the
  [Schedules Overview](http://docs.dagster.io/overview/schedules-sensors/schedules#timezones) for
  more information and examples.

### Dagit

- Countdown and refresh buttons have been added for pages with regular polling queries (e.g. Runs,
  Schedules).
- Confirmation and progress dialogs are now presented when performing run terminations and
  deletions. Additionally, hanging/orphaned runs can now be forced to terminate, by selecting
  "Force termination immediately" in the run termination dialog.
- The Runs page now shows counts for "Queued" and "In progress" tabs, and individual run pages
  show timing, tags, and configuration metadata.
- The backfill experience has been improved with means to view progress and terminate the entire
  backfill via the partition set page. Additionally, errors related to backfills are now surfaced
  more clearly.
- Shortcut hints are no longer displayed when attempting to use the screen capture command.
- The asset page has been revamped to include a table of events and enable organizing events by
  partition. Asset key escaping issues in other views have been fixed as well.
- Miscellaneous bug fixes, frontend performance tweaks, and other improvements are also included.

### Kubernetes/Helm

- The [Dagster Kubernetes documentation](https://docs.dagster.io/deploying/kubernetes) has been refreshed.

**Helm**

- We've added schema validation to our Helm chart. You can now check that your values YAML file is
  correct by running:

  ```bash
  helm lint helm/dagster -f helm/dagster/values.yaml
  ```

- Added support for resource annotations throughout our Helm chart.
- Added Helm deployment of the dagster daemon & daemon scheduler.
- Added Helm support for configuring a compute log manager in your dagster instance.
- User code deployments now include a user `ConfigMap` by default.
- Changed the default liveness probe for Dagit to use `httpGet "/dagit_info"` instead of
  `tcpSocket:80`

**Dagster-K8s [Kubernetes]**

- Added support for user code deployments on Kubernetes.
- Added support for tagging pipeline executions.
- Fixes to support version 12.0.0 of the Python Kubernetes client.
- Improved implementation of Kubernetes+Dagster retries.
- Many logging improvements to surface debugging information and failures in the structured event
  log.

**Dagster-Celery-K8s**

- Improved interrupt/termination handling in Celery workers.

### Integrations & Libraries

- Added a new `dagster-docker` library with a `DockerRunLauncher` that launches each run in its own
  Docker container. (See [Deploying with Docker docs](https://docs.dagster.io/examples/deploy_docker)
  for an example.)
- Added support for AWS Athena. (Thanks @jmsanders!)
- Added mocks for AWS S3, Athena, and Cloudwatch in tests. (Thanks @jmsanders!)
- Allow setting of S3 endpoint through env variables. (Thanks @marksteve!)
- Various bug fixes and new features for the Azure, Databricks, and Dask integrations.
- Added a `create_databricks_job_solid` for creating solids that launch Databricks jobs.

## 0.9.22.post0

**Bugfixes**

- [Dask] Pin dask[dataframe] to <=2.30.0 and distributed to <=2.30.1

## 0.9.22

**New**

- When using a solid selection in the Dagit Playground, non-matching solids are hidden in the
  RunPreview panel.
- The CLI command dagster pipeline launch now accepts --run-id

**Bugfixes**

- [Helm/K8s] Fixed whitespacing bug in ingress.yaml Helm template.

## 0.9.21

**Community Contributions**

- Fixed helm chart to only add flower to the K8s ingress when enabled (thanks [@PenguinToast](https://github.com/PenguinToast)!)
- Updated helm chart to use more lenient timeouts for liveness probes on user code deployments (thanks [@PenguinToast](https://github.com/PenguinToast)!)

**Bugfixes**

- [Helm/K8s] Due to Flower being incompatible with Celery 5.0, the Helm chart for Dagster now uses a specific image `mher/flower:0.9.5` for the Flower pod.

## 0.9.20

**New**

- [Dagit] Show recent runs on individual schedule pages
- [Dagit] It’s no longer required to run `dagster schedule up` or press the Reconcile button before turning on a new schedule for the first time
- [Dagit] Various improvements to the asset view. Expanded the Last Materialization Event view. Expansions to the materializations over time view, allowing for both a list view and a graphical view of materialization data.

**Community Contributions**

- Updated many dagster-aws tests to use mocked resources instead of depending on real cloud resources, making it possible to run these tests locally. (thanks @jmsanders!)

**Bugfixes**

- fixed an issue with retries in step launchers
- [Dagit] bugfixes and improvements
- Fixed an issue where dagit sometimes left hanging processes behind after exiting

**Experimental**

- [K8s] The dagster daemon is now optionally deployed by the helm chart. This enables run-level queuing with the QueuedRunCoordinator.

## 0.9.19

**New**

- Improved error handling when the intermediate storage stores and retrieves objects.
- New URL scheme in Dagit, with repository details included on all paths for pipelines, solids, and schedules
- Relaxed constraints for the AssetKey constructor, to enable arbitrary strings as part of the key path.
- When executing a subset of a pipeline, configuration that does not apply to the current subset but would be valid in the original pipeline is now allowed and ignored.
- GCSComputeLogManager was added, allowing for compute logs to be persisted to Google cloud storage
- The step-partition matrix in Dagit now auto-reloads runs

**Bugfixes**

- Dagit bugfixes and improvements
- When specifying a namespace during helm install, the same namespace will now be used by the K8sScheduler or K8sRunLauncher, unless overridden.
- `@pipeline` decorated functions with -> None typing no longer cause unexpected problems.
- Fixed an issue where compute logs might not always be complete on Windows.

## 0.9.18

**Breaking Changes**

- `CliApiRunLauncher` and `GrpcRunLauncher` have been combined into `DefaultRunLauncher`.
  If you had one of these run launchers in your `dagster.yaml`, replace it with `DefaultRunLauncher`
  or remove the `run_launcher:` section entirely.

**New**

- Added a type loader for typed dictionaries: can now load typed dictionaries from config.

**Bugfixes**

- Dagit bugfixes and improvements
  - Added error handling for repository errors on startup and reload
  - Repaired timezone offsets
  - Fixed pipeline explorer state for empty pipelines
  - Fixed Scheduler table
- User-defined k8s config in the pipeline run tags (with key `dagster-k8s/config`) will now be
  passed to the k8s jobs when using the `dagster-k8s` and `dagster-celery-k8s` run launchers.
  Previously, only user-defined k8s config in the pipeline definition’s tag was passed down.

**Experimental**

- Run queuing: the new `QueuedRunCoordinator` enables limiting the number of concurrent runs.
  The `DefaultRunCoordinator` launches jobs directly from Dagit, preserving existing behavior.

## 0.9.17

**New**

- [dagster-dask] Allow connecting to an existing scheduler via its address
- [dagster-aws] Importing dagster_aws.emr no longer transitively importing dagster_spark
- [dagster-dbr] CLI solids now emit materializations

**Community contributions**

- Docs fix (Thanks @kaplanbora!)

**Bug fixes**

- `PipelineDefinition` 's that do not meet resource requirements for its types will now fail at definition time
- Dagit bugfixes and improvements
- Fixed an issue where a run could be left hanging if there was a failure during launch

**Deprecated**

- We now warn if you return anything from a function decorated with `@pipeline`. This return value actually had no impact at all and was ignored, but we are making changes that will use that value in the future. By changing your code to not return anything now you will avoid any breaking changes with zero user-visible impact.

## 0.9.16

**Breaking Changes**

- Removed `DagsterKubernetesPodOperator` in `dagster-airflow`.
- Removed the `execute_plan` mutation from `dagster-graphql`.
- `ModeDefinition`, `PartitionSetDefinition`, `PresetDefinition`, `@repository`, `@pipeline`, and `ScheduleDefinition` names must pass the regular expression `r"^[A-Za-z0-9_]+$"` and not be python keywords or disallowed names. See `DISALLOWED_NAMES` in `dagster.core.definitions.utils` for exhaustive list of illegal names.
- `dagster-slack` is now upgraded to use slackclient 2.x - this means that this resource will only support Python 3.6 and above.
- [K8s] Added a health check to the helm chart for user deployments, which relies on a new `dagster api grpc-health-check` cli command present in Dagster `0.9.16` and later.

**New**

- Add helm chart configurations to allow users to configure a `K8sRunLauncher`, in place of the `CeleryK8sRunLauncher`.
- “Copy URL” button to preserve filter state on Run page in dagit

**Community Contributions**

- Dagster CLI options can now be passed in via environment variables (Thanks @xinbinhuang!)
- New `--limit` flag on the `dagster run list` command (Thanks @haydarai!)

**Bugfixes**

- Addressed performance issues loading the /assets table in dagit. Requires a data migration to create a secondary index by running dagster instance reindex.
- Dagit bugfixes and improvements

## 0.9.15

**Breaking Changes**

- CeleryDockerExecutor no longer requires a repo_location_name config field.
- `executeRunInProcess` was removed from `dagster-graphql`.

**New**

- Dagit: Warn on tab removal in playground
- Display versions CLI: Added a new CLI that displays version information for a memoized run. Called via dagster pipeline list_versions.
- CeleryDockerExecutor accepts a network field to configure the network settings for the Docker container it connects to for execution.
- Dagit will now set a statement timeout on supported instance DBs. Defaults to 5s and can be controlled with the --db-statement-timeout flag

**Community Contributions**

- dagster grpc requirements are now more friendly for users (thanks @jmo-qap!)
- dagster.utils now has is_str (thanks @monicayao!)
- dagster-pandas can now load dataframes from pickle (thanks @mrdrprofuroboros!)
- dagster-ge validation solid factory now accepts name (thanks @haydarai!)

**Bugfixes**

- Dagit bugfixes and improvements
- Fixed an issue where dagster could fail to load large pipelines.
- Fixed a bug where experimental arg warning would be thrown even when not using versioned dagster type loaders.
- Fixed a bug where CeleryDockerExecutor was failing to execute pipelines unless they used a legacy workspace config.
- Fixed a bug where pipeline runs using IntMetadataEntryData could not be visualized in dagit.

**Experimental**

- Improve the output structure of dagster-dbt solids.
- Version-based memoization over outputs stored in the intermediate store now works

**Documentation**

- Fix a code snippet rendering issue in Overview: Assets & Materializations
- Fixed all python code snippets alignment across docs examples

## 0.9.14

**New**

- Steps down stream of a failed step no longer report skip events and instead simply do not execute.
- dagit-debug can load multiple debug files.
- dagit now has a Debug Console Logging feature flag accessible at /flags .
- Telemetry metrics are now taken when scheduled jobs are executed.
- With memoized reexecution, we now only copy outputs that current plan won't generate
- Document titles throughout dagit

**Community Contributions**

- [dagster-ge] solid factory can now handle arbitrary types (thanks @sd2k!)
- [dagster-dask] utility options are now available in loader/materializer for Dask DataFrame (thanks @kinghuang!)

**Bugfixes**

- Fixed an issue where run termination would sometimes be ignored or leave the execution process hanging
- [dagster-k8s] fixed issue that would cause timeouts on clusters with many jobs
- Fixed an issue where reconstructable was unusable in an interactive environment, even when the pipeline is defined in a different module.
- Bugfixes and UX improvements in dagit

**Experimental**

- AssetMaterializations now have an optional “partition” attribute

## 0.9.13

**Bugfixes**

- Fixes an issue using `build_reconstructable_pipeline`.
- Improved loading times for the asset catalog in Dagit.

**Documentations**

- Improved error messages when invoking dagit from the CLI with bad arguments.

## 0.9.12

**Breaking Changes**

- Dagster now warns when a solid, pipeline, or other definition is created with an invalid name (for example, a Python keyword). This warning will become an error in the 0.9.13 release.

**Community Contributions**

- Added an int type to `EventMetadataEntry` (Thanks @[ChocoletMousse](https://github.com/ChocoletMousse)!)
- Added a `build_composite_solid_definition` method to Lakehouse (Thanks @[sd2k](https://github.com/sd2k)!)
- Improved broken link detection in Dagster docs (Thanks @[keyz](https://github.com/keyz)!)

**New**

- Improvements to log filtering on Run view in Dagit
- Improvements to instance level scheduler page
- Log engine events when pipeline termination is initiated

**Bugfixes**

- Syntax errors in user code now display the file and line number with the error in Dagit
- Dask executor no longer fails when using intermediate_storage
- In the Celery K8s executor, we now mark the step as failed when the step job fails
- Changed the `DagsterInvalidAssetKey` error so that it no longer fails upon being thrown

**Documentation**

- Added API docs for dagster-dbt experimental library
- Fixed some cosmetic issues with docs.dagster.io
- Added code snippets from Solids examples to test path, and fixed some inconsistencies regarding parameter ordering
- Changed to using markers instead of exact line numbers to mark out code snippets

## 0.9.10

**Breaking Changes**

- [dagster-dask] Removed the `compute` option from Dask DataFrame materialization configs for all output types. Setting this option to `False` (default `True`) would result in a future that is never computed, leading to missing materializations

**Community Contributions**

- Added a Dask resource (Thanks @[kinghuang](https://github.com/kinghuang)!)

**New**

- Console log messages are now streamlined to live on a single line per message
- Added better messaging around `$DAGSTER_HOME` if it is not set or improperly setup when starting up a Dagster instance
- Tools for exporting a file for debugging a run have been added:
  - `dagster debug export` - a new CLI entry added for exporting a run by id to a file
  - `dagit-debug` - a new CLI added for loading dagit with a run to debug
  - `dagit` now has a button to download the debug file for a run via the action menu on the runs page
- The `dagster api grpc` command now defaults to the current working directory if none is specified
- Added retries to dagster-postgres connections
- Fixed faulty warning message when invoking the same solid multiple times in the same context
- Added ability to specify custom liveness probe for celery workers in kubernetes deployment

**Bugfixes**

- Fixed a bug where Dagster types like List/Set/Tuple/Dict/Optional were not displaying properly on dagit logs
- Fixed endless spinners on `dagit --empty-workspace`
- Fixed incorrect snapshot banner on pipeline view
- Fixed visual overlapping of overflowing dagit logs
- Fixed a bug where hanging runs when executing against a gRPC server could cause the Runs page to be unable to load
- Fixed a bug in celery integration where celery tasks could return `None` when an iterable is expected, causing errors in the celery execution loop.

**Experimental**

- [lakehouse] Each time a Lakehouse solid updates an asset, it automatically generates an AssetMaterialization event
- [lakehouse] Lakehouse computed_assets now accept a version argument that describes the version of the computation
- Setting the “dagster/is_memoized_run” tag to true will cause the run to skip any steps whose versions match the versions of outputs produced in prior runs.
- [dagster-dbt] Solids for running dbt CLI commands
- Added extensive documentation to illuminate how versions are computed
- Added versions for step inputs from config, default values, and from other step outputs

## 0.9.9

**New**

- [Databricks] solids created with create_databricks_job_solid now log a URL for accessing the job in the Databricks UI.
- The pipeline execute command now defaults to using your current directory if you don’t specify a working directory.

**Bugfixes**

- [Celery-K8s] Surface errors to Dagit that previously were not caught in the Celery workers.
- Fix issues with calling add_run_tags on tags that already exist.
- Add “Unknown” step state in Dagit’s pipeline run logs view for when pipeline has completed but step has not emitted a completion event

**Experimental**

- Version tags for resources and external inputs.

**Documentation**

- Fix rendering of example solid config in “Basics of Solids” tutorial.

## 0.9.8

**New**

- Support for the Dagster step selection DSL: `reexecute_pipeline` now takes `step_selection`, which accepts queries like `*solid_a.compute++` (i.e., `solid_a.compute`, all of its ancestors, its immediate descendants, and their immediate descendants). `steps_to_execute` is deprecated and will be removed in 0.10.0.

**Community contributions**

- [dagster-databricks] Improved setup of Databricks environment (Thanks @[sd2k](https://github.com/sd2k)!)
- Enabled frozenlist pickling (Thanks @[kinghuang](https://github.com/kinghuang)!)

**Bugfixes**

- Fixed a bug that pipeline-level hooks were not correctly applied on a pipeline subset.
- Improved error messages when execute command can't load a code pointer.
- Fixed a bug that prevented serializing Spark intermediates with configured intermediate storages.

**Dagit**

- Enabled subset reexecution via Dagit when part of the pipeline is still running.
- Made `Schedules` clickable and link to View All page in the schedule section.
- Various Dagit UI improvements.

**Experimental**

- [lakehouse] Added CLI command for building and executing a pipeline that updates a given set of assets: `house update --module package.module —assets my_asset*`

**Documentation**

- Fixes and improvements.

## 0.9.7

**Bugfixes**

- Fixed an issue in the dagstermill library that caused solid config fetch to be non-deterministic.
- Fixed an issue in the K8sScheduler where multiple pipeline runs were kicked off for each scheduled
  execution.

## 0.9.6

**New**

- Added ADLS2 storage plugin for Spark DataFrame (Thanks @sd2k!)
- Added feature in the Dagit Playground to automatically remove extra configuration that does not conform to a pipeline’s config schema.
- [Dagster-Celery/Celery-K8s/Celery-Docker] Added Celery worker names and pods to the logs for each step execution

**Community contributions**

- Re-enabled dagster-azure integration tests in dagster-databricks tests (Thanks @sd2k!)
- Moved dict_without_keys from dagster-pandas into dagster.utils (Thanks @DavidKatz-il)
- Moved Dask DataFrame read/to options under read/to keys (Thanks @kinghuang)

**Bugfixes**

- Fixed helper for importing data from GCS paths into Bigquery (Thanks @grabangomb (https://github.com/grabangomb)!)
- Postgres event storage now waits to open a thread to watch runs until it is needed

**Experimental**

- Added version computation function for DagsterTypeLoader. (Actual versioning will be supported in 0.10.0)
- Added version attribute to solid and SolidDefinition. (Actual versioning will be supported in 0.10.0)

## 0.9.5

**New**

- UI improvements to the backfill partition selector
- Enabled sorting of steps by failure in the partition run matrix in Dagit

**Bugfixes**

- [dagstermill] fixes an issue with output notebooks and s3 storage
- [dagster_celery] bug fixed in pythonpath calculation (thanks @enima2648!)
- [dagster_pandas] marked create_structured_dataframe_type and ConstraintWithMetadata as experimental APIs
- [dagster_k8s] reduced default job backoff limit to 0

**Docs**

- Various docs site improvements

## 0.9.4

**Breaking Changes**

- When using the `configured` API on a solid or composite solid, a new solid name must be provided.
- The image used by the K8sScheduler to launch scheduled executions is now specified under the “scheduler” section of the Helm chart (previously under “pipeline_run” section).

**New**

- Added an experimental mode that speeds up interactions in dagit by launching a gRPC server on startup for each repository location in your workspace. To enable it, add the following to your `dagster.yaml`:

```yaml
opt_in:
  local_servers: true
```

- Intermediate Storage and System Storage now default to the first provided storage definition when no configuration is provided. Previously, it would be necessary to provide a run config for storage whenever providing custom storage definitions, even if that storage required no run configuration. Now, if the first provided storage definition requires no run configuration, the system will default to using it.
- Added a timezone picker to Dagit, and made all timestamps timezone-aware
- Added solid_config to hook context which provides the access to the config schema variable of the corresponding solid.
- Hooks can be directly set on `PipelineDefinition` or `@pipeline`, e.g. `@pipeline(hook_defs={hook_a})`. It will apply the hooks on every single solid instance within the pipeline.
- Added Partitions tab for partitioned pipelines, with new backfill selector.

## 0.9.3

**Breaking Changes**

- Removed deprecated `--env` flag from CLI
- The `--host` CLI param has been renamed to `--grpc_host` to avoid conflict with the dagit `--host` param.

**New**

- Descriptions for solid inputs and outputs will now be inferred from doc blocks if available (thanks [@AndersonReyes](https://github.com/dagster-io/dagster/commits?author=AndersonReyes) !)
- Various documentation improvements (thanks [@jeriscc](https://github.com/dagster-io/dagster/commits?author=jeriscc) !)
- Load inputs from pyspark dataframes (thanks [@davidkatz-il](https://github.com/dagster-io/dagster/commits?author=davidkatz-il) !)
- Added step-level run history for partitioned schedules on the schedule view
- Added great_expectations integration, through the `dagster_ge` library. Example usage is under a new example, called `ge_example`, and documentation for the library can be found under the libraries section of the api docs.
- `PythonObjectDagsterType` can now take a tuple of types as well as a single type, more closely mirroring `isinstance` and allowing Union types to be represented in Dagster.
- The `configured` API can now be used on all definition types (including `CompositeDefinition`). Example usage has been updated in the [configuration documentation](https://docs.dagster.io/overview/configuration).
- Updated Helm chart to include auto-generated user code configmap in user code deployment by default

**Bugfixes**

- Databricks now checks intermediate storage instead of system storage
- Fixes a bug where applying hooks on a pipeline with composite solids would flatten the top-level solids. Now applying hooks on pipelines or composite solids means attaching hooks to every single solid instance within the pipeline or the composite solid.
- Fixes the GraphQL playground hosted by dagit
- Fixes a bug where K8s CronJobs were stopped unnecessarily during schedule reconciliation

**Experimental**

- New `dagster-k8s/config` tag that lets users pass in custom configuration to the Kubernetes `Job`, `Job` metadata, `JobSpec`, `PodSpec`, and `PodTemplateSpec` metadata.
  - This allows users to specify settings like eviction policy annotations and node affinities.
  - Example:
  ```python
    @solid(
      tags = {
        'dagster-k8s/config': {
          'container_config': {
            'resources': {
              'requests': { 'cpu': '250m', 'memory': '64Mi' },
              'limits': { 'cpu': '500m', 'memory': '2560Mi' },
            }
          },
          'pod_template_spec_metadata': {
            'annotations': { "cluster-autoscaler.kubernetes.io/safe-to-evict": "true"}
          },
          'pod_spec_config': {
            'affinity': {
              'nodeAffinity': {
                'requiredDuringSchedulingIgnoredDuringExecution': {
                  'nodeSelectorTerms': [{
                    'matchExpressions': [{
                      'key': 'beta.kubernetes.io/os', 'operator': 'In', 'values': ['windows', 'linux'],
                    }]
                  }]
                }
              }
            }
          },
        },
      },
    )
    def my_solid(context):
      context.log.info('running')
  ```

## 0.9.2

**Breaking Changes**

- The `--env` flag no longer works for the `pipeline launch` or `pipeline execute` commands. Use `--config` instead.
- The `pipeline execute` command no longer accepts the `--workspace` argument.
  To execute pipelines in a workspace, use `pipeline launch` instead.

**New**

- Added `ResourceDefinition.mock_resource` helper for magic mocking resources. Example usage can be found [here](https://git.io/JJ7tz)
- Remove the `row_count` metadata entry from the Dask DataFrame type check (thanks [@kinghuang](https://github.com/kinghuang)!)
- Add [`orient`](https://docs.dask.org/en/latest/dataframe-api.html#dask.dataframe.to_json) to the config options when materializing a Dask DataFrame to `json` (thanks [@kinghuang](https://github.com/kinghuang)!)

**Bugfixes**

- Fixed a bug where applying `configured` to a solid definition would overwrite inputs from run config.
- Fixed a bug where pipeline tags would not apply to solid subsets.
- Improved error messages for repository-loading errors in CLI commands.
- Fixed a bug where pipeline execution error messages were not being surfaced in Dagit.

## 0.9.1

**Bugfixes**

- Fixes an issue in the `dagster-k8s-celery` executor when executing solid subsets

**Breaking Changes**

- Deprecated the `IntermediateStore` API. `IntermediateStorage` now wraps an ObjectStore, and `TypeStoragePlugin` now accepts an `IntermediateStorage` instance instead of an `IntermediateStore` instance. (Noe that `IntermediateStore` and `IntermediateStorage` are both internal APIs that are used in some non-core libraries).

## 0.9.0

**Breaking Changes**

- The `dagit` key is no longer part of the instance configuration schema and must be removed from `dagster.yaml` files before they can be used.
- `-d` can no longer be used as a command-line argument to specify a mode. Use `--mode` instead.
- Use `--preset` instead of `--preset-name` to specify a preset to the `pipeline launch` command.
- We have removed the `config` argument to the `ConfigMapping`, `@composite_solid`, `@solid`, `SolidDefinition`, `@executor`, `ExecutorDefinition`, `@logger`, `LoggerDefinition`, `@resource`, and `ResourceDefinition` APIs, which we deprecated in 0.8.0. Use `config_schema` instead.

**New**

- Python 3.8 is now fully supported.
- `-d` or `--working-directory` can be used to specify a working directory in any command that
  takes in a `-f` or `--python_file` argument.
- Removed the deprecation of `create_dagster_pandas_dataframe_type`. This is the currently
  supported API for custom pandas data frame type creation.
- Removed gevent dependency from dagster
- New `configured` API for predefining configuration for various definitions: https://docs.dagster.io/overview/configuration/#configured
- Added hooks to enable success and failure handling policies on pipelines. This enables users to set up policies on all solids within a pipeline or on a per solid basis. Example usage can be found [here](https://docs.dagster.io/examples/hooks)
- New instance level view of Scheduler and running schedules
- dagster-graphql is now only required in dagit images.

## 0.8.11

**Breaking Changes**

- `AssetMaterializations` no longer accepts a `dagster_type` argument. This reverts the change
  billed as "`AssetMaterializations` can now have type information attached as metadata." in the
  previous release.

## 0.8.10

**New**

- Added new GCS and Azure file manager resources
- `AssetMaterializations` can now have type information attached as metadata. See the materializations tutorial for more
- Added verification for resource arguments (previously only validated at runtime)

**Bugfixes**

- Fixed bug with order-dependent python module resolution seen with some packages (e.g. numpy)
- Fixed bug where Airflow's `context['ts']` was not passed properly
- Fixed a bug in celery-k8s when using `task_acks_late: true` that resulted in a `409 Conflict error` from Kubernetes. The creation of a Kubernetes Job will now be aborted if another Job with the same name exists
- Fixed a bug with composite solid output results when solids are skipped
- Hide the re-execution button in Dagit when the pipeline is not re-executable in the currently loaded repository

**Docs**

- Fixed code example in the advanced scheduling doc (Thanks @wingyplus!)
- Various other improvements

## 0.8.9

**New**

- `CeleryK8sRunLauncher` supports termination of pipeline runs. This can be accessed via the
  “Terminate” button in Dagit’s Pipeline Run view or via “Cancel” in Dagit’s All Runs page. This
  will terminate the run master K8s Job along with all running step job K8s Jobs; steps that are
  still in the Celery queue will not create K8s Jobs. The pipeline and all impacted steps will
  be marked as failed. We recommend implementing resources as context managers and we will execute
  the finally block upon termination.
- `K8sRunLauncher` supports termination of pipeline runs.
- `AssetMaterialization` events display the asset key in the Runs view.
- Added a new "Actions" button in Dagit to allow to cancel or delete mulitple runs.

**Bugfixes**

- Fixed an issue where `DagsterInstance` was leaving database connections open due to not being
  garbage collected.
- Fixed an issue with fan-in inputs skipping when upstream solids have skipped.
- Fixed an issue with getting results from composites with skippable outputs in python API.
- Fixed an issue where using `Enum` in resource config schemas resulted in an error.

## 0.8.8

**New**

- The new `configured` API makes it easy to create configured versions of resources.
- Deprecated the `Materialization` event type in favor of the new `AssetMaterialization` event type,
  which requires the `asset_key` parameter. Solids yielding `Materialization` events will continue
  to work as before, though the `Materialization` event will be removed in a future release.
- We are starting to deprecate "system storages" - instead of pipelines having a system storage
  definition which creates an intermediate storage, pipelines now directly have an intermediate
  storage definition.
  - We have added an `intermediate_storage_defs` argument to `ModeDefinition`, which accepts a
    list of `IntermediateStorageDefinition`s, e.g. `s3_plus_default_intermediate_storage_defs`.
    As before, the default includes an in-memory intermediate and a local filesystem intermediate
    storage.
  - We have deprecated `system_storage_defs` argument to `ModeDefinition` in favor of
    `intermediate_storage_defs`. `system_storage_defs` will be removed in 0.10.0 at the earliest.
  - We have added an `@intermediate_storage` decorator, which makes it easy to define intermediate
    storages.
  - We have added `s3_file_manager` and `local_file_manager` resources to replace the file managers
    that previously lived inside system storages. The airline demo has been updated to include
    an example of how to do this:
    https://github.com/dagster-io/dagster/blob/0.8.8/examples/airline_demo/airline_demo/solids.py#L171.
- The help panel in the dagit config editor can now be resized and toggled open or closed, to
  enable easier editing on smaller screens.

**Bugfixes**

- Opening new Dagit browser windows maintains your current repository selection. #2722
- Pipelines with the same name in different repositories no longer incorrectly share playground state. #2720
- Setting `default_value` config on a field now works as expected. #2725
- Fixed rendering bug in the dagit run reviewer where yet-to-be executed execution steps were
  rendered on left-hand side instead of the right.

## 0.8.7

**Breaking Changes**

- Loading python modules reliant on the working directory being on the PYTHONPATH is no longer
  supported. The `dagster` and `dagit` CLI commands no longer add the working directory to the
  PYTHONPATH when resolving modules, which may break some imports. Explicitly installed python
  packages can be specified in workspaces using the `python_package` workspace yaml config option.
  The `python_module` config option is deprecated and will be removed in a future release.

**New**

- Dagit can be hosted on a sub-path by passing `--path-prefix` to the dagit CLI. #2073
- The `date_partition_range` util function now accepts an optional `inclusive` boolean argument. By default, the function does not return include the partition for which the end time of the date range is greater than the current time. If `inclusive=True`, then the list of partitions returned will include the extra partition.
- `MultiDependency` or fan-in inputs will now only cause the solid step to skip if all of the
  fanned-in inputs upstream outputs were skipped

**Bugfixes**

- Fixed accidental breaking change with `input_hydration_config` arguments
- Fixed an issue with yaml merging (thanks @shasha79!)
- Invoking `alias` on a solid output will produce a useful error message (thanks @iKintosh!)
- Restored missing run pagination controls
- Fixed error resolving partition-based schedules created via dagster schedule decorators (e.g. `daily_schedule`) for certain workspace.yaml formats

## 0.8.6

**Breaking Changes**

- The `dagster-celery` module has been broken apart to manage dependencies more coherently. There
  are now three modules: `dagster-celery`, `dagster-celery-k8s`, and `dagster-celery-docker`.
- Related to above, the `dagster-celery worker start` command now takes a required `-A` parameter
  which must point to the `app.py` file within the appropriate module. E.g if you are using the
  `celery_k8s_job_executor` then you must use the `-A dagster_celery_k8s.app` option when using the
  `celery` or `dagster-celery` cli tools. Similar for the `celery_docker_executor`:
  `-A dagster_celery_docker.app` must be used.
- Renamed the `input_hydration_config` and `output_materialization_config` decorators to
  `dagster_type_` and `dagster_type_materializer` respectively. Renamed DagsterType's
  `input_hydration_config` and `output_materialization_config` arguments to `loader` and `materializer` respectively.

**New**

- New pipeline scoped runs tab in Dagit
- Add the following Dask Job Queue clusters: moab, sge, lsf, slurm, oar (thanks @DavidKatz-il!)
- K8s resource-requirements for run coordinator pods can be specified using the `dagster-k8s/ resource_requirements` tag on pipeline definitions:

  ```python
  @pipeline(
      tags={
          'dagster-k8s/resource_requirements': {
              'requests': {'cpu': '250m', 'memory': '64Mi'},
              'limits': {'cpu': '500m', 'memory': '2560Mi'},
          }
      },
  )
  def foo_bar_pipeline():
  ```

- Added better error messaging in dagit for partition set and schedule configuration errors
- An initial version of the CeleryDockerExecutor was added (thanks @mrdrprofuroboros!). The celery
  workers will launch tasks in docker containers.
- **Experimental:** Great Expectations integration is currently under development in the new library
  dagster-ge. Example usage can be found [here](https://github.com/dagster-io/dagster/blob/master/python_modules/libraries/dagster-ge/dagster_ge/examples/ge_demo.py)

## 0.8.5

**Breaking Changes**

- Python 3.5 is no longer under test.
- `Engine` and `ExecutorConfig` have been deleted in favor of `Executor`. Instead of the `@executor` decorator decorating a function that returns an `ExecutorConfig` it should now decorate a function that returns an `Executor`.

**New**

- The python built-in `dict` can be used as an alias for `Permissive()` within a config schema declaration.
- Use `StringSource` in the `S3ComputeLogManager` configuration schema to support using environment variables in the configuration (Thanks @mrdrprofuroboros!)
- Improve Backfill CLI help text
- Add options to spark_df_output_schema (Thanks @DavidKatz-il!)
- Helm: Added support for overriding the PostgreSQL image/version used in the init container checks.
- Update celery k8s helm chart to include liveness checks for celery workers and flower
- Support step level retries to celery k8s executor

**Bugfixes**

- Improve error message shown when a RepositoryDefinition returns objects that are not one of the allowed definition types (Thanks @sd2k!)
- Show error message when `$DAGSTER_HOME` environment variable is not an absolute path (Thanks @AndersonReyes!)
- Update default value for `staging_prefix` in the `DatabricksPySparkStepLauncher` configuration to be an absolute path (Thanks @sd2k!)
- Improve error message shown when Databricks logs can't be retrieved (Thanks @sd2k!)
- Fix errors in documentation fo `input_hydration_config` (Thanks @joeyfreund!)

## 0.8.4

**Bugfix**

- Reverted changed in 0.8.3 that caused error during run launch in certain circumstances
- Updated partition graphs on schedule page to select most recent run
- Forced reload of partitions for partition sets to ensure not serving stale data

**New**

- Added reload button to dagit to reload current repository
- Added option to wipe a single asset key by using `dagster asset wipe <asset_key>`
- Simplified schedule page, removing ticks table, adding tags for last tick attempt
- Better debugging tools for launch errors

## 0.8.3

**Breaking Changes**

- Previously, the `gcs_resource` returned a `GCSResource` wrapper which had a single `client` property that returned a `google.cloud.storage.client.Client`. Now, the `gcs_resource` returns the client directly.

  To update solids that use the `gcp_resource`, change:

  ```
  context.resources.gcs.client
  ```

  To:

  ```
  context.resources.gcs
  ```

**New**

- Introduced a new Python API `reexecute_pipeline` to reexecute an existing pipeline run.
- Performance improvements in Pipeline Overview and other pages.
- Long metadata entries in the asset details view are now scrollable.
- Added a `project` field to the `gcs_resource` in `dagster_gcp`.
- Added new CLI command `dagster asset wipe` to remove all existing asset keys.

**Bugfix**

- Several Dagit bugfixes and performance improvements
- Fixes pipeline execution issue with custom run launchers that call `executeRunInProcess`.
- Updates `dagster schedule up` output to be repository location scoped

## 0.8.2

**Bugfix**

- Fixes issues with `dagster instance migrate`.
- Fixes bug in `launch_scheduled_execution` that would mask configuration errors.
- Fixes bug in dagit where schedule related errors were not shown.
- Fixes JSON-serialization error in `dagster-k8s` when specifying per-step resources.

**New**

- Makes `label` optional parameter for materializations with `asset_key` specified.
- Changes `Assets` page to have a typeahead selector and hierarchical views based on asset_key path.
- _dagster-ssh_
  - adds SFTP get and put functions to `SSHResource`, replacing sftp_solid.

**Docs**

- Various docs corrections

## 0.8.1

**Bugfix**

- Fixed a file descriptor leak that caused `OSError: [Errno 24] Too many open files` when enough
  temporary files were created.
- Fixed an issue where an empty config in the Playground would unexpectedly be marked as invalid
  YAML.
- Removed "config" deprecation warnings for dask and celery executors.

**New**

- Improved performance of the Assets page.

## 0.8.0 "In The Zone"

**Major Changes**

Please see the `080_MIGRATION.md` migration guide for details on updating existing code to be
compatible with 0.8.0

- _Workspace, host and user process separation, and repository definition_ Dagit and other tools no
  longer load a single repository containing user definitions such as pipelines into the same
  process as the framework code. Instead, they load a "workspace" that can contain multiple
  repositories sourced from a variety of different external locations (e.g., Python modules and
  Python virtualenvs, with containers and source control repositories soon to come).

  The repositories in a workspace are loaded into their own "user" processes distinct from the
  "host" framework process. Dagit and other tools now communicate with user code over an IPC
  mechanism. This architectural change has a couple of advantages:

  - Dagit no longer needs to be restarted when there is an update to user code.
  - Users can use repositories to organize their pipelines, but still work on all of their
    repositories using a single running Dagit.
  - The Dagit process can now run in a separate Python environment from user code so pipeline
    dependencies do not need to be installed into the Dagit environment.
  - Each repository can be sourced from a separate Python virtualenv, so teams can manage their
    dependencies (or even their own Python versions) separately.

  We have introduced a new file format, `workspace.yaml`, in order to support this new architecture.
  The workspace yaml encodes what repositories to load and their location, and supersedes the
  `repository.yaml` file and associated machinery.

  As a consequence, Dagster internals are now stricter about how pipelines are loaded. If you have
  written scripts or tests in which a pipeline is defined and then passed across a process boundary
  (e.g., using the `multiprocess_executor` or dagstermill), you may now need to wrap the pipeline
  in the `reconstructable` utility function for it to be reconstructed across the process boundary.

  In addition, rather than instantiate the `RepositoryDefinition` class directly, users should now
  prefer the `@repository` decorator. As part of this change, the `@scheduler` and
  `@repository_partitions` decorators have been removed, and their functionality subsumed under
  `@repository`.

* _Dagit organization_ The Dagit interface has changed substantially and is now oriented around
  pipelines. Within the context of each pipeline in an environment, the previous "Pipelines" and
  "Solids" tabs have been collapsed into the "Definition" tab; a new "Overview" tab provides
  summary information about the pipeline, its schedules, its assets, and recent runs; the previous
  "Playground" tab has been moved within the context of an individual pipeline. Related runs (e.g.,
  runs created by re-executing subsets of previous runs) are now grouped together in the Playground
  for easy reference. Dagit also now includes more advanced support for display of scheduled runs
  that may not have executed ("schedule ticks"), as well as longitudinal views over scheduled runs,
  and asset-oriented views of historical pipeline runs.

* _Assets_ Assets are named materializations that can be generated by your pipeline solids, which
  support specialized views in Dagit. For example, if we represent a database table with an asset
  key, we can now index all of the pipelines and pipeline runs that materialize that table, and
  view them in a single place. To use the asset system, you must enable an asset-aware storage such
  as Postgres.

* _Run launchers_ The distinction between "starting" and "launching" a run has been effaced. All
  pipeline runs instigated through Dagit now make use of the `RunLauncher` configured on the
  Dagster instance, if one is configured. Additionally, run launchers can now support termination of
  previously launched runs. If you have written your own run launcher, you may want to update it to
  support termination. Note also that as of 0.7.9, the semantics of `RunLauncher.launch_run` have
  changed; this method now takes the `run_id` of an existing run and should no longer attempt to
  create the run in the instance.

* _Flexible reexecution_ Pipeline re-execution from Dagit is now fully flexible. You may
  re-execute arbitrary subsets of a pipeline's execution steps, and the re-execution now appears
  in the interface as a child run of the original execution.

* _Support for historical runs_ Snapshots of pipelines and other Dagster objects are now persisted
  along with pipeline runs, so that historial runs can be loaded for review with the correct
  execution plans even when pipeline code has changed. This prepares the system to be able to diff
  pipeline runs and other objects against each other.

* _Step launchers and expanded support for PySpark on EMR and Databricks_ We've introduced a new
  `StepLauncher` abstraction that uses the resource system to allow individual execution steps to
  be run in separate processes (and thus on separate execution substrates). This has made extensive
  improvements to our PySpark support possible, including the option to execute individual PySpark
  steps on EMR using the `EmrPySparkStepLauncher` and on Databricks using the
  `DatabricksPySparkStepLauncher` The `emr_pyspark` example demonstrates how to use a step launcher.

* _Clearer names_ What was previously known as the environment dictionary is now called the
  `run_config`, and the previous `environment_dict` argument to APIs such as `execute_pipeline` is
  now deprecated. We renamed this argument to focus attention on the configuration of the run
  being launched or executed, rather than on an ambiguous "environment". We've also renamed the
  `config` argument to all use definitions to be `config_schema`, which should reduce ambiguity
  between the configuration schema and the value being passed in some particular case. We've also
  consolidated and improved documentation of the valid types for a config schema.

* _Lakehouse_ We're pleased to introduce Lakehouse, an experimental, alternative programming model
  for data applications, built on top of Dagster core. Lakehouse allows developers to define data
  applications in terms of data assets, such as database tables or ML models, rather than in terms
  of the computations that produce those assets. The `simple_lakehouse` example gives a taste of
  what it's like to program in Lakehouse. We'd love feedback on whether this model is helpful!

* _Airflow ingest_ We've expanded the tooling available to teams with existing Airflow installations
  that are interested in incrementally adopting Dagster. Previously, we provided only injection
  tools that allowed developers to write Dagster pipelines and then compile them into Airflow DAGs
  for execution. We've now added ingestion tools that allow teams to move to Dagster for execution
  without having to rewrite all of their legacy pipelines in Dagster. In this approach, Airflow
  DAGs are kept in their own container/environment, compiled into Dagster pipelines, and run via
  the Dagster orchestrator. See the `airflow_ingest` example for details!

**Breaking Changes**

- _dagster_

  - The `@scheduler` and `@repository_partitions` decorators have been removed. Instances of
    `ScheduleDefinition` and `PartitionSetDefinition` belonging to a repository should be specified
    using the `@repository` decorator instead.
  - Support for the Dagster solid selection DSL, previously introduced in Dagit, is now uniform
    throughout the Python codebase, with the previous `solid_subset` arguments (`--solid-subset` in
    the CLI) being replaced by `solid_selection` (`--solid-selection`). In addition to the names of
    individual solids, this argument now supports selection queries like `*solid_name++` (i.e.,
    `solid_name`, all of its ancestors, its immediate descendants, and their immediate descendants).
  - The built-in Dagster type `Path` has been removed.
  - `PartitionSetDefinition` names, including those defined by a `PartitionScheduleDefinition`,
    must now be unique within a single repository.
  - Asset keys are now sanitized for non-alphanumeric characters. All characters besides
    alphanumerics and `_` are treated as path delimiters. Asset keys can also be specified using
    `AssetKey`, which accepts a list of strings as an explicit path. If you are running 0.7.10 or
    later and using assets, you may need to migrate your historical event log data for asset keys
    from previous runs to be attributed correctly. This `event_log` data migration can be invoked
    as follows:

    ```python
    from dagster.core.storage.event_log.migration import migrate_event_log_data
    from dagster import DagsterInstance

    migrate_event_log_data(instance=DagsterInstance.get())
    ```

  - The interface of the `Scheduler` base class has changed substantially. If you've written a
    custom scheduler, please get in touch!
  - The partitioned schedule decorators now generate `PartitionSetDefinition` names using
    the schedule name, suffixed with `_partitions`.
  - The `repository` property on `ScheduleExecutionContext` is no longer available. If you were
    using this property to pass to `Scheduler` instance methods, this interface has changed
    significantly. Please see the `Scheduler` class documentation for details.
  - The CLI option `--celery-base-priority` is no longer available for the command:
    `dagster pipeline backfill`. Use the tags option to specify the celery priority, (e.g.
    `dagster pipeline backfill my_pipeline --tags '{ "dagster-celery/run_priority": 3 }'`
  - The `execute_partition_set` API has been removed.
  - The deprecated `is_optional` parameter to `Field` and `OutputDefinition` has been removed.
    Use `is_required` instead.
  - The deprecated `runtime_type` property on `InputDefinition` and `OutputDefinition` has been
    removed. Use `dagster_type` instead.
  - The deprecated `has_runtime_type`, `runtime_type_named`, and `all_runtime_types` methods on
    `PipelineDefinition` have been removed. Use `has_dagster_type`, `dagster_type_named`, and
    `all_dagster_types` instead.
  - The deprecated `all_runtime_types` method on `SolidDefinition` and `CompositeSolidDefinition`
    has been removed. Use `all_dagster_types` instead.
  - The deprecated `metadata` argument to `SolidDefinition` and `@solid` has been removed. Use
    `tags` instead.
  - The graphviz-based DAG visualization in Dagster core has been removed. Please use Dagit!

- _dagit_

  - `dagit-cli` has been removed, and `dagit` is now the only console entrypoint.

- _dagster-aws_

  - The AWS CLI has been removed.
  - `dagster_aws.EmrRunJobFlowSolidDefinition` has been removed.

- _dagster-bash_

  - This package has been renamed to dagster-shell. The`bash_command_solid` and `bash_script_solid`
    solid factory functions have been renamed to `create_shell_command_solid` and
    `create_shell_script_solid`.

- _dagster-celery_

  - The CLI option `--celery-base-priority` is no longer available for the command:
    `dagster pipeline backfill`. Use the tags option to specify the celery priority, (e.g.
    `dagster pipeline backfill my_pipeline --tags '{ "dagster-celery/run_priority": 3 }'`

- _dagster-dask_

  - The config schema for the `dagster_dask.dask_executor` has changed. The previous config should
    now be nested under the key `local`.

- _dagster-gcp_

  - The `BigQueryClient` has been removed. Use `bigquery_resource` instead.

- _dagster-dbt_

  - The dagster-dbt package has been removed. This was inadequate as a reference integration, and
    will be replaced in 0.8.x.

- _dagster-spark_

  - `dagster_spark.SparkSolidDefinition` has been removed - use `create_spark_solid` instead.
  - The `SparkRDD` Dagster type, which only worked with an in-memory engine, has been removed.

- _dagster-twilio_

  - The `TwilioClient` has been removed. Use `twilio_resource` instead.

**New**

- _dagster_

  - You may now set `asset_key` on any `Materialization` to use the new asset system. You will also
    need to configure an asset-aware storage, such as Postgres. The `longitudinal_pipeline` example
    demonstrates this system.
  - The partitioned schedule decorators now support an optional `end_time`.
  - Opt-in telemetry now reports the Python version being used.

- _dagit_

  - Dagit's GraphQL playground is now available at `/graphiql` as well as at `/graphql`.

- _dagster-aws_

  - The `dagster_aws.S3ComputeLogManager` may now be configured to override the S3 endpoint and
    associated SSL settings.
  - Config string and integer values in the S3 tooling may now be set using either environment
    variables or literals.

- _dagster-azure_

  - We've added the dagster-azure package, with support for Azure Data Lake Storage Gen2; you can
    use the `adls2_system_storage` or, for direct access, the `adls2_resource` resource. (Thanks
    @sd2k!)

- _dagster-dask_

  - Dask clusters are now supported by `dagster_dask.dask_executor`. For full support, you will need
    to install extras with `pip install dagster-dask[yarn, pbs, kube]`. (Thanks @DavidKatz-il!)

- _dagster-databricks_

  - We've added the dagster-databricks package, with support for running PySpark steps on Databricks
    clusters through the `databricks_pyspark_step_launcher`. (Thanks @sd2k!)

- _dagster-gcp_

  - Config string and integer values in the BigQuery, Dataproc, and GCS tooling may now be set
    using either environment variables or literals.

- _dagster-k8s_

  - Added the `CeleryK8sRunLauncher` to submit execution plan steps to Celery task queues for
    execution as k8s Jobs.
  - Added the ability to specify resource limits on a per-pipeline and per-step basis for k8s Jobs.
  - Many improvements and bug fixes to the dagster-k8s Helm chart.

- _dagster-pandas_

  - Config string and integer values in the dagster-pandas input and output schemas may now be set
    using either environment variables or literals.

- _dagster-papertrail_

  - Config string and integer values in the `papertrail_logger` may now be set using either
    environment variables or literals.

- _dagster-pyspark_

  - PySpark solids can now run on EMR, using the `emr_pyspark_step_launcher`, or on Databricks using
    the new dagster-databricks package. The `emr_pyspark` example demonstrates how to use a step
    launcher.

- _dagster-snowflake_

  - Config string and integer values in the `snowflake_resource` may now be set using either
    environment variables or literals.

- _dagster-spark_

  - `dagster_spark.create_spark_solid` now accepts a `required_resource_keys` argument, which
    enables setting up a step launcher for Spark solids, like the `emr_pyspark_step_launcher`.

**Bugfix**

- `dagster pipeline execute` now sets a non-zero exit code when pipeline execution fails.

## 0.7.16

**Bugfix**

- Enabled `NoOpComputeLogManager` to be configured as the `compute_logs` implementation in
  `dagster.yaml`
- Suppressed noisy error messages in logs from skipped steps

## 0.7.15

**New**

- Improve dagster scheduler state reconciliation.

## 0.7.14

**New**

- Dagit now allows re-executing arbitrary step subset via step selector syntax, regardless of
  whether the previous pipeline failed or not.
- Added a search filter for the root Assets page
- Adds tooltip explanations for disabled run actions
- The last output of the cron job command created by the scheduler is now stored in a file. A new
  `dagster schedule logs {schedule_name}` command will show the log file for a given schedule. This
  helps uncover errors like missing environment variables and import errors.
- The Dagit schedule page will now show inconsistency errors between schedule state and the cron
  tab that were previously only displayed by the `dagster schedule debug` command. As before, these
  errors can be resolve using `dagster schedule up`

**Bugfix**

- Fixes an issue with config schema validation on Arrays
- Fixes an issue with initializing K8sRunLauncher when configured via `dagster.yaml`
- Fixes a race condition in Airflow injection logic that happens when multiple Operators try to
  create PipelineRun entries simultaneously.
- Fixed an issue with schedules that had invalid config not logging the appropriate error.

## 0.7.13

**Breaking Changes**

- `dagster pipeline backfill` command no longer takes a `mode` flag. Instead, it uses the mode
  specified on the `PartitionSetDefinition`. Similarly, the runs created from the backfill also use
  the `solid_subset` specified on the `PartitionSetDefinition`

**BugFix**

- Fixes a bug where using solid subsets when launching pipeline runs would fail config validation.
- (dagster-gcp) allow multiple "bq_solid_for_queries" solids to co-exist in a pipeline
- Improve scheduler state reconciliation with dagster-cron scheduler. `dagster schedule` debug
  command will display issues related to missing crob jobs, extraneous cron jobs, and duplicate cron
  jobs. Running `dagster schedule up` will fix any issues.

**New**

- The dagster-airflow package now supports loading Airflow dags without depending on initialized
  Airflow db
- Improvements to the longitudinal partitioned schedule view, including live updates, run filtering,
  and better default states.
- Added user warning for dagster library packages that are out of sync with the core `dagster`
  package.

## 0.7.12

**Bugfix**

- We now only render the subset of an execution plan that has actually executed, and persist that
  subset information along with the snapshot.
- @pipeline and @composite_solid now correctly capture `__doc__` from the function they decorate.
- Fixed a bug with using solid subsets in the Dagit playground

## 0.7.11

**Bugfix**

- Fixed an issue with strict snapshot ID matching when loading historical snapshots, which caused
  errors on the Runs page when viewing historical runs.
- Fixed an issue where `dagster_celery` had introduced a spurious dependency on `dagster_k8s`
  (#2435)
- Fixed an issue where our Airflow, Celery, and Dask integrations required S3 or GCS storage and
  prevented use of filesystem storage. Filesystem storage is now also permitted, to enable use of
  these integrations with distributed filesystems like NFS (#2436).

## 0.7.10

**New**

- `RepositoryDefinition` now takes `schedule_defs` and `partition_set_defs` directly. The loading
  scheme for these definitions via `repository.yaml` under the `scheduler:` and `partitions:` keys
  is deprecated and expected to be removed in 0.8.0.
- Mark published modules as python 3.8 compatible.
- The dagster-airflow package supports loading all Airflow DAGs within a directory path, file path,
  or Airflow DagBag.
- The dagster-airflow package supports loading all 23 DAGs in Airflow example_dags folder and
  execution of 17 of them (see: `make_dagster_repo_from_airflow_example_dags`).
- The dagster-celery CLI tools now allow you to pass additional arguments through to the underlying
  celery CLI, e.g., running `dagster-celery worker start -n my-worker -- --uid=42` will pass the
  `--uid` flag to celery.
- It is now possible to create a `PresetDefinition` that has no environment defined.
- Added `dagster schedule debug` command to help debug scheduler state.
- The `SystemCronScheduler` now verifies that a cron job has been successfully been added to the
  crontab when turning a schedule on, and shows an error message if unsuccessful.

**Breaking Changes**

- A `dagster instance migrate` is required for this release to support the new experimental assets
  view.
- Runs created prior to 0.7.8 will no longer render their execution plans as DAGs. We are only
  rendering execution plans that have been persisted. Logs are still available.
- `Path` is no longer valid in config schemas. Use `str` or `dagster.String` instead.
- Removed the `@pyspark_solid` decorator - its functionality, which was experimental, is subsumed by
  requiring a StepLauncher resource (e.g. emr_pyspark_step_launcher) on the solid.

**Dagit**

- Merged "re-execute", "single-step re-execute", "resume/retry" buttons into one "re-execute" button
  with three dropdown selections on the Run page.

**Experimental**

- Added new `asset_key` string parameter to Materializations and created a new “Assets” tab in Dagit
  to view pipelines and runs associated with these keys. The API and UI of these asset-based are
  likely to change, but feedback is welcome and will be used to inform these changes.
- Added an `emr_pyspark_step_launcher` that enables launching PySpark solids in EMR. The
  "simple_pyspark" example demonstrates how it’s used.

**Bugfix**

- Fixed an issue when running Jupyter notebooks in a Python 2 kernel through dagstermill with
  Dagster running in Python 3.
- Improved error messages produced when dagstermill spins up an in-notebook context.
- Fixed an issue with retrieving step events from `CompositeSolidResult` objects.

## 0.7.9

**Breaking Changes**

- If you are launching runs using `DagsterInstance.launch_run`, this method now takes a run id
  instead of an instance of `PipelineRun`. Additionally, `DagsterInstance.create_run` and
  `DagsterInstance.create_empty_run` have been replaced by `DagsterInstance.get_or_create_run` and
  `DagsterInstance.create_run_for_pipeline`.
- If you have implemented your own `RunLauncher`, there are two required changes:
  - `RunLauncher.launch_run` takes a pipeline run that has already been created. You should remove
    any calls to `instance.create_run` in this method.
  - Instead of calling `startPipelineExecution` (defined in the
    `dagster_graphql.client.query.START_PIPELINE_EXECUTION_MUTATION`) in the run launcher, you
    should call `startPipelineExecutionForCreatedRun` (defined in
    `dagster_graphql.client.query.START_PIPELINE_EXECUTION_FOR_CREATED_RUN_MUTATION`).
  - Refer to the `RemoteDagitRunLauncher` for an example implementation.

**New**

- Improvements to preset and solid subselection in the playground. An inline preview of the pipeline
  instead of a modal when doing subselection, and the correct subselection is chosen when selecting
  a preset.
- Improvements to the log searching. Tokenization and autocompletion for searching messages types
  and for specific steps.
- You can now view the structure of pipelines from historical runs, even if that pipeline no longer
  exists in the loaded repository or has changed structure.
- Historical execution plans are now viewable, even if the pipeline has changed structure.
- Added metadata link to raw compute logs for all StepStart events in PipelineRun view and Step
  view.
- Improved error handling for the scheduler. If a scheduled run has config errors, the errors are
  persisted to the event log for the run and can be viewed in Dagit.

**Bugfix**

- No longer manually dispose sqlalchemy engine in dagster-postgres
- Made boto3 dependency in dagster-aws more flexible (#2418)
- Fixed tooltip UI cleanup in partitioned schedule view

**Documentation**

- Brand new documentation site, available at https://docs.dagster.io
- The tutorial has been restructured to multiple sections, and the examples in intro_tutorial have
  been rearranged to separate folders to reflect this.

## 0.7.8

**Breaking Changes**

- The `execute_pipeline_with_mode` and `execute_pipeline_with_preset` APIs have been dropped in
  favor of new top level arguments to `execute_pipeline`, `mode` and `preset`.
- The use of `RunConfig` to pass options to `execute_pipeline` has been deprecated, and `RunConfig`
  will be removed in 0.8.0.
- The `execute_solid_within_pipeline` and `execute_solids_within_pipeline` APIs, intended to support
  tests, now take new top level arguments `mode` and `preset`.

**New**

- The dagster-aws Redshift resource now supports providing an error callback to debug failed
  queries.
- We now persist serialized execution plans for historical runs. They will render correctly even if
  the pipeline structure has changed or if it does not exist in the current loaded repository.
- Clicking on a pipeline tag in the `Runs` view will apply that tag as a filter.

**Bugfix**

- Fixed a bug where telemetry logger would create a log file (but not write any logs) even when
  telemetry was disabled.

**Experimental**

- The dagster-airflow package supports ingesting Airflow dags and running them as dagster pipelines
  (see: `make_dagster_pipeline_from_airflow_dag`). This is in the early experimentation phase.
- Improved the layout of the experimental partition runs table on the `Schedules` detailed view.

**Documentation**

- Fixed a grammatical error (Thanks @flowersw!)

## 0.7.7

**Breaking Changes**

- The default sqlite and `dagster-postgres` implementations have been altered to extract the
  event `step_key` field as a column, to enable faster per-step queries. You will need to run
  `dagster instance migrate` to update the schema. You may optionally migrate your historical event
  log data to extract the `step_key` using the `migrate_event_log_data` function. This will ensure
  that your historical event log data will be captured in future step-key based views. This
  `event_log` data migration can be invoked as follows:

  ```python
  from dagster.core.storage.event_log.migration import migrate_event_log_data
  from dagster import DagsterInstance

  migrate_event_log_data(instance=DagsterInstance.get())
  ```

- We have made pipeline metadata serializable and persist that along with run information.
  While there are no user-facing features to leverage this yet, it does require an instance
  migration. Run `dagster instance migrate`. If you have already run the migration for the
  `event_log` changes above, you do not need to run it again. Any unforeseen errors related to the
  new `snapshot_id` in the `runs` table or the new `snapshots` table are related to this migration.
- dagster-pandas `ColumnTypeConstraint` has been removed in favor of `ColumnDTypeFnConstraint` and
  `ColumnDTypeInSetConstraint`.

**New**

- You can now specify that dagstermill output notebooks be yielded as an output from dagstermill
  solids, in addition to being materialized.
- You may now set the extension on files created using the `FileManager` machinery.
- dagster-pandas typed `PandasColumn` constructors now support pandas 1.0 dtypes.
- The Dagit Playground has been restructured to make the relationship between Preset, Partition
  Sets, Modes, and subsets more clear. All of these buttons have be reconciled and moved to the
  left side of the Playground.
- Config sections that are required but not filled out in the Dagit playground are now detected
  and labeled in orange.
- dagster-celery config now support using `env:` to load from environment variables.

**Bugfix**

- Fixed a bug where selecting a preset in `dagit` would not populate tags specified on the pipeline
  definition.
- Fixed a bug where metadata attached to a raised `Failure` was not displayed in the error modal in
  `dagit`.
- Fixed an issue where reimporting dagstermill and calling `dagstermill.get_context()` outside of
  the parameters cell of a dagstermill notebook could lead to unexpected behavior.
- Fixed an issue with connection pooling in dagster-postgres, improving responsiveness when using
  the Postgres-backed storages.

**Experimental**

- Added a longitudinal view of runs for on the `Schedule` tab for scheduled, partitioned pipelines.
  Includes views of run status, execution time, and materializations across partitions. The UI is
  in flux and is currently optimized for daily schedules, but feedback is welcome.

## 0.7.6

**Breaking Changes**

- `default_value` in `Field` no longer accepts native instances of python enums. Instead
  the underlying string representation in the config system must be used.
- `default_value` in `Field` no longer accepts callables.
- The `dagster_aws` imports have been reorganized; you should now import resources from
  `dagster_aws.<AWS service name>`. `dagster_aws` provides `s3`, `emr`, `redshift`, and `cloudwatch`
  modules.
- The `dagster_aws` S3 resource no longer attempts to model the underlying boto3 API, and you can
  now just use any boto3 S3 API directly on a S3 resource, e.g.
  `context.resources.s3.list_objects_v2`. (#2292)

**New**

- New `Playground` view in `dagit` showing an interactive config map
- Improved storage and UI for showing schedule attempts
- Added the ability to set default values in `InputDefinition`
- Added CLI command `dagster pipeline launch` to launch runs using a configured `RunLauncher`
- Added ability to specify pipeline run tags using the CLI
- Added a `pdb` utility to `SolidExecutionContext` to help with debugging, available within a solid
  as `context.pdb`
- Added `PresetDefinition.with_additional_config` to allow for config overrides
- Added resource name to log messages generated during resource initialization
- Added grouping tags for runs that have been retried / reexecuted.

**Bugfix**

- Fixed a bug where date range partitions with a specified end date was clipping the last day
- Fixed an issue where some schedule attempts that failed to start would be marked running forever.
- Fixed the `@weekly` partitioned schedule decorator
- Fixed timezone inconsistencies between the runs view and the schedules view
- Integers are now accepted as valid values for Float config fields
- Fixed an issue when executing dagstermill solids with config that contained quote characters.

**dagstermill**

- The Jupyter kernel to use may now be specified when creating dagster notebooks with the `--kernel`
  flag.

**dagster-dbt**

- `dbt_solid` now has a `Nothing` input to allow for sequencing

**dagster-k8s**

- Added `get_celery_engine_config` to select celery engine, leveraging Celery infrastructure

**Documentation**

- Improvements to the airline and bay bikes demos
- Improvements to our dask deployment docs (Thanks jswaney!!)

## 0.7.5

**New**

- Added the `IntSource` type, which lets integers be set from environment variables in config.
- You may now set tags on pipeline definitions. These will resolve in the following cases:

  1. Loading in the playground view in Dagit will pre-populate the tag container.
  2. Loading partition sets from the preset/config picker will pre-populate the tag container with
     the union of pipeline tags and partition tags, with partition tags taking precedence.
  3. Executing from the CLI will generate runs with the pipeline tags.
  4. Executing programmatically using the `execute_pipeline` api will create a run with the union
     of pipeline tags and `RunConfig` tags, with `RunConfig` tags taking precedence.
  5. Scheduled runs (both launched and executed) will have the union of pipeline tags and the
     schedule tags function, with the schedule tags taking precedence.

- Output materialization configs may now yield multiple Materializations, and the tutorial has
  been updated to reflect this.

- We now export the `SolidExecutionContext` in the public API so that users can correctly type hint
  solid compute functions.

**Dagit**

- Pipeline run tags are now preserved when resuming/retrying from Dagit.
- Scheduled run stats are now grouped by partition.
- A "preparing" section has been added to the execution viewer. This shows steps that are in
  progress of starting execution.
- Markers emitted by the underlying execution engines are now visualized in the Dagit execution
  timeline.

**Bugfix**

- Resume/retry now works as expected in the presence of solids that yield optional outputs.
- Fixed an issue where dagster-celery workers were failing to start in the presence of config
  values that were `None`.
- Fixed an issue with attempting to set `threads_per_worker` on Dask distributed clusters.

**dagster-postgres**

- All postgres config may now be set using environment variables in config.

**dagster-aws**

- The `s3_resource` now exposes a `list_objects_v2` method corresponding to the underlying boto3
  API. (Thanks, @basilvetas!)
- Added the `redshift_resource` to access Redshift databases.

**dagster-k8s**

- The `K8sRunLauncher` config now includes the `load_kubeconfig` and `kubeconfig_file` options.

**Documentation**

- Fixes and improvements.

**Dependencies**

- dagster-airflow no longer pins its werkzeug dependency.

**Community**

- We've added opt-in telemetry to Dagster so we can collect usage statistics in order to inform
  development priorities. Telemetry data will motivate projects such as adding features in
  frequently-used parts of the CLI and adding more examples in the docs in areas where users
  encounter more errors.

  We will not see or store solid definitions (including generated context) or pipeline definitions
  (including modes and resources). We will not see or store any data that is processed within solids
  and pipelines.

  If you'd like to opt in to telemetry, please add the following to `$DAGSTER_HOME/dagster.yaml`:

      telemetry:
        enabled: true

- Thanks to @basilvetas and @hspak for their contributions!

## 0.7.4

**New**

- It is now possible to use Postgres to back schedule storage by configuring
  `dagster_postgres.PostgresScheduleStorage` on the instance.
- Added the `execute_pipeline_with_mode` API to allow executing a pipeline in test with a specific
  mode without having to specify `RunConfig`.
- Experimental support for retries in the Celery executor.
- It is now possible to set run-level priorities for backfills run using the Celery executor by
  passing `--celery-base-priority` to `dagster pipeline backfill`.
- Added the `@weekly` schedule decorator.

**Deprecations**

- The `dagster-ge` library has been removed from this release due to drift from the underlying
  Great Expectations implementation.

**dagster-pandas**

- `PandasColumn` now includes an `is_optional` flag, replacing the previous
  `ColumnExistsConstraint`.
- You can now pass the `ignore_missing_values flag` to `PandasColumn` in order to apply column
  constraints only to the non-missing rows in a column.

**dagster-k8s**

- The Helm chart now includes provision for an Ingress and for multiple Celery queues.

**Documentation**

- Improvements and fixes.

## 0.7.3

**New**

- It is now possible to configure a Dagit instance to disable executing pipeline runs in a local
  subprocess.
- Resource initialization, teardown, and associated failure states now emit structured events
  visible in Dagit. Structured events for pipeline errors and multiprocess execution have been
  consolidated and rationalized.
- Support Redis queue provider in `dagster-k8s` Helm chart.
- Support external postgresql in `dagster-k8s` Helm chart.

**Bugfix**

- Fixed an issue with inaccurate timings on some resource initializations.
- Fixed an issue that could cause the multiprocess engine to spin forever.
- Fixed an issue with default value resolution when a config value was set using `SourceString`.
- Fixed an issue when loading logs from a pipeline belonging to a different repository in Dagit.
- Fixed an issue with where the CLI command `dagster schedule up` would fail in certain scenarios
  with the `SystemCronScheduler`.

**Pandas**

- Column constraints can now be configured to permit NaN values.

**Dagstermill**

- Removed a spurious dependency on sklearn.

**Docs**

- Improvements and fixes to docs.
- Restored dagster.readthedocs.io.

**Experimental**

- An initial implementation of solid retries, throwing a `RetryRequested` exception, was added.
  This API is experimental and likely to change.

**Other**

- Renamed property `runtime_type` to `dagster_type` in definitions. The following are deprecated
  and will be removed in a future version.
  - `InputDefinition.runtime_type` is deprecated. Use `InputDefinition.dagster_type` instead.
  - `OutputDefinition.runtime_type` is deprecated. Use `OutputDefinition.dagster_type` instead.
  - `CompositeSolidDefinition.all_runtime_types` is deprecated. Use
    `CompositeSolidDefinition.all_dagster_types` instead.
  - `SolidDefinition.all_runtime_types` is deprecated. Use `SolidDefinition.all_dagster_types`
    instead.
  - `PipelineDefinition.has_runtime_type` is deprecated. Use `PipelineDefinition.has_dagster_type`
    instead.
  - `PipelineDefinition.runtime_type_named` is deprecated. Use
    `PipelineDefinition.dagster_type_named` instead.
  - `PipelineDefinition.all_runtime_types` is deprecated. Use
    `PipelineDefinition.all_dagster_types` instead.

## 0.7.2

**Docs**

- New docs site at docs.dagster.io.
- dagster.readthedocs.io is currently stale due to availability issues.

**New**

- Improvements to S3 Resource. (Thanks @dwallace0723!)
- Better error messages in Dagit.
- Better font/styling support in Dagit.
- Changed `OutputDefinition` to take `is_required` rather than `is_optional` argument. This is to
  remain consistent with changes to `Field` in 0.7.1 and to avoid confusion
  with python's typing and dagster's definition of `Optional`, which indicates None-ability,
  rather than existence. `is_optional` is deprecated and will be removed in a future version.
- Added support for Flower in dagster-k8s.
- Added support for environment variable config in dagster-snowflake.

**Bugfixes**

- Improved performance in Dagit waterfall view.
- Fixed bug when executing solids downstream of a skipped solid.
- Improved navigation experience for pipelines in Dagit.
- Fixed for the dagster-aws CLI tool.
- Fixed issue starting Dagit without DAGSTER_HOME set on windows.
- Fixed pipeline subset execution in partition-based schedules.

## 0.7.1

**Dagit**

- Dagit now looks up an available port on which to run when the default port is
  not available. (Thanks @rparrapy!)

**dagster_pandas**

- Hydration and materialization are now configurable on `dagster_pandas` dataframes.

**dagster_aws**

- The `s3_resource` no longer uses an unsigned session by default.

**Bugfixes**

- Type check messages are now displayed in Dagit.
- Failure metadata is now surfaced in Dagit.
- Dagit now correctly displays the execution time of steps that error.
- Error messages now appear correctly in console logging.
- GCS storage is now more robust to transient failures.
- Fixed an issue where some event logs could be duplicated in Dagit.
- Fixed an issue when reading config from an environment variable that wasn't set.
- Fixed an issue when loading a repository or pipeline from a file target on Windows.
- Fixed an issue where deleted runs could cause the scheduler page to crash in Dagit.

**Documentation**

- Expanded and improved docs and error messages.

## 0.7.0 "Waiting to Exhale"

**Breaking Changes**

There are a substantial number of breaking changes in the 0.7.0 release.
Please see `070_MIGRATION.md` for instructions regarding migrating old code.

**_Scheduler_**

- The scheduler configuration has been moved from the `@schedules` decorator to `DagsterInstance`.
  Existing schedules that have been running are no longer compatible with current storage. To
  migrate, remove the `scheduler` argument on all `@schedules` decorators:

  instead of:

  ```
  @schedules(scheduler=SystemCronScheduler)
  def define_schedules():
    ...
  ```

  Remove the `scheduler` argument:

  ```
  @schedules
  def define_schedules():
    ...
  ```

  Next, configure the scheduler on your instance by adding the following to
  `$DAGSTER_HOME/dagster.yaml`:

  ```
  scheduler:
    module: dagster_cron.cron_scheduler
    class: SystemCronScheduler
  ```

  Finally, if you had any existing schedules running, delete the existing `$DAGSTER_HOME/schedules`
  directory and run `dagster schedule wipe && dagster schedule up` to re-instatiate schedules in a
  valid state.

- The `should_execute` and `environment_dict_fn` argument to `ScheduleDefinition` now have a
  required first argument `context`, representing the `ScheduleExecutionContext`

**_Config System Changes_**

- In the config system, `Dict` has been renamed to `Shape`; `List` to `Array`; `Optional` to
  `Noneable`; and `PermissiveDict` to `Permissive`. The motivation here is to clearly delineate
  config use cases versus cases where you are using types as the inputs and outputs of solids as
  well as python typing types (for mypy and friends). We believe this will be clearer to users in
  addition to simplifying our own implementation and internal abstractions.

  Our recommended fix is _not_ to use `Shape` and `Array`, but instead to use our new condensed
  config specification API. This allow one to use bare dictionaries instead of `Shape`, lists with
  one member instead of `Array`, bare types instead of `Field` with a single argument, and python
  primitive types (`int`, `bool` etc) instead of the dagster equivalents. These result in
  dramatically less verbose config specs in most cases.

  So instead of

  ```
  from dagster import Shape, Field, Int, Array, String
  # ... code
  config=Shape({ # Dict prior to change
        'some_int' : Field(Int),
        'some_list: Field(Array[String]) # List prior to change
    })
  ```

  one can instead write:

  ```
  config={'some_int': int, 'some_list': [str]}
  ```

  No imports and much simpler, cleaner syntax.

- `config_field` is no longer a valid argument on `solid`, `SolidDefinition`, `ExecutorDefintion`,
  `executor`, `LoggerDefinition`, `logger`, `ResourceDefinition`, `resource`, `system_storage`, and
  `SystemStorageDefinition`. Use `config` instead.
- For composite solids, the `config_fn` no longer takes a `ConfigMappingContext`, and the context
  has been deleted. To upgrade, remove the first argument to `config_fn`.

  So instead of

  ```
  @composite_solid(config={}, config_fn=lambda context, config: {})
  ```

  one must instead write:

  ```
  @composite_solid(config={}, config_fn=lambda config: {})
  ```

- `Field` takes a `is_required` rather than a `is_optional` argument. This is to avoid confusion
  with python's typing and dagster's definition of `Optional`, which indicates None-ability,
  rather than existence. `is_optional` is deprecated and will be removed in a future version.

**_Required Resources_**

- All solids, types, and config functions that use a resource must explicitly list that
  resource using the argument `required_resource_keys`. This is to enable efficient
  resource management during pipeline execution, especially in a multiprocessing or
  remote execution environment.

- The `@system_storage` decorator now requires argument `required_resource_keys`, which was
  previously optional.

**_Dagster Type System Changes_**

- `dagster.Set` and `dagster.Tuple` can no longer be used within the config system.
- Dagster types are now instances of `DagsterType`, rather than a class than inherits from
  `RuntimeType`. Instead of dynamically generating a class to create a custom runtime type, just
  create an instance of a `DagsterType`. The type checking function is now an argument to the
  `DagsterType`, rather than an abstract method that has to be implemented in
  a subclass.
- `RuntimeType` has been renamed to `DagsterType` is now an encouraged API for type creation.
- Core type check function of DagsterType can now return a naked `bool` in addition
  to a `TypeCheck` object.
- `type_check_fn` on `DagsterType` (formerly `type_check` and `RuntimeType`, respectively) now
  takes a first argument `context` of type `TypeCheckContext` in addition to the second argument of
  `value`.
- `define_python_dagster_type` has been eliminated in favor of `PythonObjectDagsterType` .
- `dagster_type` has been renamed to `usable_as_dagster_type`.
- `as_dagster_type` has been removed and similar capabilities added as
  `make_python_type_usable_as_dagster_type`.
- `PythonObjectDagsterType` and `usable_as_dagster_type` no longer take a `type_check` argument. If
  a custom type_check is needed, use `DagsterType`.
- As a consequence of these changes, if you were previously using `dagster_pyspark` or
  `dagster_pandas` and expecting Pyspark or Pandas types to work as Dagster types, e.g., in type
  annotations to functions decorated with `@solid` to indicate that they are input or output types
  for a solid, you will need to call `make_python_type_usable_as_dagster_type` from your code in
  order to map the Python types to the Dagster types, or just use the Dagster types
  (`dagster_pandas.DataFrame` instead of `pandas.DataFrame`) directly.

**_Other_**

- We no longer publish base Docker images. Please see the updated deployment docs for an example
  Dockerfile off of which you can work.
- `step_metadata_fn` has been removed from `SolidDefinition` & `@solid`.
- `SolidDefinition` & `@solid` now takes `tags` and enforces that values are strings or
  are safely encoded as JSON. `metadata` is deprecated and will be removed in a future version.
- `resource_mapper_fn` has been removed from `SolidInvocation`.

**New**

- Dagit now includes a much richer execution view, with a Gantt-style visualization of step
  execution and a live timeline.
- Early support for Python 3.8 is now available, and Dagster/Dagit along with many of our libraries
  are now tested against 3.8. Note that several of our upstream dependencies have yet to publish
  wheels for 3.8 on all platforms, so running on Python 3.8 likely still involves building some
  dependencies from source.
- `dagster/priority` tags can now be used to prioritize the order of execution for the built-in
  in-process and multiprocess engines.
- `dagster-postgres` storages can now be configured with separate arguments and environment
  variables, such as:

  ```
  run_storage:
    module: dagster_postgres.run_storage
    class: PostgresRunStorage
    config:
      postgres_db:
        username: test
        password:
          env: ENV_VAR_FOR_PG_PASSWORD
        hostname: localhost
        db_name: test
  ```

- Support for `RunLauncher`s on `DagsterInstance` allows for execution to be "launched" outside of
  the Dagit/Dagster process. As one example, this is used by `dagster-k8s` to submit pipeline
  execution as a Kubernetes Job.
- Added support for adding tags to runs initiated from the `Playground` view in Dagit.
- Added `@monthly_schedule` decorator.
- Added `Enum.from_python_enum` helper to wrap Python enums for config. (Thanks @kdungs!)
- **[dagster-bash]** The Dagster bash solid factory now passes along `kwargs` to the underlying
  solid construction, and now has a single `Nothing` input by default to make it easier to create a
  sequencing dependency. Also, logs are now buffered by default to make execution less noisy.
- **[dagster-aws]** We've improved our EMR support substantially in this release. The
  `dagster_aws.emr` library now provides an `EmrJobRunner` with various utilities for creating EMR
  clusters, submitting jobs, and waiting for jobs/logs. We also now provide a
  `emr_pyspark_resource`, which together with the new `@pyspark_solid` decorator makes moving
  pyspark execution from your laptop to EMR as simple as changing modes.
  **[dagster-pandas]** Added `create_dagster_pandas_dataframe_type`, `PandasColumn`, and
  `Constraint` API's in order for users to create custom types which perform column validation,
  dataframe validation, summary statistics emission, and dataframe serialization/deserialization.
- **[dagster-gcp]** GCS is now supported for system storage, as well as being supported with the
  Dask executor. (Thanks @habibutsu!) Bigquery solids have also been updated to support the new API.

**Bugfix**

- Ensured that all implementations of `RunStorage` clean up pipeline run tags when a run
  is deleted. Requires a storage migration, using `dagster instance migrate`.
- The multiprocess and Celery engines now handle solid subsets correctly.
- The multiprocess and Celery engines will now correctly emit skip events for steps downstream of
  failures and other skips.
- The `@solid` and `@lambda_solid` decorators now correctly wrap their decorated functions, in the
  sense of `functools.wraps`.
- Performance improvements in Dagit when working with runs with large configurations.
- The Helm chart in `dagster_k8s` has been hardened against various failure modes and is now
  compatible with Helm 2.
- SQLite run and event log storages are more robust to concurrent use.
- Improvements to error messages and to handling of user code errors in input hydration and output
  materialization logic.
- Fixed an issue where the Airflow scheduler could hang when attempting to load dagster-airflow
  pipelines.
- We now handle our SQLAlchemy connections in a more canonical way (thanks @zzztimbo!).
- Fixed an issue using S3 system storage with certain custom serialization strategies.
- Fixed an issue leaking orphan processes from compute logging.
- Fixed an issue leaking semaphores from Dagit.
- Setting the `raise_error` flag in `execute_pipeline` now actually raises user exceptions instead
  of a wrapper type.

**Documentation**

- Our docs have been reorganized and expanded (thanks @habibutsu, @vatervonacht, @zzztimbo). We'd
  love feedback and contributions!

**Thank you**
Thank you to all of the community contributors to this release!! In alphabetical order: @habibutsu,
@kdungs, @vatervonacht, @zzztimbo.

## 0.6.9

**Bugfix**

- Improved SQLite concurrency issues, uncovered while using concurrent nodes in Airflow
- Fixed sqlalchemy warnings (thanks @zzztimbo!)
- Fixed Airflow integration issue where a Dagster child process triggered a signal handler of a
  parent Airflow process via a process fork
- Fixed GCS and AWS intermediate store implementations to be compatible with read/write mode
  serialization strategies
- Improve test stability

**Documentation**

- Improved descriptions for setting up the cron scheduler (thanks @zzztimbo!)

## 0.6.8

**New**

- Added the dagster-github library, a community contribution from @Ramshackle-Jamathon and
  @k-mahoney!

**dagster-celery**

- Simplified and improved config handling.
- An engine event is now emitted when the engine fails to connect to a broker.

**Bugfix**

- Fixes a file descriptor leak when running many concurrent dagster-graphql queries (e.g., for
  backfill).
- The `@pyspark_solid` decorator now handles inputs correctly.
- The handling of solid compute functions that accept kwargs but which are decorated with explicit
  input definitions has been rationalized.
- Fixed race conditions in concurrent execution using SQLite event log storage with concurrent
  execution, uncovered by upstream improvements in the Python inotify library we use.

**Documentation**

- Improved error messages when using system storages that don't fulfill executor requirements.

## 0.6.7

**New**

- We are now more permissive when specifying configuration schema in order make constructing
  configuration schema more concise.
- When specifying the value of scalar inputs in config, one can now specify that value directly as
  the key of the input, rather than having to embed it within a `value` key.

**Breaking**

- The implementation of SQL-based event log storages has been consolidated,
  which has entailed a schema change. If you have event logs stored in a
  Postgres- or SQLite-backed event log storage, and you would like to maintain
  access to these logs, you should run `dagster instance migrate`. To check
  what event log storages you are using, run `dagster instance info`.
- Type matches on both sides of an `InputMapping` or `OutputMapping` are now enforced.

**New**

- Dagster is now tested on Python 3.8
- Added the dagster-celery library, which implements a Celery-based engine for parallel pipeline
  execution.
- Added the dagster-k8s library, which includes a Helm chart for a simple Dagit installation on a
  Kubernetes cluster.

**Dagit**

- The Explore UI now allows you to render a subset of a large DAG via a new solid
  query bar that accepts terms like `solid_name+*` and `+solid_name+`. When viewing
  very large DAGs, nothing is displayed by default and `*` produces the original behavior.
- Performance improvements in the Explore UI and config editor for large pipelines.
- The Explore UI now includes a zoom slider that makes it easier to navigate large DAGs.
- Dagit pages now render more gracefully in the presence of inconsistent run storage and event logs.
- Improved handling of GraphQL errors and backend programming errors.
- Minor display improvements.

**dagster-aws**

- A default prefix is now configurable on APIs that use S3.
- S3 APIs now parametrize `region_name` and `endpoint_url`.

**dagster-gcp**

- A default prefix is now configurable on APIs that use GCS.

**dagster-postgres**

- Performance improvements for Postgres-backed storages.

**dagster-pyspark**

- Pyspark sessions may now be configured to be held open after pipeline execution completes, to
  enable extended test cases.

**dagster-spark**

- `spark_outputs` must now be specified when initializing a `SparkSolidDefinition`, rather than in
  config.
- Added new `create_spark_solid` helper and new `spark_resource`.
- Improved EMR implementation.

**Bugfix**

- Fixed an issue retrieving output values using `SolidExecutionResult` (e.g., in test) for
  dagster-pyspark solids.
- Fixes an issue when expanding composite solids in Dagit.
- Better errors when solid names collide.
- Config mapping in composite solids now works as expected when the composite solid has no top
  level config.
- Compute log filenames are now guaranteed not to exceed the POSIX limit of 255 chars.
- Fixes an issue when copying and pasting solid names from Dagit.
- Termination now works as expected in the multiprocessing executor.
- The multiprocessing executor now executes parallel steps in the expected order.
- The multiprocessing executor now correctly handles solid subsets.
- Fixed a bad error condition in `dagster_ssh.sftp_solid`.
- Fixed a bad error message giving incorrect log level suggestions.

**Documentation**

- Minor fixes and improvements.

**Thank you**
Thank you to all of the community contributors to this release!! In alphabetical order: @cclauss,
@deem0n, @irabinovitch, @pseudoPixels, @Ramshackle-Jamathon, @rparrapy, @yamrzou.

## 0.6.6

**Breaking**

- The `selector` argument to `PipelineDefinition` has been removed. This API made it possible to
  construct a `PipelineDefinition` in an invalid state. Use `PipelineDefinition.build_sub_pipeline`
  instead.

**New**

- Added the `dagster_prometheus` library, which exposes a basic Prometheus resource.
- Dagster Airflow DAGs may now use GCS instead of S3 for storage.
- Expanded interface for schedule management in Dagit.

**Dagit**

- Performance improvements when loading, displaying, and editing config for large pipelines.
- Smooth scrolling zoom in the explore tab replaces the previous two-step zoom.
- No longer depends on internet fonts to run, allowing fully offline dev.
- Typeahead behavior in search has improved.
- Invocations of composite solids remain visible in the sidebar when the solid is expanded.
- The config schema panel now appears when the config editor is first opened.
- Interface now includes hints for autocompletion in the config editor.
- Improved display of solid inputs and output in the explore tab.
- Provides visual feedback while filter results are loading.
- Better handling of pipelines that aren't present in the currently loaded repo.

**Bugfix**

- Dagster Airflow DAGs previously could crash while handling Python errors in DAG logic.
- Step failures when running Dagster Airflow DAGs were previously not being surfaced as task
  failures in Airflow.
- Dagit could previously get into an invalid state when switching pipelines in the context of a
  solid subselection.
- `frozenlist` and `frozendict` now pass Dagster's parameter type checks for `list` and `dict`.
- The GraphQL playground in Dagit is now working again.

**Nits**

- Dagit now prints its pid when it loads.
- Third-party dependencies have been relaxed to reduce the risk of version conflicts.
- Improvements to docs and example code.

## 0.6.5

**Breaking**

- The interface for type checks has changed. Previously the `type_check_fn` on a custom type was
  required to return None (=passed) or else raise `Failure` (=failed). Now, a `type_check_fn` may
  return `True`/`False` to indicate success/failure in the ordinary case, or else return a
  `TypeCheck`. The new`success` field on `TypeCheck` now indicates success/failure. This obviates
  the need for the `typecheck_metadata_fn`, which has been removed.
- Executions of individual composite solids (e.g. in test) now produce a
  `CompositeSolidExecutionResult` rather than a `SolidExecutionResult`.
- `dagster.core.storage.sqlite_run_storage.SqliteRunStorage` has moved to
  `dagster.core.storage.runs.SqliteRunStorage`. Any persisted `dagster.yaml` files should be updated
  with the new classpath.
- `is_secret` has been removed from `Field`. It was not being used to any effect.
- The `environmentType` and `configTypes` fields have been removed from the dagster-graphql
  `Pipeline` type. The `configDefinition` field on `SolidDefinition` has been renamed to
  `configField`.

**Bugfix**

- `PresetDefinition.from_files` is now guaranteed to give identical results across all Python
  minor versions.
- Nested composite solids with no config, but with config mapping functions, now behave as expected.
- The dagster-airflow `DagsterKubernetesPodOperator` has been fixed.
- Dagit is more robust to changes in repositories.
- Improvements to Dagit interface.

**New**

- dagster_pyspark now supports remote execution on EMR with the `@pyspark_solid` decorator.

**Nits**

- Documentation has been improved.
- The top level config field `features` in the `dagster.yaml` will no longer have any effect.
- Third-party dependencies have been relaxed to reduce the risk of version conflicts.

## 0.6.4

- Scheduler errors are now visible in Dagit
- Run termination button no longer persists past execution completion
- Fixes run termination for multiprocess execution
- Fixes run termination on Windows
- `dagit` no longer prematurely returns control to terminal on Windows
- `raise_on_error` is now available on the `execute_solid` test utility
- `check_dagster_type` added as a utility to help test type checks on custom types
- Improved support in the type system for `Set` and `Tuple` types
- Allow composite solids with config mapping to expose an empty config schema
- Simplified graphql API arguments to single-step re-execution to use `retryRunId`, `stepKeys`
  execution parameters instead of a `reexecutionConfig` input object
- Fixes missing step-level stdout/stderr from dagster CLI

## 0.6.3

- Adds a `type_check` parameter to `PythonObjectType`, `as_dagster_type`, and `@as_dagster_type` to
  enable custom type checks in place of default `isinstance` checks.
  See documentation here:
  https://dagster.readthedocs.io/en/latest/sections/learn/tutorial/types.html#custom-type-checks
- Improved the type inference experience by automatically wrapping bare python types as dagster
  types.
- Reworked our tutorial (now with more compelling/scary breakfast cereal examples) and public API
  documentation.
  See the new tutorial here:
  https://dagster.readthedocs.io/en/latest/sections/learn/tutorial/index.html
- New solids explorer in Dagit allows you to browse and search for solids used across the
  repository.

  ![Solid Explorer](./screenshots/solid_explorer.png)
  ![Solid Explorer](./screenshots/solid_explorer_input.png)

- Enabled solid dependency selection in the Dagit search filter.

  - To select a solid and its upstream dependencies, search `+{solid_name}`.
  - To select a solid and its downstream dependents, search `{solid_name}+`.
  - For both search `+{solid_name}+`.

  For example. In the Airline demo, searching `+join_q2_data` will get the following:

  ![Screenshot](./screenshots/airline_join_parent_filter.png)

- Added a terminate button in Dagit to terminate an active run.

  ![Stop Button](./screenshots/stop_button.png)

- Added an `--output` flag to `dagster-graphql` CLI.
- Added confirmation step for `dagster run wipe` and `dagster schedule wipe` commands (Thanks
  @shahvineet98).
- Fixed a wrong title in the `dagster-snowflake` library README (Thanks @Step2Web).

## 0.6.2

- Changed composition functions `@pipeline` and `@composite_solid` to automatically give solids
  aliases with an incrementing integer suffix when there are conflicts. This removes to the need
  to manually alias solid definitions that are used multiple times.
- Add `dagster schedule wipe` command to delete all schedules and remove all schedule cron jobs
- `execute_solid` test util now works on composite solids.
- Docs and example improvements: https://dagster.readthedocs.io/
- Added `--remote` flag to `dagster-graphql` for querying remote Dagit servers.
- Fixed issue with duplicate run tag autocomplete suggestions in Dagit (#1839)
- Fixed Windows 10 / py3.6+ bug causing pipeline execution failures

## 0.6.1

- Fixed an issue where Dagster public images tagged `latest` on Docker Hub were erroneously
  published with an older version of Dagster (#1814)
- Fixed an issue where the most recent scheduled run was not displayed in Dagit (#1815)
- Fixed a bug with the `dagster schedule start --start-all` command (#1812)
- Added a new scheduler command to restart a schedule: `dagster schedule restart`. Also added a
  flag to restart all running schedules: `dagster schedule restart --restart-all-running`.

## 0.6.0 "Impossible Princess"

**New**

This major release includes features for scheduling, operating, and executing pipelines
that elevate Dagit and dagster from a local development tool to a deployable service.

- `DagsterInstance` introduced as centralized system to control run, event, compute log,
  and local intermediates storage.
- A `Scheduler` abstraction has been introduced along side an initial implementation of
  `SystemCronScheduler` in `dagster-cron`.
- `dagster-aws` has been extended with a CLI for deploying dagster to AWS. This can spin
  up a Dagit node and all the supporting infrastructure—security group, RDS PostgreSQL
  instance, etc.—without having to touch the AWS console, and for deploying your code
  to that instance.
- **Dagit**
  - `Runs`: a completely overhauled Runs history page. Includes the ability to `Retry`,
    `Cancel`, and `Delete` pipeline runs from the new runs page.
  - `Scheduler`: a page for viewing and interacting with schedules.
  - `Compute Logs`: stdout and stderr are now viewable on a per execution step basis in each run.
    This is available in real time for currently executing runs and for historical runs.
  - A `Reload` button in the top right in Dagit restarts the web-server process and updates
    the UI to reflect repo changes, including DAG structure, solid names, type names, etc.
    This replaces the previous file system watching behavior.

**Breaking Changes**

- `--log` and `--log-dir` no longer supported as CLI args. Existing runs and events stored
  via these flags are no longer compatible with current storage.
- `raise_on_error` moved from in process executor config to argument to arguments in
  python API methods such as `execute_pipeline`

## 0.5.9

- Fixes an issue using custom types for fan-in dependencies with intermediate storage.

## 0.5.8

- Fixes an issue running some Dagstermill notebooks on Windows.
- Fixes a transitive dependency issue with Airflow.
- Bugfixes, performance improvements, and better documentation.

## 0.5.7

- Fixed an issue with specifying composite output mappings (#1674)
- Added support for specifying
  [Dask worker resources](https://distributed.dask.org/en/latest/resources.html) (#1679)
- Fixed an issue with launching Dagit on Windows

## 0.5.6

- Execution details are now configurable. The new top-level `ExecutorDefinition` and `@executor`
  APIs are used to define in-process, multiprocess, and Dask executors, and may be used by users to
  define new executors. Like loggers and storage, executors may be added to a `ModeDefinition` and
  may be selected and configured through the `execution` field in the environment dict or YAML,
  including through Dagit. Executors may no longer be configured through the `RunConfig`.
- The API of dagster-dask has changed. Pipelines are now executed on Dask using the
  ordinary `execute_pipeline` API, and the Dask executor is configured through the environment.
  (See the dagster-dask README for details.)
- Added the `PresetDefinition.from_files` API for constructing a preset from a list of environment
  files (replacing the old usage of this class). `PresetDefinition` may now be directly
  instantiated with an environment dict.
- Added a prototype integration with [dbt](https://www.getdbt.com/).
- Added a prototype integration with [Great Expectations](https://greatexpectations.io/).
- Added a prototype integration with [Papertrail](https://papertrailapp.com/).
- Added the dagster-bash library.
- Added the dagster-ssh library.
- Added the dagster-sftp library.
- Loosened the PyYAML compatibility requirement.
- The dagster CLI no longer takes a `--raise-on-error` or `--no-raise-on-error` flag. Set this
  option in executor config.
- Added a `MarkdownMetadataEntryData` class, so events yielded from client code may now render
  markdown in their metadata.
- Bug fixes, documentation improvements, and improvements to error display.

## 0.5.5

- Dagit now accepts parameters via environment variables prefixed with `DAGIT_`, e.g. `DAGIT_PORT`.
- Fixes an issue with reexecuting Dagstermill notebooks from Dagit.
- Bug fixes and display improvments in Dagit.

## 0.5.4

- Reworked the display of structured log information and system events in Dagit, including support
  for structured rendering of client-provided event metadata.
- Dagster now generates events when intermediates are written to filesystem and S3 storage, and
  these events are displayed in Dagit and exposed in the GraphQL API.
- Whitespace display styling in Dagit can now be toggled on and off.
- Bug fixes, display nits and improvements, and improvements to JS build process, including better
  display for some classes of errors in Dagit and improvements to the config editor in Dagit.

## 0.5.3

- Pinned RxPY to 1.6.1 to avoid breaking changes in 3.0.0 (py3-only).
- Most definition objects are now read-only, with getters corresponding to the previous properties.
- The `valueRepr` field has been removed from `ExecutionStepInputEvent` and
  `ExecutionStepOutputEvent`.
- Bug fixes and Dagit UX improvements, including SQL highlighting and error handling.

## 0.5.2

- Added top-level `define_python_dagster_type` function.
- Renamed `metadata_fn` to `typecheck_metadata_fn` in all runtime type creation APIs.
- Renamed `result_value` and `result_values` to `output_value` and `output_values` on
  `SolidExecutionResult`
- Dagstermill: Reworked public API now contains only `define_dagstermill_solid`, `get_context`,
  `yield_event`, `yield_result`, `DagstermillExecutionContext`, `DagstermillError`, and
  `DagstermillExecutionError`. Please see the new
  [guide](https://dagster.readthedocs.io/en/0.5.2/sections/learn/guides/data_science/data_science.html)
  for details.
- Bug fixes, including failures for some dagster CLI invocations and incorrect handling of Airflow
  timestamps.
