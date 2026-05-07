import json
import logging
import os
import time

from assertpy import assert_that
from ska_control_model import ObsState
from ska_ser_logging import configure_logging
from ska_tango_base.control_model import HealthState
from tango import DeviceProxy, DevState

from tests.resources.test_harness.event_recorder import EventRecorder
from tests.resources.test_harness.helpers import (
    SIMULATED_DEVICES_DICT,
    check_subarray_obs_state,
    generate_eb_pb_ids,
    prepare_json_args_for_commands,
    wait_and_validate_device_attribute_value,
    wait_for_partial_or_complete_abort,
)
from tests.resources.test_harness.utils.constant import (
    ABORTED,
    IDLE,
    ON,
    READY,
)
from tests.resources.test_harness.utils.enums import DishMode, SubarrayObsState
from tests.resources.test_harness.utils.obs_state_resetter import (
    ObsStateResetterFactory,
)
from tests.resources.test_harness.utils.sync_decorators import (
    sync_abort,
    sync_assign_resources,
    sync_configure,
    sync_end,
    sync_endscan,
    sync_release_resources,
    sync_restart,
)
from tests.resources.test_support.common_utils.common_helpers import Resource
from tests.resources.test_support.constant import (
    COMMAND_COMPLETED,
    DISH_001_CALIBRATION_DATA,
    DISH_036_CALIBRATION_DATA,
    CorrectionKey,
    centralnode,
    csp_master,
    csp_subarray1,
    csp_subarray_prefix,
    dish_master1,
    dish_master2,
    dish_master3,
    dish_master4,
    sdp_master,
    sdp_queue_connector,
    sdp_subarray1,
    sdp_subarray_prefix,
    tmc_csp_subarray_leaf_node,
    tmc_csp_subarrayln_prefix,
    tmc_dish_leaf_node1,
    tmc_dish_leaf_node2,
    tmc_dish_leaf_node3,
    tmc_dish_leaf_node4,
    tmc_dish_pointing_device1,
    tmc_dish_pointing_device2,
    tmc_dish_pointing_device3,
    tmc_dish_pointing_device4,
    tmc_sdp_subarray_leaf_node,
    tmc_sdp_subarrayln_prefix,
    tmc_subarraynode1,
)

configure_logging(logging.DEBUG)
LOGGER = logging.getLogger(__name__)

TIMEOUT = 110
REAL_DISH1_FQDN = os.getenv("DISH_NAME_1")
REAL_DISH36_FQDN = os.getenv("DISH_NAME_36")
REAL_DISH63_FQDN = os.getenv("DISH_NAME_63")
REAL_DISH100_FQDN = os.getenv("DISH_NAME_100")

device_dict = {
    # TODO use this as as list when multiple subarray considered in testing
    "sdp_subarray": sdp_subarray1,
    "csp_subarray": csp_subarray1,
    "csp_master": csp_master,
    "tmc_subarraynode": tmc_subarraynode1,
    "sdp_master": sdp_master,
    "centralnode": centralnode,
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
    "csp_subarray_leaf_node": tmc_csp_subarray_leaf_node,
    "sdp_subarray_leaf_node": tmc_sdp_subarray_leaf_node,
}


