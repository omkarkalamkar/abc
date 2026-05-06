"""This module have all required constants for ska-tmc-integration"""

import json
from enum import IntEnum

import numpy as np
from ska_control_model import ObsState

from tests.resources.test_harness.utils.enums import (
    DishMode,
    FaultType,
    PointingState,
    ResultCode,
    SimulatorDeviceType,
)
from tests.resources.test_support.common_utils.result_code import (
    FaultType as FT,
)

centralnode = "mid-tmc/central-node/0"
tmc_subarraynode1 = "mid-tmc/subarray/01"
tmc_csp_master_leaf_node = "mid-tmc/leaf-node-csp/0"
tmc_sdp_master_leaf_node = "mid-tmc/leaf-node-sdp/0"
tmc_csp_subarray_leaf_node = "mid-tmc/subarray-leaf-node-csp/01"
tmc_sdp_subarray_leaf_node = "mid-tmc/subarray-leaf-node-sdp/01"
sdp_subarray1 = "mid-sdp/subarray/01"
csp_subarray1 = "mid-csp/subarray/01"
sdp_subarray2 = "mid-sdp/subarray/02"
csp_subarray2 = "mid-csp/subarray/02"
sdp_master = "mid-sdp/control/0"
csp_master = "mid-csp/control/0"
dish_master1 = "mid-dish/dish-manager/ska001"
dish_master2 = "mid-dish/dish-manager/ska036"
dish_master3 = "mid-dish/dish-manager/ska063"
dish_master4 = "mid-dish/dish-manager/ska100"
alarm_handler1 = "alarm/handler/01"
tmc_dish_leaf_node1 = "mid-tmc/leaf-node-dish/ska001"
tmc_dish_leaf_node2 = "mid-tmc/leaf-node-dish/ska036"
tmc_dish_leaf_node3 = "mid-tmc/leaf-node-dish/ska063"
tmc_dish_leaf_node4 = "mid-tmc/leaf-node-dish/ska100"
tmc_dish_pointing_device1 = "mid-tmc/dish-pointing/ska001"
tmc_dish_pointing_device2 = "mid-tmc/dish-pointing/ska036"
tmc_dish_pointing_device3 = "mid-tmc/dish-pointing/ska063"
tmc_dish_pointing_device4 = "mid-tmc/dish-pointing/ska100"
tmc_subarray_prefix = "mid-tmc/subarray"
tmc_csp_subarrayln_prefix = "mid-tmc/subarray-leaf-node-csp"
tmc_sdp_subarrayln_prefix = "mid-tmc/subarray-leaf-node-sdp"
sdp_subarray_prefix = "mid-sdp/subarray"
csp_subarray_prefix = "mid-csp/subarray"
sdp_queue_connector = "mid-sdp/queueconnector/01"
tmc_resource_monitor = "mid-tmc/resource-monitor/01"
COMMAND_COMPLETED = json.dumps([ResultCode.OK, "Command Completed"])

TIMEOUT = 100


DEVICE_HEALTH_STATE_OK_INFO = {
    tmc_csp_subarray_leaf_node: "OK",
    centralnode: "OK",
    tmc_csp_master_leaf_node: "OK",
    tmc_sdp_master_leaf_node: "OK",
    tmc_sdp_subarray_leaf_node: "OK",
}

# TODO use this as as list when multiple subarray considered in testing
ON_OFF_DEVICE_COMMAND_DICT = {
    "sdp_subarray": sdp_subarray1,
    "csp_subarray": csp_subarray1,
    "csp_master": csp_master,
    "tmc_subarraynode": tmc_subarraynode1,
    "sdp_master": sdp_master,
    "tmc_dish_leaf_node1": tmc_dish_leaf_node1,
    "tmc_dish_leaf_node2": tmc_dish_leaf_node2,
    "tmc_dish_leaf_node3": tmc_dish_leaf_node3,
    "tmc_dish_leaf_node4": tmc_dish_leaf_node4,
    "dish_master1": dish_master1,
    "dish_master2": dish_master2,
    "dish_master3": dish_master3,
    "dish_master4": dish_master4,
    "dish_master_list": [
        dish_master1,
        dish_master2,
        dish_master3,
        dish_master4,
    ],
    "central_node": centralnode,
    "tmc_csp_subarray_leaf_node": tmc_csp_subarray_leaf_node,
    "tmc_sdp_subarray_leaf_node": tmc_sdp_subarray_leaf_node,
}

