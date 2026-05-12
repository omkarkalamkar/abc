"""Test module to test the SetStowMode command functionality"""

import json
import logging
import re

import pytest
from assertpy import assert_that
from pytest_bdd import given, parsers, scenario, then, when
from ska_control_model import ObsState
from ska_integration_test_harness.facades import DishesFacade
from ska_integration_test_harness.facades.tmc_facade import TMCFacade
from ska_integration_test_harness.inputs.test_harness_inputs import (
    TestHarnessInputs,
)
from ska_tango_testing.integration import TangoEventTracer, log_events
from ska_tango_testing.mock.placeholders import Anything

from tests.resources.test_harness.utils.enums import ResultCode
from tests.resources.test_support.constant import (
    ERROR_PROPAGATION_DEFECT,
    RESET_DEFECT,
)
from tests.resources.test_support.enum import DishMode
from tests.tmc_csp_new_ITH.conftest import CN_ASSERTIONS_TIMEOUT

logger = logging.getLogger(__name__)


@pytest.mark.stowmode
@pytest.mark.SKA_mid
@scenario(
    "../tmc_new_ITH/features/xtp_101450_manual_stow_functionality.feature",
    "TMC processes SetStowMode command and reports status per dish",
)
def test_verify_tmc_stow_mode_command_functionality():
    """Test TMC can apply and report Stow mode for given dishes"""


@given("a TMC Mid telescope is operational")
def given_a_tmc(
    tmc: TMCFacade,
    dishes: DishesFacade,
    event_tracer: TangoEventTracer,
    default_commands_inputs: TestHarnessInputs,
):
    """Given a TMC"""

    logger.info("Given a TMC")
    event_tracer.clear_events()
    event_tracer.subscribe_event(tmc.central_node, "longRunningCommandResult")
    log_events(
        {
            tmc.central_node: [
                "longRunningCommandResult",
            ],
        }
    )
    tmc.move_to_on(wait_termination=True, is_long_running_command=True)
    # Setup TMC for testing different scenarios
    # before invoking SetStowMode command on TMC
    tmc.force_change_of_obs_state(
        ObsState.READY,
        default_commands_inputs,
        wait_termination=True,
    )

    # Set Stow mode on dish SKA036 dish
    dish_36 = dishes.dish_master_dict["dish_036"]
    dish_36.SetDirectDishMode(DishMode.STOW)

    # Set SKA077 defective
    dish_77 = dishes.dish_master_dict["dish_077"]
    dish_77.SetDefective(ERROR_PROPAGATION_DEFECT)


# Parse table rows by splitting on '|' to extract Dish_ID
@given(
    parsers.parse(
        "the following dish ids are provided as input to the"
        " SetStowMode command:\n{table_data}"
    )
)
def get_dish_ids(table_data):
    """
    Parses the raw table string into a clean list of IDs.
    """
    # Split lines, strip whitespace, and filter out header/empty lines
    lines = [line.strip() for line in table_data.split("\n") if line.strip()]
    # Extract values between pipes, ignoring the 'Dish_ID' header
    pytest.dish_ids = [
        item.strip("|").strip() for item in lines if "Dish_ID" not in item
    ]


@when("the SetStowMode command is invoked via TMC")
def apply_set_stow_mode_to_dishes(tmc: TMCFacade):
    """TMC innvokes SetStowMode on given list of dishes"""

    message, pytest.unique_id = tmc.central_node.SetStowMode(
        json.dumps(pytest.dish_ids)
    )
    logger.info("Command ID: %s Message: %s", pytest.unique_id, message)


@then(
    parsers.parse(
        "TMC reports the status as below for the respective"
        " dish id:\n{table_data}"
    )
)
def check_tmc_status(
    table_data,
    tmc: TMCFacade,
    event_tracer: TangoEventTracer,
    dishes: DishesFacade,
    default_commands_inputs: TestHarnessInputs,
):
    """Validate the SetStowMode command output"""
    lines = [line.strip() for line in table_data.strip().split("\n")]
    rows = [
        [cell.strip() for cell in line.split("|") if cell.strip()]
        for line in lines
    ]
    dish_status_map = {row[0]: row[1] for row in rows[1:]}
    print(f"Mapped Data: {dish_status_map}")

    logger.info("SetStowMode data for validation %s", dish_status_map)
    (
        assert_that(event_tracer)
        .described_as(
            'FAILED ASSUMPTION IN "THEN" STEP: '
            "TMC Central Node device "
            f"({tmc.central_node.dev_name()}) "
            "is expected have longRunningCommandResult as "
            "(unique_id, COMMAND_RESULT)",
        )
        .within_timeout(CN_ASSERTIONS_TIMEOUT + 1)
        .has_change_event_occurred(
            tmc.central_node,
            "longRunningCommandResult",
            (pytest.unique_id[0], Anything),
        )
    )

    # Validate Dish modes on dish leaf nodes
    validate_dish_mode_set_to_stow(tmc, event_tracer, dish_status_map)

    # Validate CN LRCR
    validate_stow_mode_failure_details(event_tracer, dish_status_map)

    # Restore the data for next test case execution
    dishes.dish_master_dict["dish_077"].SetDefective(RESET_DEFECT)
    tmc.force_change_of_obs_state(
        ObsState.EMPTY,
        default_commands_inputs,
        wait_termination=True,
    )
    event_tracer.clear_events()