class SubarrayNodeWrapper(object):
    """Subarray Node class which implement methods required for test cases
    to test subarray node.
    """

    def __init__(self) -> None:
        super().__init__()
        self.tmc_subarraynode1 = tmc_subarraynode1
        self.subarray_node = DeviceProxy(self.tmc_subarraynode1)
        self.subarray_node.set_timeout_millis(5000)
        self.csp_subarray_leaf_node = DeviceProxy(tmc_csp_subarray_leaf_node)
        self.sdp_subarray_leaf_node = DeviceProxy(tmc_sdp_subarray_leaf_node)
        self.sdp_qc = DeviceProxy(sdp_queue_connector)

        if (
            SIMULATED_DEVICES_DICT["csp_and_sdp"]
            and not SIMULATED_DEVICES_DICT["all_mocks"]
        ):
            dish_fqdn001 = REAL_DISH1_FQDN
            dish_fqdn036 = REAL_DISH36_FQDN
            dish_fqdn063 = REAL_DISH63_FQDN
            dish_fqdn100 = REAL_DISH100_FQDN
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
        self.dish_master_name_list = [
            dish_fqdn001,
            dish_fqdn036,
            dish_fqdn063,
            dish_fqdn100,
        ]

        self.dish_leaf_node_list = [
            DeviceProxy(tmc_dish_leaf_node1),
            DeviceProxy(tmc_dish_leaf_node2),
            DeviceProxy(tmc_dish_leaf_node3),
            DeviceProxy(tmc_dish_leaf_node4),
        ]
        self.dish_pointing_device = [
            DeviceProxy(tmc_dish_pointing_device1),
            DeviceProxy(tmc_dish_pointing_device2),
            DeviceProxy(tmc_dish_pointing_device3),
            DeviceProxy(tmc_dish_pointing_device4),
        ]
        for dish_leaf_node in self.dish_leaf_node_list:
            dish_leaf_node.set_timeout_millis(5000)

        for dish_leaf_node in self.dish_leaf_node_list:
            dish_leaf_node.set_timeout_millis(5000)

        self.subarray_devices = {
            "csp_subarray": DeviceProxy(csp_subarray1),
            "sdp_subarray": DeviceProxy(sdp_subarray1),
        }
        self._state = DevState.OFF
        self.obs_state = SubarrayObsState.EMPTY
        self._assigned_resources = []
        # setup subarray
        self._setup()
        # Subarray state
        self.ON_STATE = ON
        self.IDLE_OBS_STATE = IDLE
        self.READY_OBS_STATE = READY
        self.ABORTED_OBS_STATE = ABORTED
        self.csp_subarray1 = csp_subarray1
        self.sdp_subarray1 = sdp_subarray1
        device_dict["dish_master_list"] = self.dish_master_list
        device_dict["dish_leaf_node_list"] = self.dish_leaf_node_list
        self.event_recorder = EventRecorder()
        self.event_recorder.subscribe_event(
            self.subarray_node, "longRunningCommandResult"
        )

    def _setup(self):
        """ """
        if (
            SIMULATED_DEVICES_DICT["csp_and_dish"]
            or SIMULATED_DEVICES_DICT["all_mocks"]
        ):
            for dish_master_proxy in self.dish_master_list:
                dish_master_proxy.SetDirectState(DevState.STANDBY)
                # Setting DishMode to STANDBY_FP
                dish_master_proxy.SetDirectDishMode(DishMode.STANDBY_FP)

    @property
    def state(self) -> DevState:
        """TMC SubarrayNode operational state"""
        self._state = Resource(self.tmc_subarraynode1).get("State")
        return self._state

    @state.setter
    def state(self, value):
        """Sets value for TMC subarrayNode operational state

        Args:
            value (DevState): operational state value
        """
        self._state = value

    @property
    def assigned_resources(self) -> list:
        """TMC SubarrayNode assignedResources"""
        self._assigned_resources = Resource(self.tmc_subarraynode1).get(
            "assignedResources"
        )
        return self._assigned_resources

    @property
    def obs_state(self):
        """TMC SubarrayNode observation state"""
        self._obs_state = Resource(self.tmc_subarraynode1).get("obsState")
        return self._obs_state

    @obs_state.setter
    def obs_state(self, value):
        """Sets value for TMC subarrayNode observation state

        Args:
            value (DevState): observation state value
        """
        self._obs_state = value

    @property
    def health_state(self) -> HealthState:
        """Telescope health state representing overall health of telescope"""
        self._health_state = Resource(self.tmc_subarraynode1).get(
            "healthState"
        )
        return self._health_state

    @health_state.setter
    def health_state(self, value):
        """Telescope health state representing overall health of telescope

        Args:
            value (HealthState): telescope health state value
        """
        self._health_state = value

    def set_subarray_id(self, requested_subarray_id: str) -> None:
        """This method creates subarray devices for the requested subarray
        id"""
        subarray_id = str(requested_subarray_id).zfill(2)
        self.subarray_devices = {
            "csp_subarray": DeviceProxy(
                f"{csp_subarray_prefix}/{subarray_id}"
            ),
            "sdp_subarray": DeviceProxy(
                f"{sdp_subarray_prefix}/{subarray_id}"
            ),
        }
        self.csp_subarray_leaf_node = DeviceProxy(
            f"{tmc_csp_subarrayln_prefix}/{subarray_id}"
        )
        self.sdp_subarray_leaf_node = DeviceProxy(
            f"{tmc_sdp_subarrayln_prefix}/{subarray_id}"
        )

    def move_to_on(self):
        # Move subarray to ON state
        if self.state != self.ON_STATE:
            Resource(self.tmc_subarraynode1).assert_attribute("State").equals(
                "OFF"
            )
            result, message = self.subarray_node.On()
            LOGGER.info("Invoked ON on SubarrayNode")
            return result, message

    def move_to_off(self):
        # Move Subarray to OFF state
        Resource(self.tmc_subarraynode1).assert_attribute("State").equals("ON")
        result, message = self.subarray_node.Off()
        LOGGER.info("Invoked OFF on SubarrayNode")
        return result, message

    @sync_configure(device_dict=device_dict)
    def store_configuration_data(self, input_string: str):
        """Invoke configure command on subarray Node
        Args:
            input_string (str): config input json
        Returns:
            (result, message): result, message tuple
        """
        result, message = self.subarray_node.Configure(input_string)
        LOGGER.info("Invoked Configure on SubarrayNode")
        return result, message

    @sync_end(device_dict=device_dict)
    def end_observation(self):
        result, message = self.subarray_node.End()
        LOGGER.info("Invoked End on SubarrayNode")
        return result, message

    @sync_endscan(device_dict=device_dict)
    def remove_scan_data(self):
        result, message = self.subarray_node.EndScan()
        LOGGER.info("Invoked EndScan on SubarrayNode")
        return result, message

    def store_scan_data(self, input_string):
        result, message = self.subarray_node.Scan(input_string)
        LOGGER.info("Invoked Scan on SubarrayNode")
        return result, message

    @sync_abort(device_dict=device_dict)
    def abort_subarray(self):
        result, message = self.subarray_node.Abort()
        LOGGER.info("Invoked Abort on SubarrayNode")
        return result, message

    @sync_restart(device_dict=device_dict)
    def restart_subarray(self):
        result, message = self.subarray_node.Restart()
        LOGGER.info("Invoked Restart on SubarrayNode")
        return result, message

    @sync_assign_resources(device_dict)
    def store_resources(self, assign_json: str):
        """Invoke Assign Resource command on subarray Node
        Args:
            assign_json (str): Assign resource input json
        """
        input_json = json.loads(assign_json)
        generate_eb_pb_ids(input_json)
        result, message = self.subarray_node.AssignResources(
            json.dumps(input_json)
        )
        LOGGER.info("Invoked AssignResources on SubarrayNode")
        return result, message

    @sync_release_resources(device_dict)
    def release_resources_subarray(self):
        result, message = self.subarray_node.ReleaseAllResources()
        LOGGER.info("Invoked Release Resource on SubarrayNode")
        return result, message

    def execute_transition(self, command_name: str, argin=None):
        """Execute provided command on subarray
        Args:
            command_name (str): Name of command to execute
        """

        retry = 0
        while retry <= 3:
            try:
                if command_name is not None:
                    if argin:
                        result, message = self.subarray_node.command_inout(
                            command_name, argin
                        )
                        LOGGER.info(f"Invoked {command_name} on SubarrayNode")
                        return result, message
                    result, message = self.subarray_node.command_inout(
                        command_name
                    )
                    LOGGER.info(f"Invoked {command_name} on SubarrayNode")
                    return result, message

            except Exception as e:
                LOGGER.exception(
                    "Exception occurred while executing command: %s", e
                )
                if retry == 2:
                    raise Exception
                retry += 1
            time.sleep(0.1)

    def _reset_simulator_devices(self):
        """Reset Simulator devices to it's original state"""
        if (
            SIMULATED_DEVICES_DICT["csp_and_sdp"]
            or SIMULATED_DEVICES_DICT["all_mocks"]
        ):
            sim_device_fqdn_list = [self.sdp_subarray1, self.csp_subarray1]
        elif SIMULATED_DEVICES_DICT["csp_and_dish"]:
            sim_device_fqdn_list = [self.csp_subarray1]
        elif (
            SIMULATED_DEVICES_DICT["sdp_and_dish"]
            or SIMULATED_DEVICES_DICT["sdp"]
        ):
            sim_device_fqdn_list = [self.sdp_subarray1]
        for sim_device_fqdn in sim_device_fqdn_list:
            device = DeviceProxy(sim_device_fqdn)
            device.ResetDelayInfo()
            device.SetDirectHealthState(HealthState.UNKNOWN)
            device.SetDefective(json.dumps({"enabled": False}))

    def _reset_dishes(self):
        """Reset Dish Devices"""
        if (
            SIMULATED_DEVICES_DICT["csp_and_dish"]
            or SIMULATED_DEVICES_DICT["all_mocks"]
            or SIMULATED_DEVICES_DICT["sdp_and_dish"]
        ):
            for dish_master in self.dish_master_list:
                dish_master.SetDelay(2)
                dish_master.SetDirectHealthState(HealthState.UNKNOWN)

    def _clear_command_call_and_transition_data(self, clear_transition=False):
        """Clears the command call data"""
        if SIMULATED_DEVICES_DICT["csp_and_sdp"]:
            for sim_device in [
                self.sdp_subarray1,
                self.csp_subarray1,
            ]:
                device = DeviceProxy(sim_device)
                device.set_timeout_millis(5000)
                device.ClearCommandCallInfo()
                if clear_transition:
                    device.ResetTransitions()
        elif SIMULATED_DEVICES_DICT["csp_and_dish"]:
            for sim_device in [
                self.csp_subarray1,
                dish_master1,
                dish_master2,
            ]:
                device = DeviceProxy(sim_device)
                device.set_timeout_millis(5000)
                device.ClearCommandCallInfo()
                if clear_transition:
                    device.ResetTransitions()
        elif SIMULATED_DEVICES_DICT["sdp_and_dish"]:
            for sim_device in [
                self.sdp_subarray1,
                dish_master1,
                dish_master2,
            ]:
                device = DeviceProxy(sim_device)
                device.set_timeout_millis(5000)
                device.ClearCommandCallInfo()
                if clear_transition:
                    device.ResetTransitions()
        elif SIMULATED_DEVICES_DICT["all_mocks"]:
            for sim_device in [
                self.sdp_subarray1,
                self.csp_subarray1,
                dish_master1,
                dish_master2,
            ]:
                device = DeviceProxy(sim_device)
                device.set_timeout_millis(5000)
                device.ClearCommandCallInfo()
                if clear_transition:
                    device.ResetTransitions()
        else:
            LOGGER.info("Devices deployed are real")

    def get_assigned_dish_leaf_nodes_list(self) -> list:
        """Returns a list of all the dish leaf nodes corresponding to the
        dishes that are assigned"""
        assigned_receptors = self.assigned_resources
        assigned_receptors = [receptor[3:] for receptor in assigned_receptors]
        assigned_dish_leaf_nodes = []
        for receptor in assigned_receptors:
            for dish_leaf_node in self.dish_leaf_node_list:
                if receptor in dish_leaf_node.dev_name():
                    assigned_dish_leaf_nodes.append(dish_leaf_node)
                    break
        return assigned_dish_leaf_nodes

    def tear_down(self):
        """Tear down after each test run"""

        LOGGER.info(
            "Calling tear down for subarray with %s obsState", self.obs_state
        )
        self._clear_command_call_and_transition_data(clear_transition=True)

        if self.obs_state in ("RESOURCING", "CONFIGURING", "SCANNING"):
            LOGGER.info("Invoking Abort on Subarray")
            self.execute_transition("Abort")
            wait_for_partial_or_complete_abort()

            _, unique_restart = self.restart_subarray()
            assert self.event_recorder.has_change_event_occurred(
                self.subarray_node,
                "longRunningCommandResult",
                (unique_restart[0], COMMAND_COMPLETED),
            )
            self.event_recorder.clear_events()

        elif self.obs_state == ObsState.READY:
            _, unique_end = self.end_observation()
            assert self.event_recorder.has_change_event_occurred(
                self.subarray_node,
                "longRunningCommandResult",
                (unique_end[0], COMMAND_COMPLETED),
            )
            _, unique_release = self.release_resources_subarray()
            assert self.event_recorder.has_change_event_occurred(
                self.subarray_node,
                "longRunningCommandResult",
                (unique_release[0], COMMAND_COMPLETED),
            )
            self.event_recorder.clear_events()

        elif self.obs_state == ObsState.IDLE:
            _, unique_release_resource = self.release_resources_subarray()
            assert self.event_recorder.has_change_event_occurred(
                self.subarray_node,
                "longRunningCommandResult",
                (unique_release_resource[0], COMMAND_COMPLETED),
            )
            self.event_recorder.clear_events()

        elif self.obs_state in [ObsState.ABORTED, "FAULT"]:
            """Invoke Restart"""
            LOGGER.info("Invoking Restart on Subarray")
            _, unique_id = self.restart_subarray()
            assert self.event_recorder.has_change_event_occurred(
                self.subarray_node,
                "longRunningCommandResult",
                (unique_id[0], COMMAND_COMPLETED),
            )
        else:
            self.force_change_of_obs_state("EMPTY")
        # Move Subarray to OFF state
        self.move_to_off()
        self._reset_dishes()
        self._reset_simulator_devices()
        assert check_subarray_obs_state("EMPTY")
        self.event_recorder.clear_events()

    def check_if_dishes_are_ready(self, waiter):
        LOGGER.info("waiter.dish_master_list: %s", waiter.dish_master_list)
        LOGGER.info(
            "waiter.dish_leaf_node_list: %s", waiter.dish_leaf_node_list
        )
        if waiter.dish_master_list and waiter.dish_leaf_node_list:
            LOGGER.info("Check for PS READY")
            waiter.set_wait_for_dish("pointingState", "READY")

    def clear_all_data(self):
        """Method to clear the observations
        and put the SubarrayNode in EMPTY"""
        if self.obs_state in [
            "IDLE",
            "RESOURCING",
            "READY",
            "CONFIGURING",
            "SCANNING",
        ]:
            self.abort_subarray()
            self.restart_subarray()
        elif self.obs_state == "ABORTED":
            self.restart_subarray()

    def force_change_of_obs_state(
        self,
        dest_state_name: str,
        assign_input_json: str = "",
        configure_input_json: str = "",
        scan_input_json: str = "",
    ) -> None:
        """Force SubarrayNode obsState to provided obsState

        Args:
            dest_state_name (str): Destination obsState
        """
        factory_obj = ObsStateResetterFactory()
        obs_state_resetter = factory_obj.create_obs_state_resetter(
            dest_state_name, self
        )
        if assign_input_json:
            obs_state_resetter.assign_input = assign_input_json
        if configure_input_json:
            obs_state_resetter.configure_input = configure_input_json
        if scan_input_json:
            obs_state_resetter.scan_input = scan_input_json
        obs_state_resetter.reset()
        self._clear_command_call_and_transition_data()

    def simulate_receive_addresses_event(self, sdp_sim, command_input_factory):
        """Sets the receive addresses attribute on SDP Subarray so an event can
        be simulated for Subarray Node to process.
        """
        receive_addresses = prepare_json_args_for_commands(
            "receive_addresses_mid", command_input_factory
        )
        sdp_sim.SetDirectreceiveAddresses(receive_addresses)

    def set_pointing_cal_on_queue_connector(self):
        """Set Pointing Cal on SDP"""
        # Setting pointing calibration data
        sdp_qc = DeviceProxy(sdp_queue_connector)

        sdp_qc.SetPointingCalSka001(DISH_001_CALIBRATION_DATA)
        sdp_qc.SetPointingCalSka036(DISH_036_CALIBRATION_DATA)

    def execute_five_point_calibration_scan(
        self,
        partial_configure_jsons: list[str],
        event_tracer,
        command_input_factory,
        correction_key=CorrectionKey.UPDATE,
    ) -> None:
        """Perform a five point calibration scan on Subarray Node using the
        partial configuration jsons and scan jsons provided as inputs.

        Args:
            partial_configure_jsons (list[str]): Partial configuration json
                file names
            scan_jsons (list[str]): Scan json file names
        """
        partial_configure_1 = prepare_json_args_for_commands(
            partial_configure_jsons[0], command_input_factory
        )
        partial_configure_2 = prepare_json_args_for_commands(
            partial_configure_jsons[1], command_input_factory
        )
        partial_configure_3 = prepare_json_args_for_commands(
            partial_configure_jsons[2], command_input_factory
        )
        partial_configure_4 = prepare_json_args_for_commands(
            partial_configure_jsons[3], command_input_factory
        )

        scan_json = prepare_json_args_for_commands(
            "scan_mid", command_input_factory
        )

        partial_configure_list = [
            partial_configure_1,
            partial_configure_2,
            partial_configure_3,
            partial_configure_4,
        ]

        for idx, partial_configure_json in enumerate(partial_configure_list):
            if correction_key == CorrectionKey.UPDATE:
                input_json = json.loads(partial_configure_json)
                input_json["pointing"]["correction"] = "UPDATE"
                partial_configure_json = json.dumps(input_json)
            elif correction_key == CorrectionKey.RESET:
                input_json = json.loads(partial_configure_json)
                input_json["pointing"]["correction"] = "RESET"
                partial_configure_json = json.dumps(input_json)

            # Partial configure
            _, unique_id = self.execute_transition(
                "Configure", partial_configure_json
            )
            assert_that(event_tracer).described_as(
                "FAILED ASSUMPTION AFTER CONFIGURE COMMAND: "
                "Subarray Node device"
                f"({self.subarray_node.dev_name()}) "
                "is expected to be in CONFIGURING obstate",
            ).within_timeout(TIMEOUT).has_change_event_occurred(
                self.subarray_node,
                "obsState",
                ObsState.CONFIGURING,
            )
            assert_that(event_tracer).described_as(
                "FAILED ASSUMPTION AFTER CONFIGURE COMMAND COMPLETION: "
                "Subarray Node device"
                f"({self.subarray_node.dev_name()}) "
                "is expected to be in READY obstate",
            ).within_timeout(TIMEOUT).has_change_event_occurred(
                self.subarray_node,
                "obsState",
                ObsState.READY,
            )
            assert_that(event_tracer).described_as(
                "FAILED ASSUMPTION AFTER PARTIAL CONFIGURE COMMAND: "
                "'the subarray is in READY obsState'"
                "Subarray Node device"
                f"({self.subarray_node.dev_name()}) "
                "is expected have longRunningCommand as"
                '(unique_id,(ResultCode.OK,"Command Completed"))',
            ).within_timeout(TIMEOUT).has_change_event_occurred(
                self.subarray_node,
                "longRunningCommandResult",
                (
                    unique_id[0],
                    COMMAND_COMPLETED,
                ),
            )
            event_tracer.clear_events()

            # assert sourceOffset gets populated as expected
            ca_offset, ie_offset = 0.0, 0.0
            if correction_key == CorrectionKey.UPDATE:
                # For partial_configure_1 and partial_configure_3 ,
                # extract x,y from trajectory attrs
                if idx in (0, 2):
                    pointing_data = json.loads(partial_configure_json)[
                        "pointing"
                    ]
                    ca_offset = pointing_data["groups"][0]["trajectory"][
                        "attrs"
                    ]["x"]
                    ie_offset = pointing_data["groups"][0]["trajectory"][
                        "attrs"
                    ]["y"]
                else:
                    ca_offset, ie_offset = (
                        json.loads(partial_configure_json)["pointing"][key]
                        for key in ("ca_offset_arcsec", "ie_offset_arcsec")
                    )
            elif correction_key == CorrectionKey.RESET:
                ca_offset, ie_offset = 0.0, 0.0
            LOGGER.info(
                "Asserting sourceOffset attribute value on dish leaf nodes %s",
                [
                    dish_leaf_node.sourceOffset
                    for dish_leaf_node in self.dish_leaf_node_list
                ],
            )
            expected_offset = [float(ca_offset), float(ie_offset)]
            assigned_dish_leaf_nodes = self.get_assigned_dish_leaf_nodes_list()
            dish_leaf_nodes_to_check = [
                dish_leaf_node
                for dish_leaf_node in assigned_dish_leaf_nodes
                if "ska036" in dish_leaf_node.dev_name()
                or "ska100" in dish_leaf_node.dev_name()
            ]
            dish_pointing_devices_to_check = [
                dish_pointing_device
                for dish_pointing_device in self.dish_pointing_device
                if "ska036" in dish_pointing_device.dev_name()
                or "ska100" in dish_pointing_device.dev_name()
            ]
            LOGGER.info(
                "Validating sourceOffset on dish leaf nodes %s",
                [
                    dish_leaf_node.name()
                    for dish_leaf_node in dish_leaf_nodes_to_check
                ],
            )
            for dish_leaf_node in dish_leaf_nodes_to_check:
                retries = 0
                current_offset = list(dish_leaf_node.sourceOffset)
                while retries < 6:
                    current_offset = list(dish_leaf_node.sourceOffset)
                    if current_offset == expected_offset:
                        break
                    time.sleep(2)
                    retries += 1

                assert current_offset == expected_offset, (
                    f"{dish_leaf_node.name()} sourceOffset {current_offset} "
                    f"does not match expected {expected_offset}"
                )

            LOGGER.info(
                "Validating targetData trajectory offsets on "
                "dish pointing devices %s",
                [
                    dish_pointing_device.name()
                    for dish_pointing_device in dish_pointing_devices_to_check
                ],
            )
            expected_target_data = {
                "x": float(ca_offset),
                "y": float(ie_offset),
            }
            for dish_pointing_device in dish_pointing_devices_to_check:
                retries = 0
                current_target_data = {}
                while retries < 6:
                    current_target_data = json.loads(
                        dish_pointing_device.targetData
                    )["pointing"]["trajectory"]["attrs"]
                    if current_target_data == expected_target_data:
                        break
                    time.sleep(2)
                    retries += 1

                assert current_target_data == expected_target_data, (
                    f"{dish_pointing_device.name()} targetData trajectory "
                    f"{current_target_data} does not match expected "
                    f"{expected_target_data}"
                )

                program_track_table = json.loads(
                    dish_pointing_device.pointingprogramtracktable
                )
                LOGGER.info(
                    "Validating pointingProgramTrackTable on "
                    f"{dish_pointing_device.name()}, "
                    f"pointingProgramTrackTable: {program_track_table}"
                    f" and length of "
                    f"pointingProgramTrackTable: {len(program_track_table)}",
                )
                assert len(program_track_table) == 15

            # Scan
            self.execute_transition("Scan", scan_json)
            assert_that(event_tracer).described_as(
                "FAILED ASSUMPTION AFTER SCAN COMMAND: "
                "Subarray Node device"
                f"({self.subarray_node.dev_name()}) "
                "is expected to be in SCANNING obstate",
            ).within_timeout(TIMEOUT).has_change_event_occurred(
                self.subarray_node,
                "obsState",
                ObsState.SCANNING,
            )
            assert wait_and_validate_device_attribute_value(
                self.subarray_node, "obsState", ObsState.READY
            )
            event_tracer.clear_events()
