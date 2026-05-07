"""
Test case to verify error propagation functionality for
the End / Scan /EndScan command

This test case verifies that one of  the CSP/SDP Subarray
is identified as defective,
 and the required command is executed on the TMC Mid,
 then Subarry node
   reports an error
"""
import json

import pytest
from assertpy import assert_that
from pytest_bdd import parsers, scenario, then, when
from ska_control_model import ResultCode
from ska_tango_base.control_model import ObsState
from ska_tango_testing.integration import TangoEventTracer

from tests.conftest import LOGGER
from tests.resources.test_harness.central_node_mid import CentralNodeWrapperMid
from tests.resources.test_harness.helpers import prepare_json_args_for_commands
from tests.resources.test_harness.simulator_factory import SimulatorFactory
from tests.resources.test_harness.subarray_node import SubarrayNodeWrapper
from tests.resources.test_harness.utils.common_utils import JsonFactory
from tests.resources.test_harness.utils.enums import SimulatorDeviceType
from tests.resources.test_support.constant import (
    INTERMEDIATE_CONFIGURING_STATE_DEFECT,
    INTERMEDIATE_CONFIGURING_STATE_DEFECT_DISH,
    INTERMEDIATE_READY_STATE_DEFECT,
    INTERMEDIATE_RESOURCING_STATE_DEFECT,
    INTERMEDIATE_SCANNING_STATE_DEFECT,
    tmc_csp_subarray_leaf_node,
    tmc_dish_leaf_node1,
    tmc_sdp_subarray_leaf_node,
)
from tests.tmc_harness_testcases.conftest import (
    perform_ready_transition_with_end,
    perform_scan,
    verify_scanning_transition_with_endscan,
)


@pytest.mark.batch1
@pytest.mark.SKA_mid
@scenario(
    "../features/check_error_propagation.feature",
    "Error Propagation Reported by TMC Mid "
    "AssignResources/ReleaseAllResources/Configure/End/EndScan/Scan "
    "Commands for Defective Subarray",
)
def test_tmc_command_error_propagation():
    """
    Test case to verify TMC Error Propagation functionality.
    """


@pytest.mark.batch2
@pytest.mark.SKA_mid
@scenario(
    "../features/check_error_propagation.feature",
    "TimeOut Reported by TMC Mid "
    "AssignResources/ReleaseAllResources/Configure/End/EndScan/Scan "
    "Commands for Defective Subarray",
)
def test_tmc_command_timeout_error_propagation():
    """
    Test case to verify TMC TimeOut Error Propagation functionality.
    """


@pytest.mark.batch2
@pytest.mark.SKA_mid
@scenario(
    "../features/check_error_propagation.feature",
    "TMC moves to FAULT obsState when CSP/SDP " "moves to FAULT obsState",
)
def test_tmc_moves_to_fault_with_subsystem():
    """
    Test case to verify TMC moves to FAULT observation state if
    one of the subsystem moves to FAULT observation state.
    """