DEVICE_STATE_STANDBY_INFO = {
    sdp_subarray1: ["DISABLE", "OFF"],
    sdp_master: ["DISABLE", "STANDBY", "OFF"],
    csp_master: ["DISABLE", "STANDBY", "OFF"],
    csp_subarray1: ["DISABLE", "OFF"],
    dish_master1: ["DISABLE", "STANDBY"],
    dish_master2: ["DISABLE", "STANDBY"],
    dish_master3: ["DISABLE", "STANDBY"],
    dish_master4: ["DISABLE", "STANDBY"],
}

DEVICE_STATE_ON_INFO = {
    sdp_subarray1: ["ON"],
    sdp_master: ["ON"],
    csp_master: ["ON"],
    csp_subarray1: ["ON"],
    centralnode: ["ON"],
    dish_master1: ["STANDBY"],
    dish_master2: ["STANDBY"],
    dish_master3: ["STANDBY"],
    dish_master4: ["STANDBY"],
}

DISH_MODE_STANDBYFP_INFO = {
    dish_master1: ["STANDBY_FP"],
    dish_master2: ["STANDBY_FP"],
    dish_master3: ["STANDBY_FP"],
    dish_master4: ["STANDBY_FP"],
}

DISH_MODE_STANDBYLP_INFO = {
    dish_master1: ["STANDBY_LP"],
    dish_master2: ["STANDBY_LP"],
    dish_master3: ["STANDBY_LP"],
    dish_master4: ["STANDBY_LP"],
}

DEVICE_OBS_STATE_EMPTY_INFO = {
    sdp_subarray1: ["EMPTY"],
    tmc_subarraynode1: ["EMPTY"],
    csp_subarray1: ["EMPTY"],
}

DEVICE_OBS_STATE_READY_INFO = {
    csp_subarray1: ["READY"],
    sdp_subarray1: ["READY"],
    tmc_subarraynode1: ["READY"],
}

DEVICE_OBS_STATE_CONFIGURING_INFO = {
    sdp_subarray1: ["CONFIGURING"],
    tmc_subarraynode1: ["CONFIGURING"],
    csp_subarray1: ["CONFIGURING"],
}

DEVICE_OBS_STATE_IDLE_INFO = {
    sdp_subarray1: ["IDLE"],
    tmc_subarraynode1: ["IDLE"],
    csp_subarray1: ["IDLE"],
}

DEVICE_STATE_OFF_INFO = {
    sdp_subarray1: ["OFF"],
    sdp_master: ["OFF"],
    csp_master: ["OFF"],
    csp_subarray1: ["OFF"],
    dish_master1: ["STANDBY"],
    dish_master2: ["STANDBY"],
    dish_master3: ["STANDBY"],
    dish_master4: ["STANDBY"],
}

DEVICE_OBS_STATE_ABORT_INFO = {
    sdp_subarray1: ["ABORTED"],
    tmc_subarraynode1: ["ABORTED"],
    csp_subarray1: ["ABORTED"],
}


DEVICE_OBS_STATE_ABORT_IN_EMPTY = {
    sdp_subarray1: ["ABORTED"],
    tmc_subarraynode1: ["ABORTED"],
}

DEVICE_OBS_STATE_ABORT_IN_EMPTY_SDP = {
    csp_subarray1: ["ABORTED"],
    tmc_subarraynode1: ["ABORTED"],
}

DEVICE_OBS_STATE_ABORT_IN_EMPTY_CSP = {
    sdp_subarray1: ["ABORTED"],
    tmc_subarraynode1: ["ABORTED"],
}

