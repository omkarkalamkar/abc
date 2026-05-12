import json
import logging
import os
from typing import List, Tuple

from ska_control_model import ObsState, ResultCode
from ska_ser_logging import configure_logging
from ska_tango_base.control_model import HealthState
from tango import DeviceProxy, DevState
from tango.db import Database

from tests.resources.test_harness.central_node import CentralNodeWrapper
from tests.resources.test_harness.event_recorder import EventRecorder
from tests.resources.test_harness.helpers import (
    SIMULATED_DEVICES_DICT,
    generate_eb_pb_ids,
    wait_csp_master_off,
)
from tests.resources.test_harness.utils.common_utils import JsonFactory
from tests.resources.test_harness.utils.enums import DishMode
from tests.resources.test_harness.utils.sync_decorators import (
    sync_abort,
    sync_assign_resources,
    sync_load_dish_cfg,
    sync_release_resources,
    sync_restart,
    sync_set_to_off,
    sync_set_to_standby,
)
from tests.resources.test_harness.utils.wait_helpers import Waiter
from tests.resources.test_support.common_utils.common_helpers import Resource
from tests.resources.test_support.constant import (
    COMMAND_COMPLETED,
    DEFAULT_DISH_VALIDATION_STATUS,
    DEFAULT_DISH_VCC_CONFIG,
    centralnode,
    csp_master,
    csp_subarray1,
    device_dict,
    dish_master1,
    dish_master2,
    dish_master3,
    dish_master4,
    sdp_master,
    sdp_subarray1,
    tmc_csp_master_leaf_node,
    tmc_csp_subarrayln_prefix,
    tmc_dish_leaf_node1,
    tmc_dish_leaf_node2,
    tmc_dish_leaf_node3,
    tmc_dish_leaf_node4,
    tmc_sdp_master_leaf_node,
    tmc_sdp_subarrayln_prefix,
    tmc_subarray_prefix,
    tmc_subarraynode1,
)

configure_logging(logging.DEBUG)
LOGGER = logging.getLogger(__name__)

REAL_DISH1_FQDN = os.getenv("DISH_NAME_1")
REAL_DISH36_FQDN = os.getenv("DISH_NAME_36")
REAL_DISH63_FQDN = os.getenv("DISH_NAME_63")
REAL_DISH100_FQDN = os.getenv("DISH_NAME_100")


