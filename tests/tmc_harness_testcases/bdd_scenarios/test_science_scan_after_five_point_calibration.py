"""Testing the Science Scan after a five point calibration scan"""
import json

import pytest
from assertpy import assert_that
from pytest_bdd import given, scenario, then, when
from ska_control_model import ObsState
from ska_tango_testing.integration import TangoEventTracer, log_events
from tango import DevState

from tests.resources.test_harness.central_node_mid import CentralNodeWrapperMid
from tests.resources.test_harness.helpers import (
    check_subarray_obs_state,
    prepare_json_args_for_centralnode_commands,
    prepare_json_args_for_commands,
    wait_and_validate_device_attribute_value,
)
from tests.resources.test_harness.subarray_node import SubarrayNodeWrapper
from tests.resources.test_harness.utils.common_utils import JsonFactory
from tests.resources.test_harness.utils.enums import SimulatorDeviceType
from tests.resources.test_support.constant import (
    COMMAND_COMPLETED,
    DISH_001_CALIBRATION_DATA,
    DISH_036_CALIBRATION_DATA,
)

# Assertion timeouts
TIMEOUT = 110


@pytest.mark.batch1
@pytest.mark.SKA_mid
@scenario(
    "../features/test_harness/science_scan_after_calibration_scan.feature",
    "TMC implements five point calibration scan: TMC executes Science scan "
    + "after calibration successfully.",
)
def test_science_scan_after_five_point_calibration_scan():
    """
    Test case to verify the Science scan functionality after a five point
    calibration scan on TMC
    """


@given("a TMC")
def given_tmc(
    central_node_mid: CentralNodeWrapperMid,
    subarray_node: SubarrayNodeWrapper,
    event_tracer: TangoEventTracer,
):
    """Given a TMC"""
    # Setting up subscriptions
    event_tracer.subscribe_event(
        central_node_mid.central_node, "telescopeState"
    )
    event_tracer.subscribe_event(
        central_node_mid.central_node, "longRunningCommandResult"
    )
    event_tracer.subscribe_event(subarray_node.subarray_node, "obsState")
    event_tracer.subscribe_event(
        subarray_node.subarray_node, "longRunningCommandResult"
    )

    # Logging setup
    log_events(
        {
            central_node_mid.central_node: [
                "telescopeState",
                "longRunningCommandResult",
            ],
            subarray_node.subarray_node: [
                "obsState",
                "longRunningCommandResult",
            ],
        }
    )

    for dish_master in subarray_node.dish_master_list:
        event_tracer.subscribe_event(dish_master, "dishMode")

    # TelescopeOn
    central_node_mid.move_to_on()

    # Assertions
    assert_that(event_tracer).described_as(
        "FAILED ASSUMPTION AFTER ON COMMAND: "
        "Central Node device"
        f"({central_node_mid.central_node.dev_name()}) "
        "is expected to be in TelescopeState ON",
    ).within_timeout(TIMEOUT).has_change_event_occurred(
        central_node_mid.central_node,
        "telescopeState",
        DevState.ON,
    )
    assert_that(event_tracer).described_as(
        "FAILED UNEXPECTED INITIAL OBSSTATE: "
        "Subarray Node device"
        f"({central_node_mid.subarray_node.dev_name()}) "
        "is expected to be in EMPTY obstate",
    ).within_timeout(TIMEOUT).has_change_event_occurred(
        central_node_mid.subarray_node,
        "obsState",
        ObsState.EMPTY,
    )
    event_tracer.clear_events()