DEVICE_LIST_FOR_CHECK_DEVICES = [
    centralnode,
    csp_subarray1,
    sdp_subarray1,
    tmc_subarraynode1,
    tmc_csp_master_leaf_node,
    tmc_csp_subarray_leaf_node,
    tmc_sdp_master_leaf_node,
    tmc_sdp_subarray_leaf_node,
]

DEVICE_OBS_STATE_SCANNING_INFO = {
    sdp_subarray1: ["SCANNING"],
    tmc_subarraynode1: ["SCANNING"],
    csp_subarray1: ["SCANNING"],
}

INTERMEDIATE_STATE_DEFECT = {
    "enabled": True,
    "fault_type": FaultType.STUCK_IN_INTERMEDIATE_STATE,
    "error_message": "Device stuck in intermediate state",
    "result": ResultCode.FAILED,
    "intermediate_state": ObsState.RESOURCING,
}

INTERMEDIATE_CONFIGURING_OBS_STATE_DEFECT = {
    "enabled": True,
    "fault_type": FaultType.STUCK_IN_INTERMEDIATE_STATE,
    "error_message": "Device stuck in intermediate state",
    "result": ResultCode.FAILED,
    "intermediate_state": ObsState.CONFIGURING,
}

COMMAND_NOT_ALLOWED_DEFECT = {
    "enabled": True,
    "fault_type": FT.COMMAND_NOT_ALLOWED,
    "error_message": "Exception to test exception propagation",
    "result": ResultCode.FAILED,
}

READY_STATE_DEFECT = json.dumps(
    {
        "enabled": True,
        "fault_type": FaultType.STUCK_IN_INTERMEDIATE_STATE,
        "error_message": "Device stuck in intermediate state",
        "result": ResultCode.FAILED,
        "intermediate_state": ObsState.READY,
    }
)

IDLE_STATE_DEFECT = json.dumps(
    {
        "enabled": True,
        "fault_type": FaultType.STUCK_IN_INTERMEDIATE_STATE,
        "error_message": "Device stuck in intermediate state",
        "result": ResultCode.FAILED,
        "intermediate_state": ObsState.IDLE,
    }
)

OBS_STATE_RESOURCING_STUCK_DEFECT = {
    "enabled": True,
    "fault_type": FaultType.STUCK_IN_OBSTATE,
    "error_message": "Device stuck in Resourcing state",
    "result": ResultCode.FAILED,
    "intermediate_state": ObsState.RESOURCING,
}

INTERMEDIATE_FAULT_OBS_STATE_DEFECT = {
    "enabled": True,
    "fault_type": FaultType.STUCK_IN_INTERMEDIATE_STATE,
    "error_message": "Device stuck in intermediate state",
    "result": ResultCode.FAILED,
    "intermediate_state": ObsState.FAULT,
}


class CorrectionKey(IntEnum):
    """An enum class for correction keys"""

    MAINTAIN = 0
    UPDATE = 1
    RESET = 2


ABORT_COMPLETED = json.dumps([ResultCode.OK, "Abort command completed"])
DISH_ERROR_MESSAGE = (
    "Exception occurred on the following devices: "
    + f"{tmc_dish_leaf_node1.lower()}:"
)
TIMOUT_ERROR = "Timeout has occurred, command failed"

OBS_STATE_RESOURCING_STUCK_DEFECT = {
    "enabled": True,
    "fault_type": FaultType.STUCK_IN_OBSTATE,
    "error_message": "Device stuck in Resourcing state",
    "result": ResultCode.FAILED,
    "intermediate_state": ObsState.RESOURCING,
}

POINTING_STATE_READY_STUCK_DEFECT = {
    "enabled": True,
    "fault_type": FaultType.STUCK_IN_OBSTATE,
    "error_message": "Device stuck in Resourcing state",
    "result": ResultCode.FAILED,
    "intermediate_state": ObsState.RESOURCING,
}


