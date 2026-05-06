import json
import logging
from datetime import datetime

from ska_ser_logging import configure_logging

from tests.resources.test_support.common_utils.common_helpers import (
    AttributeWatcher,
    Resource,
    watch,
)
from tests.resources.test_support.constant import DEFAULT_DISH_VCC_CONFIG

configure_logging(logging.DEBUG)
LOGGER = logging.getLogger(__name__)


# this is a composite type of waiting based on a set of predefined
# pre conditions expected to be true
class Waiter:
    def __init__(self, **kwargs):
        """
        Args:
            kwargs (dict): device names
        """
        self.waits = []
        self.logs = ""
        self.error_logs = ""
        self.timed_out = False
        self.sdp_subarray1 = kwargs.get("sdp_subarray")
        self.sdp_master = kwargs.get("sdp_master")
        self.csp_subarray1 = kwargs.get("csp_subarray")
        self.csp_master = kwargs.get("csp_master")
        self.tmc_subarraynode1 = kwargs.get("tmc_subarraynode")
        self.dish_master_list = kwargs.get("dish_master_list", [])
        self.dish_leaf_node_list = kwargs.get("dish_leaf_node_list", [])
        self.tmc_csp_subarray_leaf_node = kwargs.get("csp_subarray_leaf_node")
        self.tmc_sdp_subarray_leaf_node = kwargs.get("sdp_subarray_leaf_node")
        self.cbf_subarray1 = kwargs.get("cbf_subarray1")
        self.cbf_controller = kwargs.get("cbf_controller")
        self.csp_master_leaf_node = kwargs.get("csp_master_leaf_node")

    def clear_watches(self):
        self.waits = []

    def set_wait_for_dish_ln(self, attribute_name, state_name):
        """Set wait for dish"""
        for dish_leaf_node in self.dish_leaf_node_list:
            if dish_leaf_node.dishMode != state_name:
                self.waits.append(
                    watch(Resource(dish_leaf_node)).to_become(
                        attribute_name, changed_to=state_name
                    )
                )

    def set_wait_for_dish_master(self, attribute_name, state_name):
        """Set wait for dish master"""
        for dish_master in self.dish_master_list:
            if dish_master.dishMode != state_name:
                self.waits.append(
                    watch(Resource(dish_master)).to_become(
                        attribute_name, changed_to=state_name
                    )
                )

    def set_wait_for_dish(self, attribute_name, state_name):
        """Set wait for dish master and dish leaf node"""
        LOGGER.info("self.dish_master_list: %s", self.dish_master_list)
        for index in range(0, len(self.dish_master_list)):
            LOGGER.info("index: %s", index)
            if self.dish_master_list[index].dishMode != state_name:
                self.waits.append(
                    watch(Resource(self.dish_master_list[index])).to_become(
                        attribute_name, changed_to=state_name
                    )
                )

                # PoinitngState Event will not be pushed if command is complete
                # Hence this assertion is skipped.
                if (
                    attribute_name not in ["pointingState"]
                    and self.dish_leaf_node_list[index].dishMode != state_name
                ):
                    self.waits.append(
                        watch(
                            Resource(self.dish_leaf_node_list[index])
                        ).to_become(attribute_name, changed_to=state_name)
                    )
        LOGGER.info("Dish Leaf Node check is done")

    def set_wait_for_going_to_off(self):
        self.waits.append(
            watch(Resource(self.sdp_subarray1)).to_become(
                "State", changed_to="OFF"
            )
        )
        self.waits.append(
            watch(Resource(self.sdp_master)).to_become(
                "State", changed_to="OFF"
            )
        )
        self.waits.append(
            watch(Resource(self.csp_master)).to_become(
                "State", changed_to="OFF"
            )
        )
        if self.dish_master_list and self.dish_leaf_node_list:
            self.set_wait_for_dish("dishMode", "STANDBY_LP")

    def set_wait_for_going_to_standby(self):
        self.waits.append(
            watch(Resource(self.sdp_subarray1)).to_become(
                "State", changed_to="OFF"
            )
        )
        self.waits.append(
            watch(Resource(self.sdp_master)).to_become(
                "State", changed_to="STANDBY"
            )
        )
        self.waits.append(
            watch(Resource(self.csp_master)).to_become(
                "State", changed_to="STANDBY"
            )
        )
        if self.dish_master_list and self.dish_leaf_node_list:
            self.set_wait_for_dish("dishMode", "STANDBY_LP")

    def set_wait_for_telescope_on(self):
        self.waits.append(
            watch(Resource(self.sdp_master)).to_become(
                "State", changed_to="ON"
            )
        )
        self.waits.append(
            watch(Resource(self.sdp_subarray1)).to_become(
                "State", changed_to="ON"
            )
        )
        self.waits.append(
            watch(Resource(self.csp_master)).to_become(
                "State", changed_to="ON"
            )
        )
        self.waits.append(
            watch(Resource(self.csp_subarray1)).to_become(
                "State", changed_to="ON"
            )
        )
        if self.dish_master_list:
            self.set_wait_for_dish_master("dishMode", "STANDBY_FP")

        if self.cbf_subarray1:
            watch(Resource(self.cbf_subarray1)).to_become(
                "State", changed_to="ON"
            )
        if self.cbf_controller:
            watch(Resource(self.cbf_controller)).to_become(
                "State", changed_to="ON"
            )
            watch(Resource(self.cbf_controller)).to_become(
                "reportVccState", changed_to="[0, 0, 0, 0]"
            )

    def set_wait_for_going_to_empty(self):
        self.waits.append(
            watch(Resource(self.tmc_csp_subarray_leaf_node)).to_become(
                "cspSubarrayObsState", changed_to="EMPTY"
            )
        )
        self.waits.append(
            watch(Resource(self.tmc_sdp_subarray_leaf_node)).to_become(
                "sdpSubarrayObsState", changed_to="EMPTY"
            )
        )
        self.waits.append(
            watch(Resource(self.tmc_subarraynode1)).to_become(
                "assignedResources", changed_to=None
            )
        )
        self.waits.append(
            watch(Resource(self.sdp_subarray1)).to_become(
                "obsState", changed_to="EMPTY"
            )
        )
        self.waits.append(
            watch(Resource(self.csp_subarray1)).to_become(
                "obsState", changed_to="EMPTY"
            )
        )
        self.waits.append(
            watch(Resource(self.tmc_subarraynode1)).to_become(
                "obsState", changed_to="EMPTY"
            )
        )

    def set_wait_for_assign_resources(self):
        self.waits.append(
            watch(Resource(self.tmc_csp_subarray_leaf_node)).to_become(
                "cspSubarrayObsState", changed_to="IDLE"
            )
        )
        self.waits.append(
            watch(Resource(self.tmc_sdp_subarray_leaf_node)).to_become(
                "sdpSubarrayObsState", changed_to="IDLE"
            )
        )
        self.waits.append(
            watch(Resource(self.csp_subarray1)).to_become(
                "obsState", changed_to="IDLE"
            )
        )
        self.waits.append(
            watch(Resource(self.sdp_subarray1)).to_become(
                "obsState", changed_to="IDLE"
            )
        )

        self.waits.append(
            watch(Resource(self.tmc_subarraynode1)).to_become(
                "obsState", changed_to="IDLE"
            )
        )

    def set_wait_for_configuring(self):
        self.waits.append(
            watch(Resource(self.tmc_subarraynode1)).to_become(
                "obsState", changed_to="CONFIGURING"
            )
        )

    def set_wait_for_obs_state(self, obs_state=None):
        self.waits.append(
            watch(Resource(self.tmc_csp_subarray_leaf_node)).to_become(
                "cspSubarrayObsState", changed_to=obs_state
            )
        )
        self.waits.append(
            watch(Resource(self.tmc_sdp_subarray_leaf_node)).to_become(
                "sdpSubarrayObsState", changed_to=obs_state
            )
        )
        self.waits.append(
            watch(Resource(self.csp_subarray1)).to_become(
                "obsState", changed_to=obs_state
            )
        )
        self.waits.append(
            watch(Resource(self.sdp_subarray1)).to_become(
                "obsState", changed_to=obs_state
            )
        )

        self.waits.append(
            watch(Resource(self.tmc_subarraynode1)).to_become(
                "obsState", changed_to=obs_state
            )
        )
        if self.dish_master_list and self.dish_leaf_node_list:
            self.set_wait_for_dish("pointingState", "TRACK")

    def set_wait_for_configure(self):
        self.waits.append(
            watch(Resource(self.tmc_csp_subarray_leaf_node)).to_become(
                "cspSubarrayObsState", changed_to="READY"
            )
        )
        self.waits.append(
            watch(Resource(self.tmc_sdp_subarray_leaf_node)).to_become(
                "sdpSubarrayObsState", changed_to="READY"
            )
        )
        self.waits.append(
            watch(Resource(self.csp_subarray1)).to_become(
                "obsState", changed_to="READY"
            )
        )
        self.waits.append(
            watch(Resource(self.sdp_subarray1)).to_become(
                "obsState", changed_to="READY"
            )
        )
        if self.dish_master_list:
            self.set_wait_for_dish("dishMode", "OPERATE")
            self.set_wait_for_dish("pointingState", "TRACK")

        self.waits.append(
            watch(Resource(self.tmc_subarraynode1)).to_become(
                "obsState", changed_to="READY"
            )
        )

    def set_wait_for_idle(self):
        self.waits.append(
            watch(Resource(self.tmc_csp_subarray_leaf_node)).to_become(
                "cspSubarrayObsState", changed_to="IDLE"
            )
        )
        self.waits.append(
            watch(Resource(self.tmc_sdp_subarray_leaf_node)).to_become(
                "sdpSubarrayObsState", changed_to="IDLE"
            )
        )
        self.waits.append(
            watch(Resource(self.csp_subarray1)).to_become(
                "obsState", changed_to="IDLE"
            )
        )
        self.waits.append(
            watch(Resource(self.sdp_subarray1)).to_become(
                "obsState", changed_to="IDLE"
            )
        )
        self.waits.append(
            watch(Resource(self.tmc_subarraynode1)).to_become(
                "obsState", changed_to="IDLE"
            )
        )

    def set_wait_for_aborted(self):
        self.waits.append(
            watch(Resource(self.tmc_subarraynode1)).to_become(
                "obsState", changed_to="ABORTED"
            )
        )

    def set_wait_for_ready(self):
        self.waits.append(
            watch(Resource(self.tmc_csp_subarray_leaf_node)).to_become(
                "cspSubarrayObsState", changed_to="READY"
            )
        )
        self.waits.append(
            watch(Resource(self.tmc_sdp_subarray_leaf_node)).to_become(
                "sdpSubarrayObsState", changed_to="READY"
            )
        )
        self.waits.append(
            watch(Resource(self.csp_subarray1)).to_become(
                "obsState", changed_to="READY"
            )
        )
        self.waits.append(
            watch(Resource(self.sdp_subarray1)).to_become(
                "obsState", changed_to="READY"
            )
        )
        self.waits.append(
            watch(Resource(self.tmc_subarraynode1)).to_become(
                "obsState", changed_to="READY"
            )
        )

    def set_wait_for_specific_obsstate(self, obsstate: str, devices: list):
        """Waits for the obsState of given devices
        to change to specified value."""
        for device in devices:
            self.waits.append(
                watch(Resource(device)).to_become(
                    "obsState", changed_to=obsstate
                )
            )

    def set_wait_for_scanning(self):
        self.waits.append(
            watch(Resource(self.tmc_csp_subarray_leaf_node)).to_become(
                "cspSubarrayObsState", changed_to="SCANNING"
            )
        )
        self.waits.append(
            watch(Resource(self.tmc_sdp_subarray_leaf_node)).to_become(
                "sdpSubarrayObsState", changed_to="SCANNING"
            )
        )
        self.waits.append(
            watch(Resource(self.csp_subarray1)).to_become(
                "obsState", changed_to="SCANNING"
            )
        )
        self.waits.append(
            watch(Resource(self.sdp_subarray1)).to_become(
                "obsState", changed_to="SCANNING"
            )
        )
        self.waits.append(
            watch(Resource(self.tmc_subarraynode1)).to_become(
                "obsState", changed_to="SCANNING"
            )
        )

    def set_wait_for_csp_master_to_become_off(self):
        self.waits.append(
            watch(Resource(self.csp_master)).to_become(
                "State", changed_to="OFF"
            )
        )

    def set_wait_for_load_dish_cfg(self):
        # Set wait for load dish cfg
        # sourceDishVccConfig is json so use predicate which
        # call from watch function and compare json string using
        # loads method
        def is_source_dish_cfg_changed(current_value, future_value):
            if not current_value and future_value:
                return False
            return json.loads(current_value) == json.loads(future_value)

        self.waits.append(
            watch(Resource(self.csp_master_leaf_node)).to_become(
                "sourceDishVccConfig",
                changed_to=json.dumps(DEFAULT_DISH_VCC_CONFIG),
                predicate=is_source_dish_cfg_changed,
            )
        )

    def wait(self, timeout=30, resolution=0.1):
        self.logs = ""

        now = datetime.now()
        current_time = now.strftime("%d/%m/%Y %H:%M:%S:%f")
        LOGGER.info("Start Time for wait : %s", current_time)
        while self.waits:
            wait = self.waits.pop()
            if isinstance(wait, AttributeWatcher):
                timeout = timeout * resolution
            try:
                result = wait.wait_until_conditions_met(
                    timeout=timeout, resolution=resolution
                )
            except Exception as ex:
                self.timed_out = True
                future_value_shim = ""
                timeout_shim = timeout * resolution
                if isinstance(wait, AttributeWatcher):
                    timeout_shim = timeout
                if wait.future_value is not None:
                    future_value_shim = f" to {wait.future_value} \
                        (current val={wait.current_value})"
                self.error_logs += "{} timed out whilst waiting for {} to \
                change from {}{} in {:f}s and raised {}\n".format(
                    wait.device_name,
                    wait.attr,
                    wait.previous_value,
                    future_value_shim,
                    timeout_shim,
                    ex,
                )
            else:
                timeout_shim = (timeout - result) * resolution
                if isinstance(wait, AttributeWatcher):
                    timeout_shim = result
                self.logs += (
                    "{} changed {} from {} to {} after {:f}s \n".format(
                        wait.device_name,
                        wait.attr,
                        wait.previous_value,
                        wait.current_value,
                        timeout_shim,
                    )
                )
        if self.timed_out:
            now = datetime.now()
            current_time = now.strftime("%d/%m/%Y %H:%M:%S:%f")
            LOGGER.info("End Time for wait : %s", current_time)
            raise Exception(
                "timed out, the following timeouts ocurred:\n{} Successful\
                      changes:\n{}".format(
                    self.error_logs, self.logs
                )
            )
