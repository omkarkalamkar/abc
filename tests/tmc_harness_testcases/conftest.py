"""
Common modules for reuse
"""


import json

import pytest
from assertpy import assert_that
from pytest_bdd import given, parsers, then, when
from ska_control_model import ObsState, ResultCode
from ska_tango_testing.integration import TangoEventTracer, log_events
from tango import DevState

from tests.conftest import LOGGER
from tests.resources.test_harness.central_node_mid import CentralNodeWrapperMid
from tests.resources.test_harness.helpers import (
    prepare_json_args_for_centralnode_commands,
    prepare_json_args_for_commands,
)
from tests.resources.test_harness.simulator_factory import SimulatorFactory
from tests.resources.test_harness.subarray_node import SubarrayNodeWrapper
from tests.resources.test_harness.utils.common_utils import JsonFactory
from tests.resources.test_harness.utils.enums import SimulatorDeviceType
from tests.resources.test_support.constant import (
    ERROR_PROPAGATION_DEFECT,
    FAILED_DEFECT,
    TIMEOUT,
    tmc_csp_subarray_leaf_node,
    tmc_dish_leaf_node1,
    tmc_sdp_subarray_leaf_node,
)


@given("the telescope is ON state")
def check_telescope_is_in_on_state(
    central_node_mid: CentralNodeWrapperMid,
    subarray_node: SubarrayNodeWrapper,
    event_tracer: TangoEventTracer,
) -> None:
    """
    Ensure telescope is in ON state.
    """
    # Event Subscriptions
    event_tracer.subscribe_event(
        central_node_mid.central_node, "telescopeState"
    )
    event_tracer.subscribe_event(
        central_node_mid.central_node, "longRunningCommandResult"
    )
    event_tracer.subscribe_event(
        subarray_node.subarray_node, "longRunningCommandResult"
    )
    event_tracer.subscribe_event(subarray_node.subarray_node, "obsState")
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
    central_node_mid.move_to_on()
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


def perform_idle_transition(
    central_node_mid: CentralNodeWrapperMid,
    subarray_node: SubarrayNodeWrapper,
    event_tracer: TangoEventTracer,
    command_input_factory: JsonFactory,
):
    """
    Execute Assign and verify
    """

    event_tracer.subscribe_event(subarray_node.subarray_node, "obsState")
    event_tracer.subscribe_event(
        central_node_mid.central_node, "longRunningCommandResult"
    )

    log_events(
        {
            central_node_mid.central_node: [
                "longRunningCommandResult",
            ]
        }
    )

    assign_input_str = prepare_json_args_for_centralnode_commands(
        "assign_resources_mid", command_input_factory
    )
    _, unique_id = central_node_mid.store_resources(assign_input_str)

    assert_that(event_tracer).described_as(
        "FAILED ASSUMPTION AFTER ASSIGNRESOURCES COMMAND: "
        "Subarray Node device"
        f"({subarray_node.subarray_node.dev_name()}) "
        "is expected to be in IDLE obstate",
    ).within_timeout(TIMEOUT).has_change_event_occurred(
        subarray_node.subarray_node,
        "obsState",
        ObsState.IDLE,
    )

    assert_that(event_tracer).described_as(
        'FAILED ASSUMPTION IN "GIVEN" STEP: '
        "Central Node device"
        f"({central_node_mid.central_node.dev_name()}) "
        "is expected have longRunningCommand as"
        '(unique_id,(ResultCode.OK,"Command Completed"))',
    ).within_timeout(TIMEOUT).has_change_event_occurred(
        central_node_mid.central_node,
        "longRunningCommandResult",
        (unique_id[0], json.dumps((int(ResultCode.OK), "Command Completed"))),
    )
    event_tracer.clear_events()


def verify_scanning_transition_with_endscan(
    subarray_node: SubarrayNodeWrapper,
):
    """
    Execute EndScan
    """

    _, pytest.unique_id = subarray_node.execute_transition("EndScan")