OBS_STATE_CONFIGURING_STUCK_DEFECT = {
    "enabled": True,
    "fault_type": FaultType.STUCK_IN_OBSTATE,
    "error_message": "Device stuck in CONFIGURING obsState",
    "result": ResultCode.FAILED,
    "intermediate_state": ObsState.CONFIGURING,
}

INTERMEDIATE_OBSSTATE_EMPTY_DEFECT = {
    "enabled": True,
    "fault_type": FaultType.STUCK_IN_INTERMEDIATE_STATE,
    "error_message": "Device stuck in intermediate state",
    "result": ResultCode.FAILED,
    "intermediate_state": ObsState.EMPTY,
}

COMMAND_FAILED_WITH_EXCEPTION_OBSSTATE_EMPTY = {
    "enabled": True,
    "fault_type": FaultType.FAILED_RESULT,
    "error_message": "Default exception.",
    "result": ResultCode.FAILED,
    "target_obsstates": [ObsState.RESOURCING, ObsState.EMPTY],
}

ERROR_PROPAGATION_DEFECT = json.dumps(
    {
        "enabled": True,
        "fault_type": FaultType.LONG_RUNNING_EXCEPTION,
        "error_message": "Exception occurred, command failed.",
        "result": ResultCode.FAILED,
    }
)
FAILED_RESULT_DEFECT = json.dumps(
    {
        "enabled": True,
        "fault_type": FaultType.FAILED_RESULT,
        "error_message": "Device is defective, cannot process command",
        "result": ResultCode.FAILED,
    }
)

SDP_IN_FAULT = json.dumps(
    {
        "enabled": True,
        "fault_type": FaultType.SDP_FAULT,
        "error_message": "Exception occurred, command failed.",
        "result": ResultCode.FAILED,
    }
)
SDP_BACK_TO_INITIAL_STATE = json.dumps(
    {
        "enabled": True,
        "fault_type": FaultType.SDP_BACK_TO_INITIAL_STATE,
        "error_message": "Exception occurred, command failed.",
        "result": ResultCode.FAILED,
    }
)
RESET_DEFECT = json.dumps(
    {
        "enabled": False,
        "fault_type": FaultType.FAILED_RESULT,
        "error_message": "Default exception.",
        "result": ResultCode.FAILED,
    }
)
POINTING_OFFSETS = np.array(
    [
        [
            "SKA001",
            -4.115211938625473,
            69.9725295732531,
            -7.090356031104502,
            104.10028693155607,
            70.1182176899719,
            78.8829949012184,
            95.49061976199042,
            729.5782881970024,
            119.27311545171803,
            1065.4074085647912,
            0.9948872678443994,
            0.8441090109163307,
        ],
        [
            "SKA036",
            -4.115211938625473,
            69.10028693155607,
            -7.5782881970024,
            104.10028693155607,
            70.1182176899719,
            78.8829949012184,
            95.49061976199042,
            729.5782881970024,
            119.27311545171803,
            1065.4074085647912,
            0.9948872678443994,
            0.8441090109163307,
        ],
    ]
)

COMMAND_FAILED_WITH_EXCEPTION_OBSSTATE_IDLE = {
    "enabled": True,
    "fault_type": FaultType.FAILED_RESULT,
    "error_message": "Default exception.",
    "result": ResultCode.FAILED,
    "target_obsstates": [ObsState.RESOURCING, ObsState.IDLE],
}

COMMAND_FAILED_WITH_EXCEPTION_OBSSTATE_CONFIGURING_IDLE = {
    "enabled": True,
    "fault_type": FaultType.FAILED_RESULT,
    "error_message": "Default exception.",
    "result": ResultCode.FAILED,
    "target_obsstates": [ObsState.CONFIGURING, ObsState.IDLE],
}

COMMAND_NOT_ALLOWED_DEFECT_BEFORE_QUEUING = {
    "enabled": True,
    "fault_type": FaultType.COMMAND_NOT_ALLOWED_BEFORE_QUEUING,
    "error_message": "Command is not allowed",
    "result": ResultCode.FAILED,
}


