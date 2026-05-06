"""Test auto stow functionality on DishLeafNode."""

import pytest
from assertpy import assert_that
from pytest_bdd import given, scenario, then, when
from ska_integration_test_harness.facades import DishesFacade
from ska_integration_test_harness.facades.tmc_facade import TMCFacade
from ska_tango_testing.integration import TangoEventTracer

from tests.conftest import LOGGER
from tests.resources.test_harness.utils.enums import StowStatus
from tests.resources.test_support.common_utils.result_code import ResultCode
from tests.resources.test_support.constant import COMMAND_COMPLETED
from tests.resources.test_support.enum import DishMode
from tests.tmc_new_ITH.weather_sim import (
    simulate_temperature,
    simulate_windspeed,
)

ASSERTIONS_TIMEOUT = 60


@pytest.fixture
def test_state():
    """Fixture to store state between test steps."""
    return {"reset_temp": False}


def _setup_event_subscriptions(
    tmc: TMCFacade,
    event_tracer: TangoEventTracer,
):
    """Subscribe TMC and Dishes devices to track and log stowStatus events.

    :param tmc: the TMC facade.
    :param dishes: the Dishes facade.
    :param event_tracer: the event tracer.
    """
    dish_leaf_node = tmc.dish_leaf_node_list[0]
    event_tracer.subscribe_event(dish_leaf_node, "stowStatus")
    event_tracer.subscribe_event(dish_leaf_node, "dishMode")
    event_tracer.subscribe_event(dish_leaf_node, "longRunningCommandResult")


def _reset_stow_mode(dish_leaf_node, event_tracer: TangoEventTracer):
    """
    Resets the DishMode to StandbyFP.
    """
    if dish_leaf_node.stowStatus == StowStatus.STOW_STARTED:
        assert_that(event_tracer).within_timeout(
            ASSERTIONS_TIMEOUT
        ).has_change_event_occurred(
            dish_leaf_node, "stowstatus", StowStatus.STOW_COMPLETED
        )
    if dish_leaf_node.stowStatus == StowStatus.STOW_COMPLETED:
        result, unique_id = dish_leaf_node.SetStandbyLPMode()

        LOGGER.debug("Command id: %s | Returned result: %s", unique_id, result)
        assert result[0] == ResultCode.QUEUED

        assert_that(event_tracer).within_timeout(
            ASSERTIONS_TIMEOUT
        ).has_change_event_occurred(
            dish_leaf_node,
            "longRunningCommandResult",
            (unique_id[0], COMMAND_COMPLETED),
        )

        assert_that(event_tracer).within_timeout(
            ASSERTIONS_TIMEOUT
        ).has_change_event_occurred(
            dish_leaf_node, "dishMode", DishMode.STANDBY_LP
        )


@pytest.mark.batch2
@pytest.mark.SKA_mid
@scenario(
    "../tmc_new_ITH/features/auto_stow.feature",
    "Validate auto stow on gust speed",
)
def test_autostow_gust_speed(tmc: TMCFacade, event_tracer: TangoEventTracer):
    """Test that the dish automatically stows
    when gust speed exceeds threshold."""
    _setup_event_subscriptions(tmc, event_tracer)


@pytest.mark.batch2
@pytest.mark.SKA_mid
@scenario(
    "../tmc_new_ITH/features/auto_stow.feature",
    "Validate auto stow on mean wind speed exceed",
)
def test_autostow_mean_wind_speed(
    tmc: TMCFacade, event_tracer: TangoEventTracer
):
    """Test that the dish automatically stows
    when mean wind speed exceeds threshold."""
    _setup_event_subscriptions(tmc, event_tracer)


@pytest.mark.batch2
@pytest.mark.SKA_mid
@scenario(
    "../tmc_new_ITH/features/auto_stow.feature",
    "Validate auto stow on operational wind speed exceed",
)
def test_autostow_ops_wind_speed(
    tmc: TMCFacade, event_tracer: TangoEventTracer
):
    """Test that the dish automatically stows
    when operational wind speed exceeds threshold."""
    _setup_event_subscriptions(tmc, event_tracer)