def execute_command(
    device,
    command,
    central_node_mid: CentralNodeWrapperMid,
    subarray_node: SubarrayNodeWrapper,
    event_tracer: TangoEventTracer,
    command_input_factory: JsonFactory,
):
    """
    Execute command
    """
    if device in ["CSP", "DISH"]:
        match command:
            case "RELEASERESOURCES":
                pytest.defective_subarray.SetDefective(
                    INTERMEDIATE_RESOURCING_STATE_DEFECT
                )
                (
                    _,
                    pytest.unique_id,
                ) = subarray_node.subarray_node.ReleaseAllResources()

            case "ASSIGNRESOURCES":
                pytest.defective_subarray.SetDefective(
                    INTERMEDIATE_RESOURCING_STATE_DEFECT
                )
                assign_input_str = prepare_json_args_for_commands(
                    "assign_resources_mid", command_input_factory
                )
                (
                    _,
                    pytest.unique_id,
                ) = subarray_node.subarray_node.AssignResources(
                    assign_input_str
                )
            case "CONFIGURE":
                if device == "DISH":
                    pytest.defective_subarray.SetDefective(
                        INTERMEDIATE_CONFIGURING_STATE_DEFECT_DISH
                    )
                else:
                    pytest.defective_subarray.SetDefective(
                        INTERMEDIATE_CONFIGURING_STATE_DEFECT
                    )

                LOGGER.info("Working on Configure")
                configure_input_json = prepare_json_args_for_commands(
                    "configure_mid", command_input_factory
                )
                _, pytest.unique_id = subarray_node.subarray_node.Configure(
                    configure_input_json
                )
            case "END":
                if device == "DISH":
                    pytest.defective_subarray.SetDefective(
                        INTERMEDIATE_CONFIGURING_STATE_DEFECT_DISH
                    )

                else:
                    pytest.defective_subarray.SetDefective(
                        INTERMEDIATE_READY_STATE_DEFECT
                    )

                LOGGER.info("Working on Ready State")
                perform_ready_transition_with_end(
                    subarray_node,
                    event_tracer,
                )

            case "ENDSCAN":

                pytest.defective_subarray.SetDefective(
                    INTERMEDIATE_SCANNING_STATE_DEFECT
                )
                LOGGER.info("Working on End Scan")
                verify_scanning_transition_with_endscan(
                    subarray_node,
                    # event_tracer,
                )
            case "SCAN":

                pytest.defective_subarray.SetDefective(
                    INTERMEDIATE_READY_STATE_DEFECT
                )
                LOGGER.info("Workng on Scan")
                perform_scan(
                    subarray_node,
                    # event_tracer,
                    command_input_factory,
                )
    elif device == "SDP":
        match command:
            case "RELEASERESOURCES":
                pytest.defective_subarray.SetDelayInfo(
                    json.dumps({"ReleaseAllResources": 55})
                )
                (
                    _,
                    pytest.unique_id,
                ) = subarray_node.subarray_node.ReleaseAllResources()

            case "ASSIGNRESOURCES":
                pytest.defective_subarray.SetDelayInfo(
                    json.dumps({"AssignResources": 55})
                )
                assign_input_str = prepare_json_args_for_commands(
                    "assign_resources_mid", command_input_factory
                )
                (
                    _,
                    pytest.unique_id,
                ) = subarray_node.subarray_node.AssignResources(
                    assign_input_str
                )
            case "CONFIGURE":
                pytest.defective_subarray.SetDelayInfo(
                    json.dumps({"Configure": 55})
                )
                LOGGER.info("Working on Configure")
                configure_input_json = prepare_json_args_for_commands(
                    "configure_mid", command_input_factory
                )
                _, pytest.unique_id = subarray_node.subarray_node.Configure(
                    configure_input_json
                )

            case "END":
                pytest.defective_subarray.SetDelayInfo(json.dumps({"End": 55}))
                LOGGER.info("Working on Ready State")
                perform_ready_transition_with_end(
                    subarray_node,
                    event_tracer,
                )

            case "ENDSCAN":
                pytest.defective_subarray.SetDelayInfo(
                    json.dumps({"EndScan": 55})
                )
                LOGGER.info("Working on End Scan")
                verify_scanning_transition_with_endscan(
                    subarray_node,
                )

            case "SCAN":
                pytest.defective_subarray.SetDelayInfo(
                    json.dumps({"Scan": 55})
                )

                perform_scan(
                    subarray_node,
                    command_input_factory,
                )


@when(parsers.parse("{command} is invoked on a {defectiveSubsystem} Subarray"))
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
    Send next command on TMC
    """

    LOGGER.info("Inside %s  is invoked for %s", command, defectiveSubsystem)
    pytest.command = command

    pytest.defective_subarray = None
    match defectiveSubsystem:
        case "CSP":
            pytest.defective_subarray = (
                simulator_factory.get_or_create_simulator_device(
                    SimulatorDeviceType.MID_CSP_DEVICE
                )
            )
            pytest.defective_device = tmc_csp_subarray_leaf_node
            execute_command(
                "CSP",
                command,
                central_node_mid,
                subarray_node,
                event_tracer,
                command_input_factory,
            )

        case "SDP":
            pytest.defective_subarray = (
                simulator_factory.get_or_create_simulator_device(
                    SimulatorDeviceType.MID_SDP_DEVICE
                )
            )
            pytest.defective_device = tmc_sdp_subarray_leaf_node
            execute_command(
                "SDP",
                command,
                central_node_mid,
                subarray_node,
                event_tracer,
                command_input_factory,
            )

        case "DISH":

            pytest.defective_subarray = (
                simulator_factory.get_or_create_simulator_device(
                    SimulatorDeviceType.DISH_DEVICE
                )
            )
            # Set dish 1 defective
            pytest.defective_device = tmc_dish_leaf_node1

            execute_command(
                "DISH",
                command,
                central_node_mid,
                subarray_node,
                event_tracer,
                command_input_factory,
            )


@then(
    parsers.parse(
        "the command failure is reported by subarray with appropriate"
        " error message"
    )
)
def validate_error_message_reporting(
    subarray_node: SubarrayNodeWrapper,
    event_tracer: TangoEventTracer,
):
    """
    Send next command on TMC
    """
    exception_message = "Timeout has occurred, command failed"

    if (
        pytest.command == "CONFIGURE"
        and pytest.defective_device == tmc_dish_leaf_node1
    ):
        exception_message = (
            "Timeout occurred while waiting for configuredBand"
            " command to be completed in Configure command"
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
    pytest.defective_subarray.ResetDelayInfo()


@when(parsers.parse("the {subsystem} subarray moves to FAULT obsState"))
def move_csp_sdp_to_fault_obsstate(
    subarray_node: SubarrayNodeWrapper,
    subsystem,
):
    """
    Move CSP/SDP to Fault obsState
    """
    match subsystem:
        case "CSP":
            csp_subarray = subarray_node.subarray_devices.get("csp_subarray")
            csp_subarray.SetDirectObsState(ObsState.FAULT)
        case "SDP":
            sdp_subarray = subarray_node.subarray_devices.get("sdp_subarray")
            sdp_subarray.SetDirectObsState(ObsState.FAULT)
