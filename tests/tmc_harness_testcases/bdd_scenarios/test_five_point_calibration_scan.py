"""Testing the 5 point calibration scan"""
import pytest
from assertpy import assert_that
from pytest_bdd import given, parsers, scenario, then, when
from ska_control_model import ObsState
from ska_tango_testing.integration import log_events

from tests.resources.test_harness.helpers import (
    check_subarray_obs_state,
    prepare_json_args_for_centralnode_commands,
    prepare_json_args_for_commands,
)
from tests.resources.test_support.constant import COMMAND_COMPLETED

# Assertion timeouts
TIMEOUT = 50


@pytest.mark.batch1
@pytest.mark.SKA_mid
@scenario(
    "../features/test_harness/five_point_scan.feature",
    "TMC implements five point calibration scan: TMC executes five point "
    + "calibration scan successfully.",
)
def test_five_point_calibration_scan():
    """
    Test case to verify the 5 point calibration scan functionality on TMC
    """


@given("a TMC")
def given_tmc(subarray_node, event_tracer):
    """Given a TMC"""
    event_tracer.subscribe_event(subarray_node.subarray_node, "obsState")
    event_tracer.subscribe_event(
        subarray_node.subarray_node, "longRunningCommandResult"
    )

    # Logging setup
    log_events(
        {
            subarray_node.subarray_node: [
                "obsState",
                "longRunningCommandResult",
            ],
        }
    )

    subarray_node.move_to_on()
    assert_that(event_tracer).described_as(
        "FAILED UNEXPECTED INITIAL OBSSTATE: "
        "Subarray Node device"
        f"({subarray_node.subarray_node.dev_name()}) "
        "is expected to be in EMPTY obstate",
    ).within_timeout(TIMEOUT).has_change_event_occurred(
        subarray_node.subarray_node,
        "obsState",
        ObsState.EMPTY,
    )
    event_tracer.clear_events()


@given("a subarray configured for a calibration scan")
def a_configured_subarray(
    subarray_node, event_tracer, simulator_factory, command_input_factory
):
    """Given a subarray configured for a calibration scan."""
    assign_input_json = prepare_json_args_for_centralnode_commands(
        "assign_resources_mid", command_input_factory
    )
    configure_input_json = prepare_json_args_for_commands(
        "configure_holography_adr106", command_input_factory
    )

    subarray_node.force_change_of_obs_state(
        "READY",
        assign_input_json=assign_input_json,
        configure_input_json=configure_input_json,
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

    scan_command_input = prepare_json_args_for_commands(
        "scan_mid", command_input_factory
    )
    _, unique_id = subarray_node.execute_transition("Scan", scan_command_input)

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
    assert_that(event_tracer).described_as(
        "FAILED ASSUMPTION AFTER SCAN COMMAND: "
        "'the subarray is in SCANNING obsState'"
        "Subarray Node device"
        f"({subarray_node.subarray_node.dev_name()}) "
        "is expected have longRunningCommand as"
        f"({unique_id[0]},{COMMAND_COMPLETED})",
    ).within_timeout(TIMEOUT).has_change_event_occurred(
        subarray_node.subarray_node,
        "longRunningCommandResult",
        (
            unique_id[0],
            COMMAND_COMPLETED,
        ),
    )
    event_tracer.clear_events()


@given("the subarray is in READY obsState")
def a_subarray_in_ready_obsstate(subarray_node):
    """A subarray in READY obsState."""
    assert check_subarray_obs_state("READY", 500, subarray_node)


@when(
    parsers.parse(
        "I perform four partial configurations with json "
        + "{partial_configuration_json} and scans"
    )
)
def when_i_perform_partial_configurations_and_scans(
    subarray_node,
    event_tracer,
    command_input_factory,
    partial_configuration_json,
):
    """When I perform partial configurations and scans."""
    partial_configuration_jsons = partial_configuration_json.rstrip().split(
        ","
    )

    subarray_node.execute_five_point_calibration_scan(
        partial_configuration_jsons,
        event_tracer,
        command_input_factory,
    )

    # Check the actual pointing attribute is not empty
    assert subarray_node.dish_leaf_node_list[0].actualPointing


@then(
    "the subarray executes the commands successfully and is in READY obsState"
)
def subarray_executes_commands_successfully(subarray_node):
    """Subarray executes the commands successfully and is in READY obsState."""
    assert check_subarray_obs_state("READY", 500, subarray_node)