@pytest.mark.batch2
@pytest.mark.SKA_mid
@scenario(
    "../tmc_new_ITH/features/auto_stow.feature",
    "Validate auto stow on operational wind speed exceed threshold percentage",
)
def test_autostow_ops_percentage_wind_speed(
    tmc: TMCFacade, event_tracer: TangoEventTracer
):
    """Test that the dish automatically stows
    when operational wind speed exceeds threshold percentage."""
    _setup_event_subscriptions(tmc, event_tracer)


@pytest.mark.batch2
@pytest.mark.SKA_mid
@scenario(
    "../tmc_new_ITH/features/auto_stow.feature",
    "Validate auto stow on max temp",
)
def test_autostow_max_temp(tmc: TMCFacade, event_tracer: TangoEventTracer):
    """Test that the dish automatically stows
    when max temp reached"""
    _setup_event_subscriptions(tmc, event_tracer)


@pytest.mark.batch2
@pytest.mark.SKA_mid
@scenario(
    "../tmc_new_ITH/features/auto_stow.feature",
    "Validate auto stow on max temp exceeds threshold for specific time",
)
def test_autostow_max_temp_threshold(
    tmc: TMCFacade, event_tracer: TangoEventTracer
):
    """Test that the dish automatically stows
    when max temp exceeds threshold for specific time"""
    _setup_event_subscriptions(tmc, event_tracer)


@given("a DishLeafNode device in STANDBY_LP mode")
def given_tmc_and_dishes(
    tmc: TMCFacade, dishes: DishesFacade, event_tracer: TangoEventTracer
):
    """Given TMC and Dishes facades."""
    LOGGER.info("Testing SetStowMode command on DishLeafNode")
    dish_leaf_node = tmc.dish_leaf_node_list[0]

    event_tracer.subscribe_event(dish_leaf_node, "dishMode")
    event_tracer.subscribe_event(dish_leaf_node, "longRunningCommandResult")

    result, unique_id = dish_leaf_node.SetStandbyLPMode()
    assert result[0] == ResultCode.QUEUED

    assert_that(event_tracer).within_timeout(
        ASSERTIONS_TIMEOUT
    ).has_change_event_occurred(
        dish_leaf_node, "dishMode", DishMode.STANDBY_LP
    )
    assert_that(event_tracer).within_timeout(
        ASSERTIONS_TIMEOUT
    ).has_change_event_occurred(
        dish_leaf_node,
        "longRunningCommandResult",
        (unique_id[0], COMMAND_COMPLETED),
    )


@when("the gust speed is greater than the max allowed gust speed")
def when_gust_speed_exceeds_threshold(
    tmc: TMCFacade, event_tracer: TangoEventTracer
):
    """When the gust speed is greater than the max allowed gust speed."""

    dish_leaf_node = tmc.dish_leaf_node_list[0]
    event_tracer.subscribe_event(dish_leaf_node, "stowStatus")

    dish_leaf_node.maxAllowedGustWindspeed = 22.0
    dish_leaf_node.gustWindspeedMeasurementTimeWindow = 4
    simulate_windspeed(22, 24, 15)


@when(
    "the mean wind speed over a measurement time window "
    "exceeds the configured maximum threshold"
)
def when_mean_wind_speed_exceeds_threshold(
    tmc: TMCFacade, event_tracer: TangoEventTracer
):
    """When the mean wind speed is greater than the max
    allowed mean wind speed."""
    dish_leaf_node = tmc.dish_leaf_node_list[0]
    event_tracer.subscribe_event(dish_leaf_node, "stowStatus")

    dish_leaf_node.maxAllowedWindspeed = 16.0
    dish_leaf_node.meanWindspeedMeasurementTimeWindow = 10.0
    simulate_windspeed(16, 18, 10)


