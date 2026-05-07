"""Common Utils method used across multiple test cases
"""
import json

from ska_control_model import ObsState
from ska_integration_test_harness.facades.csp_facade import CSPFacade
from ska_integration_test_harness.facades.sdp_facade import SDPFacade
from ska_integration_test_harness.facades.tmc_facade import TMCFacade
from ska_integration_test_harness.inputs.test_harness_inputs import (
    TestHarnessInputs,
)
from ska_tango_testing.integration import TangoEventTracer, log_events
from tango import DeviceProxy

from tests.resources.test_harness.utils.enums import DishMode, PointingState
from tests.resources.test_support.constant import (
    IDLE_STATE_DEFECT,
    INTERMEDIATE_CONFIGURING_OBS_STATE_DEFECT,
    INTERMEDIATE_DISH_MODE_STATE_DEFECT_DISH,
    INTERMEDIATE_FAULT_OBS_STATE_DEFECT,
    INTERMEDIATE_READY_STATE_DEFECT_DISH,
    INTERMEDIATE_SLEW_STATE_DEFECT_DISH,
    INTERMEDIATE_STATE_DEFECT,
    INTERMEDIATE_TRACK_STATE_DEFECT_DISH,
    READY_STATE_DEFECT,
    RESET_DEFECT,
    SDP_BACK_TO_INITIAL_STATE,
    csp_subarray1,
    csp_subarray2,
    sdp_subarray1,
    sdp_subarray2,
)


def setup_event_subscriptions(
    tmc: TMCFacade,
    csp: CSPFacade,
    sdp: SDPFacade,
    event_tracer: TangoEventTracer,
):
    """Subscribe TMC, CSP and SDP devices to track and log obsState events.

    :param tmc: the TMC facade.
    :param csp: the CSP facade.
    :param sdp: the SDP facade.
    :param event_tracer: the event tracer.
    """
    event_tracer.subscribe_event(tmc.subarray_node, "obsState")
    event_tracer.subscribe_event(csp.csp_subarray, "obsState")
    event_tracer.subscribe_event(sdp.sdp_subarray, "obsState")
    event_tracer.subscribe_event(sdp.sdp_subarray, "receiveAddresses")
    event_tracer.subscribe_event(sdp.sdp_subarray, "commandCallInfo")
    event_tracer.subscribe_event(tmc.central_node, "longRunningCommandResult")
    event_tracer.subscribe_event(tmc.subarray_node, "longRunningCommandResult")
    event_tracer.subscribe_event(
        tmc.csp_subarray_leaf_node, "CspSubarrayObsState"
    )

    log_events(
        {
            tmc.subarray_node: [
                "obsState",
                "longRunningCommandResult",
            ],
            csp.csp_subarray: ["obsState"],
            sdp.sdp_subarray: [
                "obsState",
                "commandCallInfo",
                "receiveAddresses",
            ],
            tmc.central_node: ["longRunningCommandResult"],
            tmc.csp_subarray_leaf_node: ["CspSubarrayObsState"],
        },
        event_enum_mapping={"obsState": ObsState},
    )


def setup_event_dish_subscription(event_tracer, dishes_list):
    """Setup Event subscription for dishes"""
    for dish in dishes_list:
        event_tracer.subscribe_event(dish, "pointingState")
        event_tracer.subscribe_event(dish, "dishMode")
        event_tracer.subscribe_event(dish, "sourceOffset")
        log_events(
            {dish: ["pointingState", "dishMode"]},
            event_enum_mapping={
                "pointingState": PointingState,
                "dishMode": DishMode,
            },
        )


command_defect_mapping = {
    "AssignResources": {
        "RESOURCING": json.dumps(INTERMEDIATE_STATE_DEFECT),
        "FAULT": json.dumps(INTERMEDIATE_FAULT_OBS_STATE_DEFECT),
        "EMPTY": json.dumps(INTERMEDIATE_STATE_DEFECT),
    },
    "Configure": {
        "CONFIGURING": json.dumps(INTERMEDIATE_CONFIGURING_OBS_STATE_DEFECT),
        "FAULT": json.dumps(INTERMEDIATE_FAULT_OBS_STATE_DEFECT),
        "SLEW": json.dumps(INTERMEDIATE_SLEW_STATE_DEFECT_DISH),
        "CONFIG": json.dumps(INTERMEDIATE_DISH_MODE_STATE_DEFECT_DISH),
    },
    "Scan": {
        "READY": READY_STATE_DEFECT,
        "FAULT": json.dumps(INTERMEDIATE_FAULT_OBS_STATE_DEFECT),
    },
    "ReleaseResources": {
        "IDLE": json.dumps(IDLE_STATE_DEFECT),
        "RESOURCING": json.dumps(INTERMEDIATE_STATE_DEFECT),
        "FAULT": json.dumps(INTERMEDIATE_FAULT_OBS_STATE_DEFECT),
    },
    "EndScan": {"FAULT": json.dumps(INTERMEDIATE_FAULT_OBS_STATE_DEFECT)},
    "End": {"FAULT": json.dumps(INTERMEDIATE_FAULT_OBS_STATE_DEFECT)},
}