@when("five point calibration scan performed on given subarray")
def a_subarray_after_five_point_calibration(
    central_node_mid: CentralNodeWrapperMid,
    subarray_node: SubarrayNodeWrapper,
    event_tracer: TangoEventTracer,
    simulator_factory,
    command_input_factory: JsonFactory,
):
    """Given a Subarray after the five point Calibration scan."""
    sdp_sim = simulator_factory.get_or_create_simulator_device(
        SimulatorDeviceType.MID_SDP_DEVICE
    )
    # AssignResources
    assign_input_json = prepare_json_args_for_centralnode_commands(
        "assign_resources_mid", command_input_factory
    )
    _, unique_id = central_node_mid.store_resources(assign_input_json)
    assert_that(event_tracer).described_as(
        "FAILED ASSUMPTION AFTER ASSIGNRESOURCES COMMAND: "
        "Subarray Node device"
        f"({central_node_mid.subarray_node.dev_name()}) "
        "is expected to be in IDLE obstate",
    ).within_timeout(TIMEOUT).has_change_event_occurred(
        central_node_mid.subarray_node,
        "obsState",
        ObsState.IDLE,
    )
    assert_that(event_tracer).described_as(
        "FAILED ASSUMPTION AFTER ASSIGNRESOURCES COMMAND: "
        "'the subarray is in IDLE obsState'"
        "Subarray Node device"
        f"({central_node_mid.central_node.dev_name()}) "
        "is expected have longRunningCommand as"
        '(unique_id,(ResultCode.OK,"Command Completed"))',
    ).within_timeout(TIMEOUT).has_change_event_occurred(
        central_node_mid.central_node,
        "longRunningCommandResult",
        (
            unique_id[0],
            COMMAND_COMPLETED,
        ),
    )
    subarray_node.simulate_receive_addresses_event(
        sdp_sim, command_input_factory
    )
    event_tracer.clear_events()

    # Configure command
    configure_input_json = prepare_json_args_for_commands(
        "configure_holography_adr106", command_input_factory
    )
    _, unique_id = subarray_node.execute_transition(
        "Configure", configure_input_json
    )

    assert_that(event_tracer).described_as(
        "FAILED ASSUMPTION AFTER CONFIGURE COMMAND: "
        "Subarray Node device"
        f"({subarray_node.subarray_node.dev_name()}) "
        "is expected to be in READY obstate",
    ).within_timeout(TIMEOUT).has_change_event_occurred(
        subarray_node.subarray_node,
        "obsState",
        ObsState.READY,
    )
    assert_that(event_tracer).described_as(
        "FAILED ASSUMPTION AFTER CONFIGURE COMMAND: "
        "'the subarray is in READY obsState'"
        "Subarray Node device"
        f"({subarray_node.subarray_node.dev_name()}) "
        "is expected have longRunningCommand as"
        '(unique_id,(ResultCode.OK,"Command Completed"))',
    ).within_timeout(TIMEOUT).has_change_event_occurred(
        subarray_node.subarray_node,
        "longRunningCommandResult",
        (
            unique_id[0],
            COMMAND_COMPLETED,
        ),
    )
    event_tracer.clear_events()

    # Scan Command
    scan_command_input = prepare_json_args_for_commands(
        "scan_mid", command_input_factory
    )
    subarray_node.execute_transition("Scan", scan_command_input)
    assert_that(event_tracer).described_as(
        "FAILED ASSUMPTION AFTER SCAN COMMAND: "
        "Subarray Node device"
        f"({subarray_node.subarray_node.dev_name()}) "
        "is expected to be in SCANNING obstate",
    ).within_timeout(TIMEOUT).has_change_event_occurred(
        subarray_node.subarray_node,
        "obsState",
        ObsState.SCANNING,
    )
    assert wait_and_validate_device_attribute_value(
        subarray_node.subarray_node, "obsState", ObsState.READY
    )
    event_tracer.clear_events()

    # Partial configurations and scans
    partial_configuration_jsons = [
        f"partial_configure_{i}" for i in range(1, 5)
    ]
    subarray_node.execute_five_point_calibration_scan(
        partial_configuration_jsons,
        event_tracer,
        command_input_factory,
    )

    # Setting pointing calibration data
    subarray_node.set_pointing_cal_on_queue_connector()


@then(
    "the dish leaf node receive calibration solutions from SDP and "
    + "applies them to the Dishes"
)
def subarray_applies_calibration_solutions_to_dishes(
    subarray_node: SubarrayNodeWrapper,
):
    """Then the Subarray fetches and applies the configuration solutions to the
    dishes."""

    assert wait_and_validate_device_attribute_value(
        subarray_node.dish_leaf_node_list[0],
        "lastPointingData",
        json.dumps(DISH_001_CALIBRATION_DATA),
        is_json=True,
        timeout=30,
    )
    assert wait_and_validate_device_attribute_value(
        subarray_node.dish_leaf_node_list[1],
        "lastPointingData",
        json.dumps(DISH_036_CALIBRATION_DATA),
        is_json=True,
        timeout=30,
    )


@then("is in READY obsState")
def subarray_is_in_ready_obsstate(subarray_node: SubarrayNodeWrapper):
    """Subarray is in READY obsState."""
    assert check_subarray_obs_state("READY", 500, subarray_node=subarray_node)