def perform_ready_transition_with_end(
    subarray_node: SubarrayNodeWrapper,
    event_tracer: TangoEventTracer,
):
    """
    Execute End and verify error propagation
    """

    _, pytest.unique_id = subarray_node.subarray_node.End()

    assert_that(event_tracer).described_as(
        'FAILED ASSUMPTION IN "WHEN" STEP: '
        '"I end the observation"'
        "Subarray Node device"
        f"({subarray_node.subarray_node.dev_name()}) "
        "is expected to be in IDLE obstate",
    ).within_timeout(TIMEOUT).has_change_event_occurred(
        subarray_node.subarray_node,
        "obsState",
        ObsState.CONFIGURING,
    )


def perform_scan(
    subarray_node: SubarrayNodeWrapper,
    command_input_factory: JsonFactory,
):

    """
    Perform Scan
    """

    scan_input_json = prepare_json_args_for_commands(
        "scan_mid", command_input_factory
    )

    _, pytest.unique_id = subarray_node.execute_transition(
        "Scan", scan_input_json
    )


def perform_scanning_transition(
    subarray_node: SubarrayNodeWrapper,
    event_tracer: TangoEventTracer,
    command_input_factory: JsonFactory,
):
    """
    Send a Scan command to the subarray.
    """
    event_tracer.subscribe_event(
        subarray_node.subarray_node, "longRunningCommandResult"
    )
    scan_input_json = prepare_json_args_for_commands(
        "scan_mid", command_input_factory
    )
    _, unique_id = subarray_node.execute_transition("Scan", scan_input_json)

    assert_that(event_tracer).described_as(
        'FAILED ASSUMPTION IN "THEN" STEP: '
        "'the subarray must be in the SCANNING obsState until finished'"
        "Subarray Node device"
        f"({subarray_node.subarray_node.dev_name()}) "
        "is expected to be in SCANNING obstate",
    ).within_timeout(TIMEOUT).has_change_event_occurred(
        subarray_node.subarray_node,
        "obsState",
        ObsState.SCANNING,
    )

    assert_that(event_tracer).described_as(
        'FAILED ASSUMPTION IN "GIVEN" STEP: '
        "Central Node device"
        f"({subarray_node.subarray_node.dev_name()}) "
        "is expected have longRunningCommand as"
        '(unique_id,(ResultCode.OK,"Command Completed"))',
    ).within_timeout(TIMEOUT).has_change_event_occurred(
        subarray_node.subarray_node,
        "longRunningCommandResult",
        (unique_id[0], json.dumps((int(ResultCode.OK), "Command Completed"))),
    )
    event_tracer.clear_events()