device_dict = {
    "csp_master": csp_master,
    "tmc_subarraynode": tmc_subarraynode1,
    "sdp_master": sdp_master,
    "dish_master1": dish_master1,
    "dish_master2": dish_master2,
    "dish_master3": dish_master3,
    "dish_master4": dish_master4,
    "dish_master_list": [
        dish_master1,
        dish_master2,
        dish_master3,
        dish_master4,
    ],
    "dish_leaf_node_list": [
        tmc_dish_leaf_node1,
        tmc_dish_leaf_node2,
        tmc_dish_leaf_node3,
        tmc_dish_leaf_node4,
    ],
    "sdp_subarray": sdp_subarray1,
    "csp_subarray": csp_subarray1,
    "sdp_subarray_leaf_node": tmc_sdp_subarray_leaf_node,
    "csp_subarray_leaf_node": tmc_csp_subarray_leaf_node,
    "csp_master_leaf_node": tmc_csp_master_leaf_node,
}

SIMULATOR_DEVICE_FQDN_DICT = {
    SimulatorDeviceType.MID_SDP_DEVICE: [sdp_subarray1],
    SimulatorDeviceType.MID_CSP_DEVICE: [csp_subarray1],
    SimulatorDeviceType.MID_SDP_DEVICE2: [sdp_subarray2],
    SimulatorDeviceType.MID_CSP_DEVICE2: [csp_subarray2],
    SimulatorDeviceType.DISH_DEVICE: [
        dish_master1,
        dish_master2,
        dish_master3,
        dish_master4,
    ],
    SimulatorDeviceType.MID_SDP_MASTER_DEVICE: [sdp_master],
    SimulatorDeviceType.MID_CSP_MASTER_DEVICE: [csp_master],
}

DEFAULT_DISH_VCC_CONFIG = {
    "interface": "https://schema.skao.int/ska-mid-cbf-initsysparam/1.0",
    "tm_data_sources": [
        "car://gitlab.com/ska-telescope/ska-telmodel-data?"
        + "ska-sdp-tmlite-repository-1.0.0#tmdata"
    ],
    "tm_data_filepath": (
        "instrument/ska1_mid_psi/ska-mid-cbf-system-parameters.json"
    ),
}

DEFAULT_DISH_VALIDATION_STATUS = {
    "dish": "ALL DISH OK",
    tmc_csp_master_leaf_node: (
        "TMC and CSP Master Dish Vcc Version " + "is Same"
    ),
}

DISH_001_CALIBRATION_DATA = [1.1, 1.2, 1.3]
DISH_036_CALIBRATION_DATA = [2.1, 2.2, 2.3]
RESET_OFFSETS = [0.0, 0.0]
ABORT_COMPLETED = json.dumps([ResultCode.OK, "Abort command completed"])


FAILED_DEFECT = json.dumps(
    {
        "enabled": True,
        "fault_type": FaultType.FAILED_RESULT,
        "error_message": "Default exception.",
        "result": ResultCode.FAILED,
    }
)

INTERMEDIATE_READY_STATE_DEFECT = json.dumps(
    {
        "enabled": True,
        "fault_type": FaultType.STUCK_IN_INTERMEDIATE_STATE,
        "error_message": "Device stuck in intermediate state",
        "result": ResultCode.FAILED,
        "intermediate_state": ObsState.READY,
    }
)

INTERMEDIATE_RESOURCING_STATE_DEFECT = json.dumps(
    {
        "enabled": True,
        "fault_type": FaultType.STUCK_IN_INTERMEDIATE_STATE,
        "error_message": "Device stuck in intermediate state",
        "result": ResultCode.FAILED,
        "intermediate_state": ObsState.RESOURCING,
    }
)

INTERMEDIATE_CONFIGURING_STATE_DEFECT = json.dumps(
    {
        "enabled": True,
        "fault_type": FaultType.STUCK_IN_INTERMEDIATE_STATE,
        "error_message": "Device stuck in intermediate state",
        "result": ResultCode.FAILED,
        "intermediate_state": ObsState.CONFIGURING,
    }
)

