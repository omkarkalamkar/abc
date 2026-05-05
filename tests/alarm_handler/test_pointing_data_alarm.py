"""Test module for TMC-DISH On functionality"""

import pytest
from numpy import nan as NaN
from pytest_bdd import given, scenario, then, when
from tango import DeviceProxy

from tests.resources.test_harness.helpers import retry_tango_command
from tests.resources.test_support.constant import (
    alarm_handler1,
    tmc_dish_leaf_node1,
)


@pytest.mark.batch2
@pytest.mark.SKA_mid
@scenario(
    "../features/test_harness/xtp_50437_nan_alarm.feature",
    "TMC mid raises an alarm when it encounters NaN"
    " in received pointing calibration",
)
def test_raise_alarm_on_reception_of_nan_from_sdp():
    """
    Test case to verify attribute quality gets set to ALARM
    when Dish Leaf Node finds NaN in received pointing calibration.

    """


@given("a TMC mid with already executed calibration scans")
def given_tmc_with_already_executed_calibration_scans(tmc_mid):
    """Given a TMC mid with already executed calibration scans"""
    tmc_mid.dish_leaf_node_list[
        0
    ].sdpQueueConnectorFqdn = (
        "mid-sdp/queueconnector/01/pointing_cal_{dish_id}"
    )


@when("the Dish Leaf Node receives NaN number from SDP")
def dish_leaf_node_receives_nan_from_sdp(tmc_mid):
    """Method that generates NaN"""
    # Unset values on some of the Dish Leaf Nodes
    queue_connector = DeviceProxy("mid-sdp/queueconnector/01")
    queue_connector.SetPointingCalSka001([1.0, NaN, 2.1])


@then("an alarm is raised for NaN found in last pointing data")
def test_load_alarm():
    """Handles the scenario where an alarm is raised due to NaN values
    found in the dish leaf node last pointing data.

    This method triggers the TMC alarm for the Alarm Handler instance,
    ensuring that the system correctly identifies and responds to NaN
    values in the pointing data
    """
    global alarm_handler, alarm_list
    alarm_handler = DeviceProxy(alarm_handler1)
    alarm_formula = (
        "tag=NaN_found_in_received_pointing_calibration;"
        "formula="
        f"({tmc_dish_leaf_node1}/lastPointingData.quality == ATTR_ALARM);"
        "priority=log;message=NaN found in received pointing calibration"
    )
    assert retry_tango_command(alarm_handler, "Load", alarm_formula)
    alarm_list = alarm_handler.alarmList
    assert ("nan_found_in_received_pointing_calibration") in alarm_list
    alarm_handler.Remove("nan_found_in_received_pointing_calibration")
