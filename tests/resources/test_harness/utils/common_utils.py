"""This module implement common utils
"""

from __future__ import annotations

import time
from os.path import dirname, join
from typing import TYPE_CHECKING

from assertpy import assert_that
from ska_control_model import ObsState
from ska_tango_testing.integration import TangoEventTracer
from tango import DevState

from tests.resources.test_harness.utils.constant import EVENT_TIMEOUT
from tests.resources.test_harness.utils.wait_helpers import Waiter
from tests.resources.test_support.constant import COMMAND_COMPLETED
from tests.resources.test_support.enum import DishMode

if TYPE_CHECKING:
    from tests.resources.test_harness.central_node_mid import (
        CentralNodeWrapperMid,
    )


def get_subarray_input_json(slug):
    """
    Args:
        slug (str): base name of file
    Return:
        Read and return content of file
    """
    assign_json_file_path = join(
        dirname(__file__),
        "..",
        "..",
        "..",
        "data",
        "subarray",
        f"{slug}.json",
    )
    with open(assign_json_file_path, "r", encoding="UTF-8") as f:
        assign_json = f.read()
    return assign_json


def get_centralnode_input_json(slug):
    """
    Args:
        slug (str): base name of file
    Return:
        Read and return content of file
    """
    assign_json_file_path = join(
        dirname(__file__),
        "..",
        "..",
        "..",
        "data",
        "centralnode",
        f"{slug}.json",
    )
    with open(assign_json_file_path, "r", encoding="UTF-8") as f:
        assign_json = f.read()
    return assign_json


class JsonFactory(object):
    """Implement methods required for getting json"""

    def create_subarray_configuration(self, json_type):
        """Read and return configuration json file from
            tests/data/subarray folder
        Args:
            json_type (str): Base name of file which is stored in data folder
        Return:
            config_json (str): Return configure json based json type provided
        """
        return get_subarray_input_json(json_type)

    def create_assign_resources_configuration(self, json_type):
        """Read and return configuration json file from
            tests/data/subarray folder
        Args:
            json_type (str): Base name of file which is stored in data folder
        Return:
            config_json (str): Return configure json based json type provided
        """
        return get_subarray_input_json(json_type)

    def create_centralnode_configuration(self, json_type):
        """Read and return configuration json file from
            tests/data/centralnode folder
        Args:
            json_type (str): Base name of file which is stored in data folder
        Return:
            config_json (str): Return configure json based json type provided
        """
        return get_centralnode_input_json(json_type)


class SharedContext:
    def __init__(self):
        self.unique_id = None


def check_obsstate_sdp_in_first_configure(
    event_recorder, subarray_node
) -> None:
    """
    SDP does not go to CONFIGURING in each CONFIGURE command
    except very first CONFIGURE command after Assign .

    """
    # TODO
    # Currently SDP goes in configuring only in first configure
    # Command.This is however resolved in SDP 0.20.0.
    # When testing with same version is done ,we can check and remove
    # this logic of configure_cycle and perform check for
    # configuring after each of the configure command
    assert event_recorder.has_change_event_occurred(
        subarray_node.subarray_devices["sdp_subarray"],
        "obsState",
        ObsState.CONFIGURING,
    )
    wait_for_device_status_ready(
        subarray_node.subarray_devices["sdp_subarray"]
    )

    assert event_recorder.has_change_event_occurred(
        subarray_node.subarray_devices["sdp_subarray"],
        "obsState",
        ObsState.READY,
    )


def check_scan_successful(
    subarray_node, event_recorder, scan_id, unique_id
) -> None:
    """
    1)SDP , TMC sub-array  go to scanning
    2)scan_id attribute from SDP sub-array reflects exact scan_id
    sent by TMC .This makes sure we are checking some more attributes
    from SDP .In future this can be extended to include other attribute
    verification as well.
    3)After scan duration is completed , end scan will be triggered
    taking system to READY state. Related Obs-state checks are  added.
    """

    wait_for_device_status_scanning(subarray_node.subarray_node)

    assert event_recorder.has_change_event_occurred(
        subarray_node.subarray_node,
        "obsState",
        ObsState.SCANNING,
        lookahead=20,
    )
    assert event_recorder.has_change_event_occurred(
        subarray_node.subarray_devices["sdp_subarray"],
        "obsState",
        ObsState.SCANNING,
        lookahead=20,
    )

    assert event_recorder.has_change_event_occurred(
        subarray_node.subarray_devices["sdp_subarray"],
        "scanID",
        int(scan_id),
        lookahead=20,
    )

    wait_for_device_status_ready(
        subarray_node.subarray_devices["sdp_subarray"]
    )
    assert event_recorder.has_change_event_occurred(
        subarray_node.subarray_devices["sdp_subarray"],
        "obsState",
        ObsState.READY,
        lookahead=20,
    )

    wait_for_device_status_ready(subarray_node.subarray_node)
    assert event_recorder.has_change_event_occurred(
        subarray_node.subarray_node, "obsState", ObsState.READY, lookahead=20
    )
    assert event_recorder.has_change_event_occurred(
        subarray_node.subarray_node,
        "longRunningCommandResult",
        (unique_id[0], COMMAND_COMPLETED),
        lookahead=20,
    )