INTERMEDIATE_CONFIGURING_STATE_DEFECT_DISH = json.dumps(
    {
        "enabled": True,
        "fault_type": FaultType.STUCK_IN_INTERMEDIATE_STATE,
        "error_message": "Device stuck in intermediate state",
        "result": ResultCode.FAILED,
        "intermediate_state": PointingState.TRACK,
    }
)

INTERMEDIATE_READY_STATE_DEFECT_DISH = {
    "enabled": True,
    "fault_type": FaultType.STUCK_IN_INTERMEDIATE_STATE,
    "error_message": "Device stuck in intermediate state",
    "result": ResultCode.FAILED,
    "intermediate_state": PointingState.READY,
}

INTERMEDIATE_TRACK_STATE_DEFECT_DISH = {
    "enabled": True,
    "fault_type": FaultType.STUCK_IN_INTERMEDIATE_STATE,
    "error_message": "Device stuck in intermediate state",
    "result": ResultCode.FAILED,
    "intermediate_state": PointingState.TRACK,
}

INTERMEDIATE_DISH_MODE_STATE_DEFECT_DISH = {
    "enabled": True,
    "fault_type": FaultType.STUCK_IN_INTERMEDIATE_STATE,
    "error_message": "Device stuck in intermediate state",
    "result": ResultCode.FAILED,
    "intermediate_state": DishMode.CONFIG,
    "is_dish_mode": True,
}

INTERMEDIATE_SLEW_STATE_DEFECT_DISH = {
    "enabled": True,
    "fault_type": FaultType.STUCK_IN_INTERMEDIATE_STATE,
    "error_message": "Device stuck in intermediate state",
    "result": ResultCode.FAILED,
    "intermediate_state": PointingState.SLEW,
}

INTERMEDIATE_SCANNING_STATE_DEFECT = json.dumps(
    {
        "enabled": True,
        "fault_type": FaultType.STUCK_IN_INTERMEDIATE_STATE,
        "error_message": "Device stuck in intermediate state",
        "result": ResultCode.FAILED,
        "intermediate_state": ObsState.SCANNING,
    }
)
EVENT_DEFECT = json.dumps(
    {"enabled": True, "fault_type": FaultType.EVENT_NOT_RECEIVED}
)
RECEIVE_ADDRESSES = json.dumps(
    {
        "science_A": {
            "vis0": {
                "function": "visibilities",
                "host": [[0, "192.168.0.1"], [2000, "192.168.0.2"]],
                "port": [[0, 9000], [20, 9001]],
            }
        },
        "target:a": {
            "vis0": {
                "function": "visibilities",
                "host": [[0, "192.168.0.1"], [2000, "192.168.0.2"]],
                "port": [[0, 9000], [20, 9001]],
            }
        },
        "calibration:b": {
            "vis0": {
                "function": "visibilities",
                "host": [[0, "192.168.0.1"], [2000, "192.168.0.2"]],
                "port": [[0, 9000], [20, 9001]],
            }
        },
    }
)


expected_json_spfrx_param_case_all_dishes = {
    "dish": {
        "receiver_band": "1",
        "sub_band": 1,
        "spfrx_processing_parameters": [
            {
                "dishes": ["all"],
                "sync_pps": True,
                "attenuation_pol_x": 10,
                "attenuation_pol_y": 10,
                "saturation_threshold": 0.6,
                "noise_diode": {
                    "psuedo_random": {
                        "binary_polynomial": 1,
                        "seed": 1,
                        "dwell": 1,
                    },
                    "periodic": {
                        "period": 1,
                        "duty_cycle": 1,
                        "phase_shift": 1,
                    },
                },
            }
        ],
    }
}