def set_subsystem_defects(
    csp: CSPFacade,
    sdp: SDPFacade,
    csp_obsstate: str,
    sdp_obsstate: str,
    command: str,
    dish_pointingstates: list = [],
    dishes: list = [],
    dish_mode_list: list = [],
):
    """
    Set defects for the CSP and SDP subsystems based on their
    observation states and a command.

    Args:
        csp (CSPFacade): The CSP subsystem facade instance.
        sdp (SDPFacade): The SDP subsystem facade instance.
        csp_obsstate (str): The observation state string for the CSP subsystem.
        sdp_obsstate (str): The observation state string for the SDP subsystem.
        command (str): The command string to apply defects or changes.

    """
    csp.csp_subarray.SetDefective(
        command_defect_mapping.get(command).get(csp_obsstate, RESET_DEFECT)
    )

    if sdp_obsstate == "EMPTY" and command == "AssignResources":
        sdp.sdp_subarray.SetDefective(SDP_BACK_TO_INITIAL_STATE)
    else:
        sdp.sdp_subarray.SetDefective(
            command_defect_mapping.get(command).get(sdp_obsstate, RESET_DEFECT)
        )
    if dish_pointingstates:
        for dish, dish_pointingstate, dish_mode in zip(
            dishes, dish_pointingstates, dish_mode_list
        ):
            if dish_pointingstate == "READY" and command == "Configure":
                dish.SetDefective(
                    json.dumps(INTERMEDIATE_READY_STATE_DEFECT_DISH)
                )
            elif dish_pointingstate == "TRACK" and command == "End":
                dish.SetDefective(
                    json.dumps(INTERMEDIATE_TRACK_STATE_DEFECT_DISH)
                )
            else:
                dish.SetDefective(
                    command_defect_mapping.get(command).get(
                        dish_pointingstate, RESET_DEFECT
                    )
                )
            if dish_mode == "CONFIG":
                dish.SetDefective(
                    command_defect_mapping.get(command).get(
                        dish_mode, RESET_DEFECT
                    )
                )


def invoke_command_with_defect(
    tmc: TMCFacade,
    default_commands_inputs: TestHarnessInputs,
    csp: CSPFacade,
    sdp: SDPFacade,
    csp_obsstate: str,
    sdp_obsstate: str,
    command: str,
    pointing_states: list = [],
    dishes: list = [],
    dish_mode_list: list = [],
):
    """
    Invoke a TMC command while setting defects on CSP and SDP subsystems based
    on their observation states.

    Args:
        tmc (TMCFacade): The TMC subsystem facade instance used to
        invoke commands.
        default_commands_inputs (TestHarnessInputs): The default inputs
        required for TMC commands.
        csp (CSPFacade): The CSP subsystem facade instance.
        sdp (SDPFacade): The SDP subsystem facade instance.
        csp_obsstate (str): The observation state string.
        sdp_obsstate (str): The observation state string.
        command (str): The command string to invoke

    """
    match command:
        case "AssignResources":
            set_subsystem_defects(
                csp,
                sdp,
                csp_obsstate,
                sdp_obsstate,
                command,
            )
            tmc.assign_resources(
                default_commands_inputs.assign_input, wait_termination=False
            )
        case "Configure":
            tmc.force_change_of_obs_state(
                ObsState.IDLE, default_commands_inputs, wait_termination=True
            )
            set_subsystem_defects(
                csp,
                sdp,
                csp_obsstate,
                sdp_obsstate,
                command,
                dish_pointingstates=pointing_states,
                dishes=dishes,
                dish_mode_list=dish_mode_list,
            )
            tmc.configure(
                default_commands_inputs.configure_input, wait_termination=False
            )
        case "Scan":
            tmc.force_change_of_obs_state(
                ObsState.READY, default_commands_inputs, wait_termination=True
            )
            set_subsystem_defects(
                csp,
                sdp,
                csp_obsstate,
                sdp_obsstate,
                command,
                dish_pointingstates=pointing_states,
                dishes=dishes,
                dish_mode_list=dish_mode_list,
            )
            tmc.scan(
                default_commands_inputs.scan_input, wait_termination=False
            )
        case "ReleaseResources":
            tmc.force_change_of_obs_state(
                ObsState.IDLE, default_commands_inputs, wait_termination=True
            )
            set_subsystem_defects(
                csp,
                sdp,
                csp_obsstate,
                sdp_obsstate,
                command,
            )
            tmc.release_resources(
                default_commands_inputs.release_input, wait_termination=False
            )
        case "End":
            tmc.force_change_of_obs_state(
                ObsState.READY, default_commands_inputs, wait_termination=True
            )
            set_subsystem_defects(
                csp,
                sdp,
                csp_obsstate,
                sdp_obsstate,
                command,
                dish_pointingstates=pointing_states,
                dishes=dishes,
                dish_mode_list=dish_mode_list,
            )
            tmc.end_observation(wait_termination=False)
        case "EndScan":
            tmc.force_change_of_obs_state(
                ObsState.SCANNING,
                default_commands_inputs,
                wait_termination=True,
            )
            set_subsystem_defects(
                csp,
                sdp,
                csp_obsstate,
                sdp_obsstate,
                command,
                dish_pointingstates=pointing_states,
                dishes=dishes,
                dish_mode_list=dish_mode_list,
            )
            tmc.end_scan(wait_termination=False)


def reset_defects(csp: CSPFacade, sdp: SDPFacade, dish_master_list: list = []):
    """Reset the defects for csp and sdp"""
    csp.csp_subarray.SetDefective(RESET_DEFECT)
    sdp.sdp_subarray.SetDefective(RESET_DEFECT)
    for dish in dish_master_list:
        dish.SetDefective(RESET_DEFECT)


def get_mid_csp_sdp_subarrays_proxies():
    """Return MID CSP and SDP subarray device proxies."""
    return {
        "sdp_1": DeviceProxy(sdp_subarray1),
        "sdp_2": DeviceProxy(sdp_subarray2),
        "csp_1": DeviceProxy(csp_subarray1),
        "csp_2": DeviceProxy(csp_subarray2),
    }