@when('the SetStowMode command is invoked with "ALL" as an input')
def apply_set_stow_mode_to_all_dishes(
    tmc: TMCFacade, event_tracer: TangoEventTracer
):
    """TMC innvokes SetStowMode on all dishes"""
    event_tracer.subscribe_event(tmc.central_node, "longRunningCommandResult")
    message, pytest.unique_id = tmc.central_node.SetStowMode(
        json.dumps(["ALL"])
    )
    logger.info("Command ID: %s Message: %s", pytest.unique_id, message)


@then("TMC invokes SetStowMode on all the dishes")
def check_tmc_stow_mode_on_all_dishes(
    tmc: TMCFacade,
    event_tracer: TangoEventTracer,
    dishes: DishesFacade,
):
    """Validate the SetStowMode command output"""
    (
        assert_that(event_tracer)
        .described_as(
            'FAILED ASSUMPTION IN "THEN" STEP: '
            "TMC Central Node device "
            f"({tmc.central_node.dev_name()}) "
            "is expected have longRunningCommandResult as "
            "(unique_id, COMMAND_RESULT)",
        )
        .within_timeout(CN_ASSERTIONS_TIMEOUT + 1)
        .has_change_event_occurred(
            tmc.central_node,
            "longRunningCommandResult",
            (pytest.unique_id[0], Anything),
        )
    )
    validate_stow_mode_success_details(event_tracer)

    # Restore dish modes for next test cases
    dish_36 = dishes.dish_master_dict["dish_036"]
    dish_36.SetDirectDishMode(DishMode.STANDBY_LP)
    dish_77 = dishes.dish_master_dict["dish_077"]
    dish_77.SetDirectDishMode(DishMode.STANDBY_LP)
    dish_100 = dishes.dish_master_dict["dish_100"]
    dish_100.SetDirectDishMode(DishMode.STANDBY_LP)
    dish_001 = dishes.dish_master_dict["dish_001"]
    dish_001.SetDirectDishMode(DishMode.STANDBY_LP)
    assert dish_001.dishmode == DishMode.STANDBY_LP
    assert dish_100.dishmode == DishMode.STANDBY_LP
    assert dish_36.dishmode == DishMode.STANDBY_LP
    assert dish_77.dishmode == DishMode.STANDBY_LP
    event_tracer.clear_events()


def validate_dish_mode_set_to_stow(
    tmc: TMCFacade,
    event_tracer: TangoEventTracer,
    dish_status_map: dict,
):
    """Validate Dish mode is set to STOW."""

    stowed_dishes = [
        dish_id
        for dish_id, status in dish_status_map.items()
        if status == "DishMode set to Stow"
    ]
    for dish_id in stowed_dishes:
        dln_proxy = next(
            proxy
            for proxy in tmc.dish_leaf_node_list
            if proxy.name().lower().endswith(dish_id.lower())
        )
        assert dln_proxy.dishmode == DishMode.STOW

    # Assert DLN SKA077 dish mode not stow due to error propogation set
    assert tmc.dish_leaf_node_list[3] != DishMode.STOW


def validate_stow_mode_failure_details(events_tracer, dish_status_map):
    """Extracts parsed failure details from first failed SetStowMode
    command."""

    event_data = None
    for event in events_tracer.events:
        if isinstance(event.attribute_value, tuple):
            if "SetStowMode" in event.attribute_value[0]:
                event_data = json.loads(event.attribute_value[1])
                if event_data[0] == int(ResultCode.FAILED):
                    break

    logger.info("SetStowMode event data %s", event_data[1])
    assert "SetStowMode failed" in event_data[1]
    error_str = event_data[1]
    json_part = error_str.split(": ", 1)[1]
    match = re.search(r"\{.*\}", json_part)
    dict_str = match.group(0)
    data = json.loads(dict_str)
    err_msg1 = dish_status_map["ska077"]
    err_msg2 = dish_status_map["ska064"]
    assert err_msg1 in data["ska077"]["result_code"][1]
    assert err_msg2 in data["ska064"]


def validate_stow_mode_success_details(events_tracer):
    """Extracts parsed failure details from first failed SetStowMode
    command."""

    event_data = None
    for event in events_tracer.events:
        if isinstance(event.attribute_value, tuple):
            if "SetStowMode" in event.attribute_value[0]:
                event_data = json.loads(event.attribute_value[1])
                if event_data[0] == int(ResultCode.OK):
                    break

    assert "SetStowMode succeeded" in event_data[1]
    assert int(ResultCode.OK) == event_data[0]
    assert "ska001" in event_data[1]
    assert "ska036" in event_data[1]
    assert "ska077" in event_data[1]
    assert "ska100" in event_data[1]