@when(
    "the operational wind speed over a measurement time window exceeds "
    "the maximum allowed operational windspeed"
)
def when_operational_wind_speed_exceeds_threshold(
    tmc: TMCFacade, event_tracer: TangoEventTracer
):
    """When the operational wind speed is greater than the max
    allowed operational wind speed."""

    dish_leaf_node = tmc.dish_leaf_node_list[0]
    event_tracer.subscribe_event(dish_leaf_node, "stowStatus")

    dish_leaf_node.maxAllowedOpsWindspeed = 5.0
    dish_leaf_node.WindspeedMeasurementTimeWindow = 10.0
    simulate_windspeed(6, 7, 10)


@when(
    "the difference between operational wind speeds "
    "exceeds the configured percentage threshold"
)
def when_operational_wind_speed_exceeds_percentage_threshold(
    tmc: TMCFacade, event_tracer: TangoEventTracer
):
    """When the difference between operational wind speeds
    exceeds the configured percentage threshold."""
    dish_leaf_node = tmc.dish_leaf_node_list[0]
    event_tracer.subscribe_event(dish_leaf_node, "stowStatus")

    dish_leaf_node.maxAllowedWindspeedDifference = 5.0
    dish_leaf_node.maxAllowedOpsMeanWindspeedMeasurementTimeWindow = 10.0

    simulate_windspeed(10, 11, 3)
    simulate_windspeed(12, 13, 1)
    simulate_windspeed(20, 25, 1)


@when("the temperature exceeds the configured maximum temperature threshold")
def when_temperature_exceeds_max_threshold(
    tmc: TMCFacade, event_tracer: TangoEventTracer, test_state: dict
):
    """When the temperature exceeds the configured
    maximum temperature threshold."""
    dish_leaf_node = tmc.dish_leaf_node_list[0]
    event_tracer.subscribe_event(dish_leaf_node, "stowStatus")

    dish_leaf_node.maxTemperatureThreshold = 35
    simulate_temperature(35, 36, 2)
    test_state["reset_temp"] = True


@when(
    "the temperature change over a specified time window "
    "exceeds the configured threshold"
)
def when_temperature_exceeds_max_threshold_for_duration(
    tmc: TMCFacade, event_tracer: TangoEventTracer, test_state: dict
):
    """When the temperature exceeds the configured maximum
    temperature threshold for a specific duration."""
    dish_leaf_node = tmc.dish_leaf_node_list[0]
    event_tracer.subscribe_event(dish_leaf_node, "stowStatus")

    dish_leaf_node.timeDelta = 10.0
    dish_leaf_node.temperatureDelta = 20.0

    simulate_temperature(10, 11, 2)
    simulate_temperature(15, 20, 2)
    simulate_temperature(31, 35, 6)
    test_state["reset_temp"] = True


@then("the dish automatically stows")
def then_dish_automatically_stows(
    tmc: TMCFacade, event_tracer: TangoEventTracer, test_state: dict
):
    """Then the dish automatically stows."""
    assert_that(event_tracer).within_timeout(
        ASSERTIONS_TIMEOUT
    ).has_change_event_occurred(
        tmc.dish_leaf_node_list[0], "stowStatus", StowStatus.STOW_STARTED
    )
    assert_that(event_tracer).within_timeout(
        ASSERTIONS_TIMEOUT
    ).has_change_event_occurred(
        tmc.dish_leaf_node_list[0], "stowStatus", StowStatus.STOW_COMPLETED
    )
    if test_state.get("reset_temp", True):
        tmc.dish_leaf_node_list[0].set_timeout_millis(5000)
        tmc.dish_leaf_node_list[0].temperatureDelta = 100.0
        tmc.dish_leaf_node_list[0].maxTemperatureThreshold = 100.0
        tmc.dish_leaf_node_list[0].minTemperatureThreshold = -100.0
        tmc.dish_leaf_node_list[0].timeDelta = 1000.0
        test_state["reset_temp"] = False
    _reset_stow_mode(tmc.dish_leaf_node_list[0], event_tracer)
