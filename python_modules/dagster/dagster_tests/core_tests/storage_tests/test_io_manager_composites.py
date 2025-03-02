import pytest
from dagster import (
    DagsterInvalidDefinitionError,
    InputDefinition,
    ModeDefinition,
    OutputDefinition,
    composite_solid,
    execute_pipeline,
    pipeline,
    solid,
)
from dagster.core.storage.io_manager import IOManager, io_manager


def named_io_manager(storage_dict, name):
    @io_manager
    def my_io_manager(_):
        class MyIOManager(IOManager):
            def handle_output(self, context, obj):
                storage_dict[tuple(context.get_run_scoped_output_identifier())] = {
                    "value": obj,
                    "output_manager_name": name,
                }

            def load_input(self, context):
                result = storage_dict[
                    tuple(context.upstream_output.get_run_scoped_output_identifier())
                ]
                return {**result, "input_manager_name": name}

        return MyIOManager()

    return my_io_manager


def test_composite_solid_output():
    @solid(output_defs=[OutputDefinition(io_manager_key="inner_manager")])
    def my_solid(_):
        return 5

    @solid(
        input_defs=[InputDefinition("x")],
        output_defs=[OutputDefinition(io_manager_key="inner_manager")],
    )
    def my_solid_takes_input(_, x):
        return x

    # Error on io_manager_key on composite
    with pytest.raises(
        DagsterInvalidDefinitionError, match="IO manager cannot be set on a composite solid"
    ):

        @composite_solid(output_defs=[OutputDefinition(io_manager_key="outer_manager")])
        def _():
            return my_solid_takes_input(my_solid())

    # Values ingested by inner_manager and outer_manager are stored in storage_dict
    storage_dict = {}

    # Only use the io managers on inner solids for handling inputs and storing outputs.

    @composite_solid
    def my_composite():
        return my_solid_takes_input(my_solid())

    @pipeline(
        mode_defs=[
            ModeDefinition(
                resource_defs={"inner_manager": named_io_manager(storage_dict, "inner")},
            )
        ]
    )
    def my_pipeline():
        my_composite()

    result = execute_pipeline(my_pipeline)
    assert result.success
    # Ensure that the IO manager used to store and load my_composite.my_solid_takes_input is the
    # manager of my_solid_takes_input, not my_composite.
    assert storage_dict[(result.run_id, "my_composite.my_solid_takes_input", "result")][
        "value"
    ] == {
        "value": 5,
        "output_manager_name": "inner",
        "input_manager_name": "inner",
    }


def test_composite_solid_upstream_output():
    # Only use the io managers on inner solids for loading downstream inputs.

    @solid(output_defs=[OutputDefinition(io_manager_key="inner_manager")])
    def my_solid(_):
        return 5

    @composite_solid
    def my_composite():
        return my_solid()

    @solid
    def downstream_solid(_, input1):
        assert input1 == {
            "value": 5,
            "output_manager_name": "inner",
            "input_manager_name": "inner",
        }

    storage_dict = {}

    @pipeline(
        mode_defs=[
            ModeDefinition(resource_defs={"inner_manager": named_io_manager(storage_dict, "inner")})
        ]
    )
    def my_pipeline():
        downstream_solid(my_composite())

    result = execute_pipeline(my_pipeline)
    assert result.success


def test_io_manager_config_inside_composite():
    stored_dict = {}

    @io_manager(output_config_schema={"output_suffix": str})
    def inner_manager(_):
        class MyHardcodedIOManager(IOManager):
            def handle_output(self, context, obj):
                keys = tuple(
                    context.get_run_scoped_output_identifier() + [context.config["output_suffix"]]
                )
                stored_dict[keys] = obj

            def load_input(self, context):
                keys = tuple(
                    context.upstream_output.get_run_scoped_output_identifier()
                    + [context.upstream_output.config["output_suffix"]]
                )
                return stored_dict[keys]

        return MyHardcodedIOManager()

    @solid(output_defs=[OutputDefinition(io_manager_key="inner_manager")])
    def my_solid(_):
        return "hello"

    @solid
    def my_solid_takes_input(_, x):
        assert x == "hello"
        return x

    @composite_solid
    def my_composite_solid():
        return my_solid_takes_input(my_solid())

    @pipeline(
        mode_defs=[ModeDefinition(name="default", resource_defs={"inner_manager": inner_manager})]
    )
    def my_pipeline():
        my_composite_solid()

    result = execute_pipeline(
        my_pipeline,
        run_config={
            "solids": {
                "my_composite_solid": {
                    "solids": {"my_solid": {"outputs": {"result": {"output_suffix": "my_suffix"}}}},
                }
            }
        },
    )
    assert result.success
    assert result.output_for_solid("my_composite_solid.my_solid") == "hello"
    assert (
        stored_dict.get((result.run_id, "my_composite_solid.my_solid", "result", "my_suffix"))
        == "hello"
    )
