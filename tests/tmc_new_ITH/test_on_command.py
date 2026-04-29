"""
Test ON Command when at least one dish is available in STANDBY_FP
"""


import json

import pytest
from assertpy import assert_that
from pytest_bdd import given, parsers, scenario, then, when
from ska_control_model import ResultCode
from ska_integration_test_harness.facades import DishesFacade, TMCFacade
from ska_tango_testing.integration import TangoEventTracer, log_events
from tango import DevState

from tests.resources.test_support.constant import TIMEOUT
from tests.resources.test_support.enum import DishMode


@pytest.mark.batch1
@pytest.mark.SKA_mid
@scenario(
    "../features/test_on.feature",
    "Central Node ON command succeeds when at least one "
    "dish is available (in STANDBY_FP)",
)
def test_on_command():
    """BDD scenario for verifying On Command"""


@given("A TMC")
def given_tmc(
    tmc: TMCFacade,
    dishes: DishesFacade,
    event_tracer: TangoEventTracer,
):
    """Given a TMC"""
    event_tracer.subscribe_event(tmc.central_node, "telescopeState")
    event_tracer.subscribe_event(tmc.central_node, "longRunningCommandResult")
    for dish_manager in dishes.dish_master_list:
        event_tracer.subscribe_event(dish_manager, "State")
    for leaf_node in tmc.dish_leaf_node_list:
        event_tracer.subscribe_event(leaf_node, "State")
    log_events(
        {
            tmc.central_node: ["telescopeState", "longRunningCommandResult"],
            **{leaf_node: ["State"] for leaf_node in tmc.dish_leaf_node_list},
            **{
                dish_manager: ["State"]
                for dish_manager in dishes.dish_master_list
            },
        }
    )


@when("I invoke the ON command on the Central Node")
def when_tmc_on(tmc: TMCFacade):
    """
    Ensure that the TMC and ResourceMonitor devices are available and ON.
    """
    _, pytest.unique_id = tmc.central_node.TelescopeOn()


@when(
    parsers.parse(
        "dishes SKA001, SKA036, SKA063, SKA100 are in"
        " dish mode {DishModeSKA001}, {DishModeSKA036}, "
        "{DishModeSKA063}, {DishModeSKA100} respectively"
    )
)
def when_dishes_in_dish_mode(
    dishes: DishesFacade,
    DishModeSKA001: DishMode,
    DishModeSKA036: DishMode,
    DishModeSKA063: DishMode,
    DishModeSKA100: DishMode,
):
    """
    Ensure that the dishes are in the specified dish mode.
    """

    for dish_id, dish_mode in zip(
        ["dish_001", "dish_036", "dish_063", "dish_100"],
        [
            DishModeSKA001,
            DishModeSKA036,
            DishModeSKA063,
            DishModeSKA100,
        ],
    ):
        dish = dishes.dish_master_dict[dish_id]
        dish_mode_enum = DishMode(dish_mode)
        dish.SetDirectDishMode(dish_mode_enum)


@then("telescopeState is in DevState.ON")
def then_central_node_on(event_tracer: TangoEventTracer, tmc: TMCFacade):
    """Then the Central Node should be in ON state."""

    assert_that(event_tracer).described_as(
        "Expected telescopeState event with DevState.ON"
    ).within_timeout(TIMEOUT).has_change_event_occurred(
        tmc.central_node, "TelescopeState", DevState.ON
    )


@then("The ON command is successful")
def then_on_command_successful(event_tracer: TangoEventTracer, tmc: TMCFacade):
    """Then the ON command should be successful."""

    assert_that(event_tracer).described_as(
        "Expected longRunningCommandResult event with ON command success"
    ).within_timeout(TIMEOUT).has_change_event_occurred(
        tmc.central_node,
        "longRunningCommandResult",
        (
            pytest.unique_id[0],
            json.dumps((int(ResultCode.OK), "Command Completed")),
        ),
    )