def perform_ready_transition(
    central_node_mid: CentralNodeWrapperMid,
    subarray_node: SubarrayNodeWrapper,
    event_tracer: TangoEventTracer,
    command_input_factory: JsonFactory,
):
    """
    Send a Configure command to the subarray.
    """

    configure_input_json = prepare_json_args_for_commands(
        "configure_mid", command_input_factory
    )
    _, unique_id = subarray_node.store_configuration_data(configure_input_json)

    event_tracer.subscribe_event(
        subarray_node.subarray_devices.get("sdp_subarray"), "obsState"
    )
    event_tracer.subscribe_event(
        subarray_node.subarray_devices.get("csp_subarray"), "obsState"
    )
    event_tracer.subscribe_event(
        subarray_node.csp_subarray_leaf_node, "cspSubarrayObsState"
    )
    event_tracer.subscribe_event(
        subarray_node.sdp_subarray_leaf_node, "sdpSubarrayObsState"
    )
    log_events(
        {
            subarray_node.subarray_devices.get("sdp_subarray"): ["obsState"],
            subarray_node.subarray_devices.get("csp_subarray"): ["obsState"],
            subarray_node.csp_subarray_leaf_node: ["cspSubarrayObsState"],
            subarray_node.sdp_subarray_leaf_node: ["sdpSubarrayObsState"],
        }
    )
    csp = subarray_node.subarray_devices.get("csp_subarray")
    sdp = subarray_node.subarray_devices.get("sdp_subarray")
    assert_that(event_tracer).described_as(
        'FAILED ASSUMPTION IN "THEN" STEP: '
        "'the subarray must be in the READY obsState'"
        "CSP Subarray Leaf Node device"
        f"({subarray_node.csp_subarray_leaf_node.dev_name()}) "
        "is expected to be in READY obstate",
    ).within_timeout(TIMEOUT).has_change_event_occurred(
        subarray_node.csp_subarray_leaf_node,
        "cspSubarrayObsState",
        ObsState.READY,
    )
    assert_that(event_tracer).described_as(
        'FAILED ASSUMPTION IN "THEN" STEP: '
        "'the subarray must be in the READY obsState'"
        "SDP Subarray Leaf Node device"
        f"({subarray_node.sdp_subarray_leaf_node.dev_name()}) "
        "is expected to be in READY obstate",
    ).within_timeout(TIMEOUT).has_change_event_occurred(
        subarray_node.sdp_subarray_leaf_node,
        "sdpSubarrayObsState",
        ObsState.READY,
    )
    assert_that(event_tracer).described_as(
        'FAILED ASSUMPTION IN "THEN" STEP: '
        "'the subarray must be in the READY obsState'"
        "CSP Subarray device"
        f"({csp.dev_name()}) "
        "is expected to be in READY obstate",
    ).within_timeout(TIMEOUT).has_change_event_occurred(
        csp,
        "obsState",
        ObsState.READY,
    )
    assert_that(event_tracer).described_as(
        'FAILED ASSUMPTION IN "THEN" STEP: '
        "'the subarray must be in the READY obsState'"
        "SDP Subarray device"
        f"({sdp.dev_name()}) "
        "is expected to be in READY obstate",
    ).within_timeout(TIMEOUT).has_change_event_occurred(
        sdp,
        "obsState",
        ObsState.READY,
    )
    assert_that(event_tracer).described_as(
        'FAILED ASSUMPTION IN "THEN" STEP: '
        "'the subarray must be in the READY obsState'"
        "Subarray Node device"
        f"({central_node_mid.subarray_node.dev_name()}) "
        "is expected to be in READY obstate",
    ).within_timeout(TIMEOUT).has_change_event_occurred(
        central_node_mid.subarray_node,
        "obsState",
        ObsState.READY,
    )

    assert_that(event_tracer).described_as(
        'FAILED ASSUMPTION IN "GIVEN" STEP: '
        "Subarray Node device"
        f"({central_node_mid.subarray_node.dev_name()}) "
        "is expected have longRunningCommand as"
        '(unique_id,(ResultCode.OK,"Command Completed"))',
    ).within_timeout(TIMEOUT).has_change_event_occurred(
        central_node_mid.subarray_node,
        "longRunningCommandResult",
        (unique_id[0], json.dumps((int(ResultCode.OK), "Command Completed"))),
    )


@given(
    parsers.parse(
        "the TMC subarray is in the {initialObsState} observation state"
    )
)
def move_tmc_to_intial_state(
    central_node_mid: CentralNodeWrapperMid,
    subarray_node: SubarrayNodeWrapper,
    event_tracer: TangoEventTracer,
    command_input_factory: JsonFactory,
    initialObsState,
):

    """
    Method to move and verify tmc  subarray  in required initial
    observation state.
    """

    match initialObsState:
        case "IDLE":
            perform_idle_transition(
                central_node_mid,
                subarray_node,
                event_tracer,
                command_input_factory,
            )

        case "READY":
            perform_idle_transition(
                central_node_mid,
                subarray_node,
                event_tracer,
                command_input_factory,
            )
            perform_ready_transition(
                central_node_mid,
                subarray_node,
                event_tracer,
                command_input_factory,
            )

        case "SCANNING":
            perform_idle_transition(
                central_node_mid,
                subarray_node,
                event_tracer,
                command_input_factory,
            )
            perform_ready_transition(
                central_node_mid,
                subarray_node,
                event_tracer,
                command_input_factory,
            )
            perform_scanning_transition(
                subarray_node,
                event_tracer,
                command_input_factory,
            )