def check_configure_successful(
    subarray_node, event_recorder, unique_id, scan_type, processed_scan_type
) -> None:
    """
    Adds check to verify if configure command is successful
    """
    wait_for_device_status_ready(
        subarray_node.subarray_devices["sdp_subarray"]
    )

    wait_for_device_status_ready(subarray_node.subarray_node)
    assert event_recorder.has_change_event_occurred(
        subarray_node.subarray_node, "obsState", ObsState.READY, lookahead=10
    )

    # For same configuration scantype no event is pushed
    # https://gitlab.com/ska-telescope/sdp/ska-sdp-lmc/-/blob/master/src/ska_sdp_lmc/subarray/device.py#L548

    if scan_type != processed_scan_type:
        assert event_recorder.has_change_event_occurred(
            subarray_node.subarray_devices["sdp_subarray"],
            "scanType",
            scan_type,
            lookahead=20,
        )

    assert event_recorder.has_change_event_occurred(
        subarray_node.subarray_node,
        "longRunningCommandResult",
        (unique_id[0], COMMAND_COMPLETED),
        lookahead=20,
    )


def wait_for_device_status_ready(device_name: str) -> None:
    """
    Checks if given device is in READY obs-state

     :param device_name: device name
     :type device_name: str
    """
    the_waiter = Waiter()
    the_waiter.set_wait_for_specific_obsstate("READY", [device_name])
    the_waiter.wait(800)


def wait_for_device_status_scanning(device_name: str) -> None:
    """
    Checks if given device is in SCANNING obs-state

    :param device_name: device name
    :type device_name: str
    """
    the_waiter = Waiter()
    the_waiter.set_wait_for_specific_obsstate("SCANNING", [device_name])
    the_waiter.wait(200)


def wait_added_for_skb372():
    """
    Waits for few seocnds
    """
    # TODO: Remove this method call from the tests once new SubarrayNode
    # aggregation is intgerated in tmc-mid integration repository
    time.sleep(4)


def check_scan_successful_csp(
    subarray_node, event_recorder, scan_id, unique_id
) -> None:
    """
    1)CSP , TMC subarray  go to scanning
    2)scan_id attribute from CSP sub-array reflects exact scan_id
    sent by TMC .This makes sure we are checking some more attributes
    from CSP .In future this can be extended to include other attribute
    verification as well.
    3)After scan duration is completed , end scan will be triggered
    taking system to READY state. Related Obs-state checks are  added.
    """
    # Faced a delay while testing , hence adding waiter here.

    the_waiter = Waiter()
    the_waiter.set_wait_for_specific_obsstate(
        "SCANNING", [subarray_node.subarray_node]
    )
    the_waiter.wait(200)
    assert event_recorder.has_change_event_occurred(
        subarray_node.subarray_node,
        "obsState",
        ObsState.SCANNING,
        lookahead=10,
    )

    assert event_recorder.has_change_event_occurred(
        subarray_node.subarray_devices["csp_subarray"],
        "obsState",
        ObsState.SCANNING,
        lookahead=20,
    )
    assert event_recorder.has_change_event_occurred(
        subarray_node.subarray_devices["csp_subarray"],
        "scanID",
        int(scan_id),
        lookahead=20,
    )

    the_waiter.set_wait_for_specific_obsstate(
        "READY", [subarray_node.subarray_node]
    )
    the_waiter.wait(150)
    assert event_recorder.has_change_event_occurred(
        subarray_node.subarray_devices["csp_subarray"],
        "obsState",
        ObsState.READY,
        lookahead=10,
    )

    the_waiter.set_wait_for_specific_obsstate(
        "READY", [subarray_node.subarray_node]
    )
    the_waiter.wait(100)
    assert event_recorder.has_change_event_occurred(
        subarray_node.subarray_node, "obsState", ObsState.READY, lookahead=20
    )
    assert event_recorder.has_change_event_occurred(
        subarray_node.subarray_node,
        "longRunningCommandResult",
        (unique_id[0], COMMAND_COMPLETED),
        lookahead=10,
    )


