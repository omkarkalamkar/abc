"""
Test to validate TMC perform mattieu pattern configure functionality
"""
import pytest
from assertpy import assert_that
from pytest_bdd import given, parsers, scenario, then, when
from ska_tango_base.control_model import ObsState
from ska_tango_testing.integration import TangoEventTracer, log_events
from tango import DevState

from tests.resources.test_harness.central_node_mid import CentralNodeWrapperMid
from tests.resources.test_harness.helpers import (
    prepare_json_args_for_centralnode_commands,
    prepare_json_args_for_commands,
)
from tests.resources.test_harness.subarray_node import SubarrayNodeWrapper
from tests.resources.test_harness.utils.common_utils import JsonFactory
from tests.resources.test_support.constant import COMMAND_COMPLETED


@pytest.mark.batch2
@pytest.mark.SKA_mid
@scenario(
    "../tmc_new_ITH/features/xtp_106734_pvt_pattern.feature",
    "Test Configure command to verify Mattieu Pattern",
)
def test_pvt_pattern_configure_functionality():
    """
    Test TMC perform pvt pattern configure functionality
    """


@given("the TMC is On")
def given_tmc(
    event_tracer: TangoEventTracer, central_node_mid: CentralNodeWrapperMid
):
    """
    Method to check TMC is in ON telescopeState
    """
    event_tracer.subscribe_event(
        central_node_mid.central_node, "telescopeState"
    )
    event_tracer.subscribe_event(central_node_mid.subarray_node, "obsState")
    central_node_mid.move_to_on()
    log_events(
        {
            central_node_mid.central_node: ["telescopeState"],
            central_node_mid.subarray_node: ["obsState"],
        }
    )
    assert_that(event_tracer).described_as(
        'FAILED ASSUMPTION IN "GIVEN" STEP: '
        "'the TMC is On'"
        "TMC Central Node device"
        f"({central_node_mid.central_node.dev_name()}) "
        "is expected to be in ON telescope state",
    ).within_timeout(150).has_change_event_occurred(
        central_node_mid.central_node,
        "telescopeState",
        DevState.ON,
    )
    assert_that(event_tracer).described_as(
        'FAILED ASSUMPTION IN "GIVEN" STEP: '
        "'the TMC is On'"
        "TMC Subarray device"
        f"({central_node_mid.subarray_node.dev_name()}) "
        "is expected to be in EMPTY obstate",
    ).within_timeout(100).has_change_event_occurred(
        central_node_mid.subarray_node,
        "obsState",
        ObsState.EMPTY,
    )

    event_tracer.clear_events()


@given("the subarray is in IDLE obsState")
def given_subarray_in_idle(
    command_input_factory: JsonFactory,
    event_tracer: TangoEventTracer,
    central_node_mid: CentralNodeWrapperMid,
):
    """
    Method to check subarray is in IDLE obsState

    Args:
        command_input_factory: fixture for creating input required
        for command
        event_recorder: Fixture for EventRecorder class
        central_node_mid: Fixture for a TMC CentralNode wrapper class
    """

    assign_input_json = prepare_json_args_for_centralnode_commands(
        "assign_resources_mid", command_input_factory
    )

    _, unique_id = central_node_mid.store_resources(assign_input_json)

    event_tracer.subscribe_event(
        central_node_mid.central_node, "longRunningCommandResult"
    )
    log_events({central_node_mid.central_node: ["longRunningCommandResult"]})
    assert_that(event_tracer).described_as(
        'FAILED ASSUMPTION IN "GIVEN" STEP: '
        "'the subarray must be in the IDLE obsState'"
        "TMC Subarray device"
        f"({central_node_mid.subarray_node.dev_name()}) "
        "is expected to be in IDLE obstate",
    ).within_timeout(60).has_change_event_occurred(
        central_node_mid.subarray_node,
        "obsState",
        ObsState.IDLE,
    )

    assert_that(event_tracer).described_as(
        'FAILED ASSUMPTION IN "GIVEN" STEP: '
        "'the subarray is in IDLE obsState'"
        "TMC Central Node device"
        f"({central_node_mid.central_node.dev_name()}) "
        "is expected have longRunningCommand as"
        '(unique_id,(ResultCode.OK,"Command Completed"))',
    ).within_timeout(60).has_change_event_occurred(
        central_node_mid.central_node,
        "longRunningCommandResult",
        (unique_id[0], COMMAND_COMPLETED),
    )


@when(
    parsers.parse(
        "the command configure is issued with position velocity {input_json1}"
    )
)
def invoke_configure(
    subarray_node: SubarrayNodeWrapper,
    command_input_factory: JsonFactory,
    event_tracer: TangoEventTracer,
    input_json1: str,
):
    """
    Invoke Configure command with position velocity input json

    Args:
        subarray_node: Fixture for a Subarray Node wrapper class
        command_input_factory: fixture for creating input required
        for command
        event_recorder: Fixture for EventRecorder class
        central_node_mid: Fixture for a TMC CentralNode wrapper class
        subarray_id (str): Subarray ID
        dish_ids (str): Comma-separated IDs of DISH components.
    """
    event_tracer.subscribe_event(
        subarray_node.subarray_node, "longRunningCommandResult"
    )
    log_events({subarray_node.subarray_node: ["longRunningCommandResult"]})
    configure_input_json = prepare_json_args_for_commands(
        input_json1, command_input_factory
    )

    _, unique_id = subarray_node.execute_transition(
        "Configure", configure_input_json
    )
    assert_that(event_tracer).described_as(
        'FAILED ASSUMPTION IN "WHEN" STEP: '
        "TMC Subarray Node device"
        f"({subarray_node.subarray_node.dev_name()}) "
        "is expected have longRunningCommand as"
        '(unique_id,(ResultCode.OK,"Command Completed"))',
    ).within_timeout(60).has_change_event_occurred(
        subarray_node.subarray_node,
        "longRunningCommandResult",
        (unique_id[0], COMMAND_COMPLETED),
    )


@then("the subarray transitions to obsState READY")
def check_for_ready(
    event_tracer: TangoEventTracer,
    subarray_node: SubarrayNodeWrapper,
):
    """
    Method to check subarray is in READY obsState
    """
    assert_that(event_tracer).described_as(
        'FAILED ASSUMPTION IN "GIVEN" STEP: '
        "'the subarray must be in the READY obsState'"
        "TMC Subarray device"
        f"({subarray_node.subarray_node.dev_name()}) "
        "is expected to be in READY obstate",
    ).within_timeout(60).has_change_event_occurred(
        subarray_node.subarray_node,
        "obsState",
        ObsState.READY,
    )
    event_tracer.clear_events()


@then("TMC is able to generate track table entries")
def check_for_track_table_entries(
    central_node_mid: CentralNodeWrapperMid,
):
    """
    Method to check dish leaf node is able to generate track table entries
    """
    for dish_id in ["SKA001", "SKA063", "SKA100", "SKA036"]:
        programTrackTable = central_node_mid.get_track_table_for_dish_id(
            dish_id
        )
        assert (
            len(programTrackTable) == 15
        ), f"Expected 15 track table entries for {dish_id} dish"