expected_json_spfrx_param_case_single_parameter_per_dish = {
    "dish": {
        "receiver_band": "1",
        "sub_band": 1,
        "spfrx_processing_parameters": [
            {
                "dishes": ["SKA001"],
                "sync_pps": True,
                "attenuation_1_pol_x": 20,
                "attenuation_1_pol_y": 20,
                "attenuation_2_pol_x": 10,
                "attenuation_2_pol_y": 10,
                "saturation_threshold": 0.7,
                "noise_diode": {
                    "psuedo_random": {
                        "binary_polynomial": 2,
                        "seed": 2,
                        "dwell": 2,
                    },
                    "periodic": {
                        "period": 1,
                        "duty_cycle": 1,
                        "phase_shift": 1,
                    },
                },
            },
            {
                "dishes": ["SKA036"],
                "sync_pps": True,
                "attenuation_pol_x": 10,
                "attenuation_pol_y": 10,
                "saturation_threshold": 0.6,
                "noise_diode": {
                    "psuedo_random": {
                        "binary_polynomial": 1,
                        "seed": 1,
                        "dwell": 1,
                    },
                    "periodic": {
                        "period": 1,
                        "duty_cycle": 1,
                        "phase_shift": 1,
                    },
                },
            },
        ],
    }
}

expected_json_spfrx_param_case_multiple_dish_same_parameter = {
    "dish": {
        "receiver_band": "1",
        "sub_band": 1,
        "spfrx_processing_parameters": [
            {
                "dishes": ["SKA001", "SKA036"],
                "sync_pps": True,
                "attenuation_pol_x": 10,
                "attenuation_pol_y": 10,
                "saturation_threshold": 0.6,
                "noise_diode": {
                    "psuedo_random": {
                        "binary_polynomial": 1,
                        "seed": 1,
                        "dwell": 1,
                    },
                    "periodic": {
                        "period": 1,
                        "duty_cycle": 1,
                        "phase_shift": 1,
                    },
                },
            }
        ],
    }
}

expected_json_spfrx_param_case_all_different = {
    "dish": {
        "receiver_band": "1",
        "sub_band": 1,
        "spfrx_processing_parameters": [
            {
                "dishes": ["SKA001"],
                "sync_pps": True,
                "attenuation_pol_x": 15,
                "attenuation_pol_y": 12,
                "saturation_threshold": 0.65,
                "noise_diode": {
                    "psuedo_random": {
                        "binary_polynomial": 3,
                        "seed": 7,
                        "dwell": 4,
                    },
                    "periodic": {
                        "period": 8,
                        "duty_cycle": 1,
                        "phase_shift": 2,
                    },
                },
            },
            {
                "dishes": ["SKA036"],
                "sync_pps": False,
                "attenuation_1_pol_x": 25,
                "attenuation_1_pol_y": 22,
                "attenuation_2_pol_x": 5,
                "attenuation_2_pol_y": 8,
                "saturation_threshold": 0.55,
                "noise_diode": {
                    "psuedo_random": {
                        "binary_polynomial": 1,
                        "seed": 1,
                        "dwell": 1,
                    },
                    "periodic": {
                        "period": 10,
                        "duty_cycle": 1,
                        "phase_shift": 3,
                    },
                },
            },
            {
                "dishes": ["SKA063"],
                "sync_pps": True,
                "attenuation_pol_x": 18,
                "attenuation_pol_y": 18,
                "saturation_threshold": 0.6,
                "noise_diode": {
                    "psuedo_random": {
                        "binary_polynomial": 5,
                        "seed": 9,
                        "dwell": 2,
                    },
                    "periodic": {
                        "period": 1,
                        "duty_cycle": 1,
                        "phase_shift": 1,
                    },
                },
            },
            {
                "dishes": ["SKA100"],
                "sync_pps": True,
                "attenuation_pol_x": 10,
                "attenuation_pol_y": 10,
                "saturation_threshold": 0.7,
                "noise_diode": {
                    "psuedo_random": {
                        "binary_polynomial": 2,
                        "seed": 2,
                        "dwell": 2,
                    },
                    "periodic": {
                        "period": 1,
                        "duty_cycle": 1,
                        "phase_shift": 1,
                    },
                },
            },
        ],
    }
}