@when(
    parsers.parse(
        "{command} is invoked on a defectiveSubsystem {defectiveSubsystem}"
    )
)
def execute_command_on_tmc_with_defectivesetup(
    central_node_mid: CentralNodeWrapperMid,
    subarray_node: SubarrayNodeWrapper,
    event_tracer: TangoEventTracer,
    simulator_factory: SimulatorFactory,
    command_input_factory: JsonFactory,
    command,
    defectiveSubsystem,
):
    """
    Execute command on TMC subarray node with defective subsystem.
    """

    pytest.defective_subarray = None
    match defectiveSubsystem:
        case "CSP":
            pytest.defective_subarray = (
                simulator_factory.get_or_create_simulator_device(
                    SimulatorDeviceType.MID_CSP_DEVICE
                )
            )
            pytest.defective_device = tmc_csp_subarray_leaf_node
            pytest.defective_subarray.SetDefective(ERROR_PROPAGATION_DEFECT)
        case "SDP":
            pytest.defective_subarray = (
                simulator_factory.get_or_create_simulator_device(
                    SimulatorDeviceType.MID_SDP_DEVICE
                )
            )
            pytest.defective_device = tmc_sdp_subarray_leaf_node
            pytest.defective_subarray.SetDefective(FAILED_DEFECT)

        case "DISH":

            pytest.defective_subarray = (
                simulator_factory.get_or_create_simulator_device(
                    SimulatorDeviceType.DISH_DEVICE
                )
            )
            # Set dish 1 defective
            pytest.defective_device = tmc_dish_leaf_node1
            pytest.defective_subarray.SetDefective(ERROR_PROPAGATION_DEFECT)
            LOGGER.info("Work on dish in Progress")

    match command:
        case "RELEASERESOURCES":
            (
                _,
                pytest.unique_id,
            ) = subarray_node.subarray_node.ReleaseAllResources()

        case "ASSIGNRESOURCES":
            assign_input_str = prepare_json_args_for_commands(
                "assign_resources_mid", command_input_factory
            )
            _, pytest.unique_id = subarray_node.subarray_node.AssignResources(
                assign_input_str
            )
        case "CONFIGURE":
            configure_input_json = prepare_json_args_for_commands(
                "configure_mid", command_input_factory
            )
            _, pytest.unique_id = subarray_node.subarray_node.Configure(
                configure_input_json
            )

        case "END":
            perform_ready_transition_with_end(
                subarray_node,
                event_tracer,
            )

        case "ENDSCAN":
            verify_scanning_transition_with_endscan(
                subarray_node,
            )
        case "SCAN":
            perform_scan(subarray_node, command_input_factory)


@then(
    parsers.parse(
        "the command failure is reported by subarray with error message"
    )
)
def validate_error_message_reporting(
    subarray_node: SubarrayNodeWrapper,
    event_tracer: TangoEventTracer,
):
    """
    Check if subarray node populates error message correctly.
    """

    exception_message = (
        "Exception occurred on the following devices:"
        + f" {pytest.defective_device}:"
    )

    assert_that(event_tracer).described_as(
        'FAILED ASSUMPTION IN "THEN" STEP: '
        '"the command failure is reported by subarray with appropriate"'
        '"error message"'
        "Subarray Node device"
        f"({subarray_node.subarray_node.dev_name()}) "
        "is expected have longRunningCommandResult"
        "(ResultCode.FAILED,exception)",
    ).within_timeout(120).has_desired_result_code_message_in_lrcr_event(
        subarray_node.subarray_node,
        [exception_message],
        pytest.unique_id[0],
        ResultCode.FAILED,
    )

    pytest.defective_subarray.SetDefective(json.dumps({"enabled": False}))


@then("the TMC SubarrayNode transitions to FAULT obsState")
def validate_subarry_obsState(
    subarray_node: SubarrayNodeWrapper,
    event_tracer: TangoEventTracer,
):
    """
    Check if TMC subarray remains in stuck Obs-State.
    """
    assert_that(event_tracer).described_as(
        'FAILED ASSUMPTION IN "THEN" STEP: '
        '"the TMC SubarrayNode transitions to FAULT obsState"'
        f"({subarray_node.subarray_node.dev_name()}) "
        "is expected to be in FAULT obstate",
    ).within_timeout(TIMEOUT).has_change_event_occurred(
        subarray_node.subarray_node,
        "obsState",
        ObsState.FAULT,
    )