def check_configure_successful_csp(
    subarray_node, event_recorder, unique_id, scan_type
) -> None:
    """
    Adds check to verify if configure command is successful
    """
    the_waiter = Waiter()
    the_waiter.set_wait_for_specific_obsstate(
        "READY", [subarray_node.subarray_devices["csp_subarray"]]
    )
    the_waiter.wait(100)
    the_waiter.set_wait_for_specific_obsstate(
        "READY", [subarray_node.subarray_node]
    )
    the_waiter.wait(1500)

    event_recorder.subscribe_event(
        subarray_node.subarray_node, "longRunningCommandResult"
    )

    assert event_recorder.has_change_event_occurred(
        subarray_node.subarray_node,
        "longRunningCommandResult",
        (unique_id[0], COMMAND_COMPLETED),
        lookahead=10,
    )

    assert event_recorder.has_change_event_occurred(
        subarray_node.subarray_node, "obsState", ObsState.READY, lookahead=10
    )


def setup_dish_events(
    central_node_mid,
    event_tracer,
    dish_ids,
) -> None:
    """
    This function will subscribe events for dish attributes

    Args:
        central_node_mid: Fixture for a TMC CentralNode wrapper class
        event_tracer: Fixture for EventTracer class
    """
    dish_ids = ["SKA001", "SKA036", "SKA077", "SKA100"]
    events = ["dishMode", "pointingState"]

    for dish_id in dish_ids:
        dish_master = central_node_mid.dish_master_dict[dish_id]
        dish_leaf = central_node_mid.dish_leaf_node_dict[dish_id]

        for event in events:
            event_tracer.subscribe_event(dish_master, event)
            event_tracer.subscribe_event(dish_leaf, event)


def turn_on_telescope(
    central_node_mid: CentralNodeWrapperMid,
    event_tracer: TangoEventTracer,
    dish_ids: str,
) -> None:
    """
    A method to put Telescope ON

    Args:
        central_node_mid: Fixture for a TMC CentralNode wrapper class
        event_tracer: Fixture for EventTracer class
        dish_ids: Dish Ids to be assigned to Subarray
    """

    assert central_node_mid.csp_master.ping() > 0
    assert central_node_mid.sdp_master.ping() > 0
    for dish_id in dish_ids.split(","):
        assert central_node_mid.dish_master_dict[dish_id].ping() > 0
        assert central_node_mid.dish_leaf_node_dict[dish_id].ping() > 0

    setup_dish_events(central_node_mid, event_tracer, dish_ids)
    event_tracer.subscribe_event(central_node_mid.csp_master, "State")
    event_tracer.subscribe_event(central_node_mid.sdp_master, "State")
    event_tracer.subscribe_event(
        central_node_mid.central_node, "telescopeState"
    )

    central_node_mid.move_to_on()

    assert_that(event_tracer).described_as(
        "FAILED ASSUMPTION AFTER ON COMMAND: "
        "CSP Master device"
        f"({central_node_mid.csp_master.dev_name()}) "
        "is expected to be in DevState ON",
    ).within_timeout(EVENT_TIMEOUT).has_change_event_occurred(
        central_node_mid.csp_master,
        "State",
        DevState.ON,
    )

    assert_that(event_tracer).described_as(
        "FAILED ASSUMPTION AFTER ON COMMAND: "
        "SDP Master device"
        f"({central_node_mid.sdp_master.dev_name()}) "
        "is expected to be in DevState ON",
    ).within_timeout(EVENT_TIMEOUT).has_change_event_occurred(
        central_node_mid.sdp_master,
        "State",
        DevState.ON,
    )

    for dish_id in ["SKA001", "SKA036", "SKA077", "SKA100"]:

        assert_that(event_tracer).described_as(
            "FAILED ASSUMPTION AFTER ON COMMAND: "
            "Dish Master device"
            f"({central_node_mid.dish_master_dict[dish_id].dev_name()}) "
            "is expected to be in DishMode STANDBY_FP",
        ).within_timeout(EVENT_TIMEOUT).has_change_event_occurred(
            central_node_mid.dish_master_dict[dish_id],
            "dishMode",
            DishMode.STANDBY_FP,
        )

        assert_that(event_tracer).described_as(
            "FAILED ASSUMPTION AFTER ON COMMAND: "
            "Dish Leaf Node device"
            f"({central_node_mid.dish_leaf_node_dict[dish_id].dev_name()}) "
            "is expected to be in DishMode STANDBY_FP",
        ).within_timeout(EVENT_TIMEOUT).has_change_event_occurred(
            central_node_mid.dish_leaf_node_dict[dish_id],
            "dishMode",
            DishMode.STANDBY_FP,
        )
    assert_that(event_tracer).described_as(
        "FAILED ASSUMPTION AFTER ON COMMAND: "
        "Central Node "
        f"({central_node_mid.central_node.dev_name()}) "
        "is expected to be in telescopeState ON",
    ).within_timeout(EVENT_TIMEOUT).has_change_event_occurred(
        central_node_mid.central_node,
        "telescopeState",
        DevState.ON,
    )

    event_tracer.clear_events()
