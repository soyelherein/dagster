import datetime

import pytest
from dagster import (
    DagsterInstance,
    DagsterInvariantViolationError,
    build_schedule_context,
    daily_schedule,
    schedule,
)
from dagster.core.errors import DagsterInvalidInvocationError
from dagster.core.test_utils import instance_for_test


def cron_test_schedule_factory():
    @schedule(cron_schedule="* * * * *", pipeline_name="no_pipeline")
    def basic_schedule(_):
        return {}

    return basic_schedule


def test_cron_schedule_invocation_all_args():
    basic_schedule = cron_test_schedule_factory()

    assert basic_schedule(None) == {}
    assert basic_schedule(build_schedule_context()) == {}
    assert basic_schedule(_=None) == {}
    assert basic_schedule(_=build_schedule_context()) == {}


def test_incorrect_cron_schedule_invocation():
    basic_schedule = cron_test_schedule_factory()

    with pytest.raises(
        DagsterInvalidInvocationError,
        match="Schedule decorated function has context argument, but no context argument was "
        "provided.",
    ):
        basic_schedule()  # pylint: disable=no-value-for-parameter

    with pytest.raises(
        DagsterInvalidInvocationError,
        match="Schedule invocation expected argument '_'.",
    ):
        basic_schedule(foo=None)  # pylint: disable=no-value-for-parameter,unexpected-keyword-arg


def partition_schedule_factory():
    @daily_schedule(
        pipeline_name="test_pipeline",
        start_date=datetime.datetime(2020, 1, 1),
    )
    def my_partition_schedule(date):
        assert isinstance(date, datetime.datetime)
        return {}

    return my_partition_schedule


def test_partition_schedule_invocation_all_args():
    my_partition_schedule = partition_schedule_factory()
    test_date = datetime.datetime(2020, 1, 1)
    assert my_partition_schedule(test_date) == {}
    assert my_partition_schedule(date=test_date) == {}


def test_incorrect_partition_schedule_invocation():
    my_partition_schedule = partition_schedule_factory()
    with pytest.raises(
        DagsterInvalidInvocationError,
        match="Schedule decorated function has date argument, but no date argument was provided.",
    ):
        my_partition_schedule()  # pylint: disable=no-value-for-parameter

    with pytest.raises(
        DagsterInvalidInvocationError,
        match="Schedule invocation expected argument 'date'.",
    ):
        my_partition_schedule(  # pylint: disable=no-value-for-parameter,unexpected-keyword-arg
            foo=None
        )


def test_instance_access():
    with pytest.raises(
        DagsterInvariantViolationError,
        match="Attempted to initialize dagster instance, but no instance reference was provided.",
    ):
        build_schedule_context().instance  # pylint: disable=expression-not-assigned

    with instance_for_test() as instance:
        assert isinstance(build_schedule_context(instance).instance, DagsterInstance)