class CentralNodeWrapperMid(CentralNodeWrapper):
    """A wrapper class to implement common tango specific details
    and standard set of commands for TMC Mid CentralNode,
    defined by the SKA Control Model."""

    def __init__(self) -> None:
        super().__init__()
        self.central_node = DeviceProxy(centralnode)
        self.central_node.set_timeout_millis(5000)
        self.subarray_node = DeviceProxy(tmc_subarraynode1)
        self.subarray_node.set_timeout_millis(5000)
        self.csp_master_leaf_node = DeviceProxy(tmc_csp_master_leaf_node)
        self.sdp_master_leaf_node = DeviceProxy(tmc_sdp_master_leaf_node)
        self.sdp_master = DeviceProxy(sdp_master)
        self.subarray_devices = {
            "csp_subarray": DeviceProxy(csp_subarray1),
            "sdp_subarray": DeviceProxy(sdp_subarray1),
        }

        self.csp_master = DeviceProxy(csp_master)
        if (
            SIMULATED_DEVICES_DICT["csp_and_sdp"]
            or SIMULATED_DEVICES_DICT["sdp"]
        ) and not SIMULATED_DEVICES_DICT["all_mocks"]:
            dish_fqdn001 = REAL_DISH1_FQDN
            dish_fqdn036 = REAL_DISH36_FQDN
            dish_fqdn063 = REAL_DISH63_FQDN
            dish_fqdn100 = REAL_DISH100_FQDN

            # creating spfrx device fqdn
            self.spfrx_fqdn = dish_fqdn001.replace(
                dish_master1,
                "mid-dish/simulator-spfrx/SKA001",
            )
            spfrx_proxy = DeviceProxy(self.spfrx_fqdn)

            # Create Dish1 admin device proxy
            spfrx1_admin_dev_name = spfrx_proxy.adm_name()
            self.spfrx1_admin_dev_proxy = DeviceProxy(spfrx1_admin_dev_name)

            # Create database object for TMC TANGO DB
            self.db = Database()

            # Create database object for Dish1 TANGO DB
            dish1_tango_host = dish_fqdn001.split("/")[2]
            dish1_host = dish1_tango_host.split(":")[0]
            dish1_port = dish1_tango_host.split(":")[1]
            self.dish1_db = Database(dish1_host, dish1_port)

            # Get the Dish1 device class and server
            dish1_info = self.dish1_db.get_device_info(dish_master1)
            self.dish1_dev_class = dish1_info.class_name
            self.dish1_dev_server = dish1_info.ds_full_name

            # Get the spfrx1 device class and server
            spfrx1_info = self.dish1_db.get_device_info(
                "mid-dish/simulator-spfrx/SKA001"
            )
            self.spfrx1_dev_class = spfrx1_info.class_name
            self.spfrx1_dev_server = spfrx1_info.ds_full_name

        else:
            dish_fqdn001 = dish_master1
            dish_fqdn036 = dish_master2
            dish_fqdn063 = dish_master3
            dish_fqdn100 = dish_master4

        self.dish_master_list = [
            DeviceProxy(dish_fqdn001),
            DeviceProxy(dish_fqdn036),
            DeviceProxy(dish_fqdn063),
            DeviceProxy(dish_fqdn100),
        ]

        self.dish_master_dict = {
            "SKA001": DeviceProxy(dish_fqdn001),
            "SKA036": DeviceProxy(dish_fqdn036),
            "SKA063": DeviceProxy(dish_fqdn063),
            "SKA100": DeviceProxy(dish_fqdn100),
        }
        self.dish_leaf_node_list = [
            DeviceProxy(tmc_dish_leaf_node1),
            DeviceProxy(tmc_dish_leaf_node2),
            DeviceProxy(tmc_dish_leaf_node3),
            DeviceProxy(tmc_dish_leaf_node4),
        ]

        self.central_node.set_timeout_millis(5000)
        # Increase the timeout for Dish Leaf Node devices
        for dish_leaf_node in self.dish_leaf_node_list:
            dish_leaf_node.set_timeout_millis(5000)

        self.dish_leaf_node_dict = {
            "SKA001": DeviceProxy(tmc_dish_leaf_node1),
            "SKA036": DeviceProxy(tmc_dish_leaf_node2),
            "SKA063": DeviceProxy(tmc_dish_leaf_node3),
            "SKA100": DeviceProxy(tmc_dish_leaf_node4),
        }
        # Create Dish1 admin device proxy
        self.dish1_admin_dev_name = self.dish_master_list[0].adm_name()
        self.dish1_admin_dev_proxy = DeviceProxy(self.dish1_admin_dev_name)

        # Create Dish1 leaf node admin device proxy
        self.dish1_leaf_admin_dev_name = self.dish_leaf_node_list[0].adm_name()
        self.dish1_leaf_admin_dev_proxy = DeviceProxy(
            self.dish1_leaf_admin_dev_name
        )

        self._state = DevState.OFF
        self.json_factory = JsonFactory()
        self.release_input = (
            self.json_factory.create_centralnode_configuration(
                "release_resources_mid"
            )
        )
        if (
            SIMULATED_DEVICES_DICT["sdp_and_dish"]
            or SIMULATED_DEVICES_DICT["sdp"]
        ) and not SIMULATED_DEVICES_DICT["all_mocks"]:
            device_dict["cbf_subarray1"] = "mid_csp_cbf/sub_elt/subarray_01"
            device_dict["cbf_controller"] = "mid_csp_cbf/sub_elt/controller"

        device_dict["dish_master_list"] = self.dish_master_list
        device_dict["dish_leaf_node_list"] = self.dish_leaf_node_list
        self.wait = Waiter(**device_dict)

    @property
    def state(self) -> DevState:
        """TMC CentralNode operational state"""
        self._state = Resource(self.central_node).get("State")
        return self._state

    @state.setter
    def state(self, value: DevState):
        """Sets value for TMC CentralNode operational state

        Args:
            value (DevState): operational state value
        """
        self._state = value

    @property
    def IsDishVccConfigSet(self):
        """Return DishVccConfigSet flag"""
        return self.central_node.isDishVccConfigSet

    @property
    def DishVccValidationStatus(self):
        """Current dish vcc validation status of central node"""
        return self.central_node.DishVccValidationStatus

    @property
    def telescope_health_state(self) -> HealthState:
        """Telescope health state representing overall health of telescope"""
        self._telescope_health_state = Resource(self.central_node).get(
            "telescopeHealthState"
        )
        return self._telescope_health_state

    @telescope_health_state.setter
    def telescope_health_state(self, value: HealthState) -> None:
        """Telescope health state representing overall health of telescope

        Args:
            value (HealthState): telescope health state value
        """
        self._telescope_health_state = value

    @property
    def telescope_state(self) -> DevState:
        """Telescope state representing overall state of telescope"""

        self._telescope_state = Resource(self.central_node).get(
            "telescopeState"
        )
        return self._telescope_state

    @telescope_state.setter
    def telescope_state(self, value: DevState) -> None:
        """Telescope state representing overall state of telescope

        Args:
            value (DevState): telescope state value
        """
        self._telescope_state = value

    def set_subarray_id(self, requested_subarray_id: str) -> None:
        """This method creates subarray devices for the requested subarray
        id"""
        subarray_id = str(requested_subarray_id).zfill(2)
        self.subarray_node = DeviceProxy(
            f"{tmc_subarray_prefix}/{subarray_id}"
        )
        self.subarray_devices = {
            "csp_subarray": DeviceProxy(f"mid-csp/subarray/{subarray_id}"),
            "sdp_subarray": DeviceProxy(f"mid-sdp/subarray/{subarray_id}"),
        }
        self.csp_subarray_leaf_node = DeviceProxy(
            f"{tmc_csp_subarrayln_prefix}/{subarray_id}"
        )
        self.sdp_subarray_leaf_node = DeviceProxy(
            f"{tmc_sdp_subarrayln_prefix}/{subarray_id}"
        )

    def get_track_table_for_dish_id(
        self, dish_id: str = "SKA001"
    ) -> List[float]:
        """Return the programTrackTable value for given dish ID"""
        return (
            self.dish_master_dict[dish_id]
            .read_attribute("programTrackTable")
            .value
        )

    def load_dish_vcc_configuration(
        self, dish_vcc_config: str
    ) -> Tuple[ResultCode, str]:
        """Invoke LoadDishCfg command on central Node
        :param dish_vcc_config: Dish vcc configuration json string
        """
        result, message = self.central_node.LoadDishCfg(dish_vcc_config)
        return result, message

    def _reset_sys_param_and_k_value(self) -> None:
        """Reset sysParam and sourceSysParam attribute of csp master
        reset kValue of Dish master
        """
        if (
            SIMULATED_DEVICES_DICT["csp_and_dish"]
            or SIMULATED_DEVICES_DICT["all_mocks"]
        ):
            for mock_device in self.dish_master_list:
                mock_device.SetKValue(0)

        if (
            SIMULATED_DEVICES_DICT["csp_and_dish"]
            or SIMULATED_DEVICES_DICT["all_mocks"]
        ):
            self.csp_master.ResetSysParams()

    def _clear_command_call_and_transition_data(
        self, clear_transition: bool = False
    ) -> None:
        """Clears the command call data"""
        if SIMULATED_DEVICES_DICT["all_mocks"]:
            for sim_device in [
                csp_subarray1,
                sdp_subarray1,
                dish_master1,
                dish_master2,
                dish_master3,
                dish_master4,
            ]:
                device = DeviceProxy(sim_device)
                device.set_timeout_millis(5000)
                device.ClearCommandCallInfo()
                if clear_transition:
                    device.ResetTransitions()

    def move_to_on(self) -> None:
        """
        A method to invoke TelescopeOn command to
        put telescope in ON state
        """
        LOGGER.info("Starting up the Telescope")
        LOGGER.info(f"Received simulated devices: {SIMULATED_DEVICES_DICT}")
        if SIMULATED_DEVICES_DICT["all_mocks"]:
            LOGGER.info("Invoking TelescopeOn() with all Mocks")
            self.central_node.TelescopeOn()
            self.set_csp_subarray_state(DevState.ON)

        elif SIMULATED_DEVICES_DICT["csp_and_sdp"]:
            LOGGER.info("Invoking TelescopeOn() on simulated csp and sdp")
            self.central_node.TelescopeOn()
            self.set_csp_subarray_state(DevState.ON)

        elif SIMULATED_DEVICES_DICT["csp_and_dish"]:
            LOGGER.info("Invoking TelescopeOn() on simulated csp and Dish")
            self.central_node.TelescopeOn()
            self.set_csp_subarray_state(DevState.ON)

        elif SIMULATED_DEVICES_DICT["sdp_and_dish"]:
            LOGGER.info("Invoking TelescopeOn() on simulated sdp and dish")
            if self.csp_master.adminMode != 0:
                self.csp_master.adminMode = 0
            wait_csp_master_off()
            self.central_node.TelescopeOn()
        elif SIMULATED_DEVICES_DICT["sdp"]:
            LOGGER.info("Invoking TelescopeOn() on simulated sdp")
            if self.csp_master.adminMode != 0:
                self.csp_master.adminMode = 0
            wait_csp_master_off()
            self.central_node.TelescopeOn()
        else:
            LOGGER.info("Invoke TelescopeOn() on all real sub-systems")
            self.central_node.TelescopeOn()

    @sync_set_to_off(device_dict=device_dict)
    def move_to_off(self) -> None:
        """
        A method to invoke TelescopeOff command to
        put telescope in OFF state

        """
        if SIMULATED_DEVICES_DICT["all_mocks"]:
            LOGGER.info("Invoking TelescopeOff() with all Mocks")
            self.central_node.TelescopeOff()
            self.set_csp_subarray_state(DevState.OFF)

        elif SIMULATED_DEVICES_DICT["csp_and_sdp"]:
            LOGGER.info("Invoking TelescopeOff() on simulated csp and sdp")
            self.central_node.TelescopeOff()
            self.set_csp_subarray_state(DevState.OFF)

        elif SIMULATED_DEVICES_DICT["csp_and_dish"]:
            LOGGER.info("Invoking TelescopeOff() on simulated csp and Dish")
            self.central_node.TelescopeOff()
            self.set_csp_subarray_state(DevState.OFF)

        elif SIMULATED_DEVICES_DICT["sdp_and_dish"]:
            LOGGER.info("Invoking TelescopeOff() on simulated sdp and dish")
            self.central_node.TelescopeOff()
        elif SIMULATED_DEVICES_DICT["sdp"]:
            LOGGER.info("Invoking TelescopeOff() on simulated sdp")
            self.central_node.TelescopeOff()
        else:
            LOGGER.info("Invoke TelescopeOff() with all real sub-systems")
            self.central_node.TelescopeOff()

    @sync_set_to_standby(device_dict=device_dict)
    def set_standby(self) -> None:
        """
        A method to invoke TelescopeStandby command to
        put telescope in STANDBY state

        """
        LOGGER.info("Putting Telescope in Standby state")
        if SIMULATED_DEVICES_DICT["all_mocks"]:
            LOGGER.info("Invoking TelescopeStandBy() with all Mocks")
            self.central_node.TelescopeStandBy()
            self.set_csp_subarray_state(DevState.OFF)

        elif SIMULATED_DEVICES_DICT["csp_and_sdp"]:
            LOGGER.info("Invoking TelescopeStandBy() on simulated csp and sdp")
            self.central_node.TelescopeStandBy()
            self.set_csp_subarray_state(DevState.OFF)

        elif SIMULATED_DEVICES_DICT["csp_and_dish"]:
            LOGGER.info(
                "Invoking TelescopeStandBy() on simulated csp and Dish"
            )
            self.central_node.TelescopeStandBy()
            self.set_csp_subarray_state(DevState.OFF)

        elif SIMULATED_DEVICES_DICT["sdp_and_dish"]:
            LOGGER.info(
                "Invoking TelescopeStandBy() on simulated sdp and dish"
            )
            self.central_node.TelescopeStandBy()
        elif SIMULATED_DEVICES_DICT["sdp"]:
            self.central_node.TelescopeStandBy()
        else:
            LOGGER.info("Invoke TelescopeStandBy() with all real sub-systems")
            self.central_node.TelescopeStandBy()

    @sync_assign_resources(device_dict=device_dict)
    def store_resources(
        self, assign_json: str, is_update_eb_id_required: bool = True
    ) -> Tuple[ResultCode, str]:
        """Invoke Assign Resource command on central Node
        Args:
            assign_json (str): Assign resource input json
        """
        input_json = json.loads(assign_json)
        if is_update_eb_id_required:
            generate_eb_pb_ids(input_json)
        result, message = self.central_node.AssignResources(
            json.dumps(input_json)
        )
        LOGGER.info("Invoked AssignResources on CentralNode")
        return result, message

    @sync_release_resources(device_dict=device_dict, timeout=500)
    def invoke_release_resources(
        self, input_string: str
    ) -> Tuple[ResultCode, str]:
        """Invoke Release Resource command on central Node
        Args:
            input_string (str): Release resource input json
        """
        result, message = self.central_node.ReleaseResources(input_string)
        return result, message

    @sync_abort(device_dict=device_dict)
    def subarray_abort(self) -> Tuple[ResultCode, str]:
        """Invoke Abort command on subarray Node"""
        result, message = self.subarray_node.Abort()
        return result, message

    @sync_restart(device_dict=device_dict)
    def subarray_restart(self) -> Tuple[ResultCode, str]:
        """Invoke Restart command on subarray Node"""
        result, message = self.subarray_node.Restart()
        return result, message

    def _reset_health_state_for_mock_devices(self) -> None:
        """Reset Mock devices"""
        if SIMULATED_DEVICES_DICT["csp_and_sdp"]:
            for mock_device in [
                self.sdp_master,
                self.csp_master,
            ]:
                mock_device.SetDirectHealthState(HealthState.UNKNOWN)
        elif SIMULATED_DEVICES_DICT["csp_and_dish"]:
            self.csp_master.SetDirectHealthState(HealthState.UNKNOWN)
            for mock_device in self.dish_master_list:
                mock_device.SetDirectHealthState(HealthState.UNKNOWN)
        elif SIMULATED_DEVICES_DICT["sdp_and_dish"]:
            self.sdp_master.SetDirectHealthState(HealthState.UNKNOWN)
            for mock_device in self.dish_master_list:
                mock_device.SetDirectHealthState(HealthState.UNKNOWN)
        elif SIMULATED_DEVICES_DICT["sdp"]:
            self.sdp_master.SetDirectHealthState(HealthState.UNKNOWN)
        elif SIMULATED_DEVICES_DICT["all_mocks"]:
            for mock_device in [
                self.sdp_master,
                self.csp_master,
            ]:
                mock_device.SetDirectHealthState(HealthState.UNKNOWN)
            for mock_device in self.dish_master_list:
                if mock_device.healthstate != HealthState.UNKNOWN:
                    mock_device.SetDirectHealthState(HealthState.UNKNOWN)
        else:
            LOGGER.info("No devices to reset healthState")

    def perform_action(
        self, command_name: str, input_json: str
    ) -> Tuple[ResultCode, str]:
        """Execute provided command on centralnode
        Args:
            command_name (str): Name of command to execute
            input_json (str): Json send as input to execute command
        """

        result, message = self.central_node.command_inout(
            command_name, input_json
        )
        return result, message

    def set_csp_subarray_state(self, subarray_state: DevState) -> None:
        """
        A method to set the State on mock CSP Subarray device.
        Args:
            subarray_state: DevState - subarray state value for
                                        CSP Subarray
        """
        device_to_on_list = [
            self.subarray_devices.get("csp_subarray"),
        ]
        for device in device_to_on_list:
            device_proxy = DeviceProxy(device)
            device_proxy.SetDirectState(subarray_state)

    @sync_load_dish_cfg(device_dict=device_dict)
    def _load_default_dish_vcc_config(self):
        """Load Default Dish Vcc config"""
        result, message = self.load_dish_vcc_configuration(
            json.dumps(DEFAULT_DISH_VCC_CONFIG)
        )
        return result, message

    def set_values_on_device(
        self, subarray_state: DevState, device_list, dish_mode: DishMode = None
    ):
        """Set Device to ON"""
        for device in device_list:
            device_proxy = DeviceProxy(device)
            device_proxy.SetDirectState(subarray_state)

        # If Dish master provided then set it to standby
        if self.dish_master_list and dish_mode:
            for device in self.dish_master_list:
                device.SetDirectDishMode(dish_mode)

    def tear_down(self) -> None:
        """Handle Tear down of central Node"""
        # reset HealthState.UNKNOWN for mock devices
        self._reset_health_state_for_mock_devices()
        self.set_subarray_id("1")
        self.tear_down_subarray()
        self.set_subarray_id("2")
        self.tear_down_subarray()

        LOGGER.info("telescope_state - %s", self.telescope_state)
        if self.telescope_state != "OFF":
            if (SIMULATED_DEVICES_DICT["sdp"]) and not SIMULATED_DEVICES_DICT[
                "all_mocks"
            ]:
                LOGGER.info("Tear down is not required.")

            else:
                LOGGER.info("Moving to Off State")
                self.move_to_off()

            self._clear_command_call_and_transition_data(clear_transition=True)
            # if source dish vcc config is empty or not matching
            # with default
            # dish vcc then load default dish vcc config
            # CSP_SIMULATION_ENABLED condition will be removed after
            # testing with real csp
            if (
                not self.csp_master_leaf_node.sourceDishVccConfig
                or json.loads(self.csp_master_leaf_node.sourceDishVccConfig)
                != DEFAULT_DISH_VCC_CONFIG
                or json.loads(self.central_node.DishVccValidationStatus)
                != DEFAULT_DISH_VALIDATION_STATUS
            ):
                _, unique_id = self._load_default_dish_vcc_config()
                event_recorder = EventRecorder()
                event_recorder.subscribe_event(
                    self.central_node, "longRunningCommandResult"
                )
                assert event_recorder.has_change_event_occurred(
                    self.central_node,
                    "longRunningCommandResult",
                    (unique_id[0], COMMAND_COMPLETED),
                )
                event_recorder.clear_events()

            LOGGER.info("longRunningCommandResult for Dish VCC verified")
        LOGGER.info("Tear Down complete")

    def tear_down_subarray(self) -> None:
        """Handle Tear down of central Node"""
        try:
            Subarray_node_obsstate = self.subarray_node.obsState
            LOGGER.info(
                f"Calling tear down for {self.subarray_node}'s \
                    {Subarray_node_obsstate} obsstate."
            )
            if self.subarray_node.obsState == ObsState.IDLE:
                LOGGER.info("Calling Release Resource on centralnode")
                release_data = json.loads(self.release_input)
                release_data["subarray_id"] = int(
                    self.subarray_node.dev_name().split("/")[-1]
                )
                _, unique_id = self.invoke_release_resources(
                    json.dumps(release_data)
                )
                event_recorder = EventRecorder()
                event_recorder.subscribe_event(
                    self.central_node, "longRunningCommandResult"
                )
                assert event_recorder.has_change_event_occurred(
                    self.central_node,
                    "longRunningCommandResult",
                    (unique_id[0], COMMAND_COMPLETED),
                    lookahead=10,
                )

            if self.subarray_node.obsState in [
                ObsState.RESOURCING,
                ObsState.SCANNING,
                ObsState.CONFIGURING,
                ObsState.READY,
                ObsState.IDLE,
            ]:
                LOGGER.info("Calling Abort and Restart on SubarrayNode")
                self.subarray_abort()
                self.subarray_restart()
            elif self.subarray_node.obsState in [
                ObsState.ABORTED,
                ObsState.FAULT,
            ]:
                self.subarray_restart()

        except Exception as e:
            LOGGER.exception("The exception is: %s", e)
            raise Exception(e)
