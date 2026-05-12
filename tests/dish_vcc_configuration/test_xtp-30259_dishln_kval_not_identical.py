"""Test module for TMC-DISH Dish-VCC k-value validation functionality"""

import json
from datetime import datetime

import pytest
from pytest_bdd import given, scenario, then, when
from tango import DevState

from tests.conftest import LOGGER
from tests.resources.test_harness.helpers import (
    wait_and_validate_device_attribute_value,
)
from tests.resources.test_support.common_utils.result_code import ResultCode
from tests.resources.test_support.constant import tmc_csp_master_leaf_node


@pytest.mark.SKA_tmc_mid_device_restart
@pytest.mark.SKA_mid
@scenario(
    "../features/dish_vcc_initialization/"
    "xtp_30259_dishln_kvalue_not_identical.feature",
    "TMC Validates and Reports K-Value discrepancy in Dish Leaf Nodes",
)
def test_tmc_validate_dln_kvalue_not_identical():
    """
    Test case to verify Dish-VCC validation functionality

    Glossary:
        - "event_recorder": fixture for EventRecorder class
        - "tmc_mid": fixture to give TMC mid device server commands
    """


@given("a TMC with already loaded Dish-VCC map version")
def given_tmc_with_already_loaded_dish_vcc_config_version(tmc_mid):
    """
    Given a TMC with loaded Dish-VCC map version
    """
    cspmln_validation_string = "TMC and CSP Master Dish Vcc Version is Same"
    central_node_dish_vcc_validation_status = {
        "dish": "ALL DISH OK",
        tmc_csp_master_leaf_node: cspmln_validation_string,
    }
    assert (
        json.loads(tmc_mid.DishVccValidationStatus)
        == central_node_dish_vcc_validation_status
    )
    assert tmc_mid.IsDishVccConfigSet


@when("the Dish Leaf Node is restarted")
def restart_the_dish_leaf_nodes(tmc_mid):
    """Restart the dish leaf nodes"""
    # Set DLN k-values which are not equal to its respective dish manager
    try:
        tmc_mid.central_node.dish_leaf_node_list[1].kValue = 9
        # Set dish manager k-value which are not equal to its respective
        # dish leaf node
        tmc_mid.central_node.dish_master_list[2].SetKValue(10)
    except Exception as ex:
        LOGGER.error(
            "Exception %s occurred at with error: %s",
            ex,
            datetime.utcnow().strftime("%d/%m/%Y %H:%M:%S:%f"),
        )
    # [0, 1, 2, 3] are index for dish leaf node list
    tmc_mid.RestartServer("DISHLN_1")
    tmc_mid.RestartServer("DISHLN_2")


@when(
    "the Dish Leaf Node finds the k-value set on either of"
    + " the Dish Leaf Node and Dish Manager are not identical"
)
def check_dishln_is_on_and_kvalue_validation_accomplished(tmc_mid):
    """Method to check dish leaf node are up and k-value validation
    is completed"""
    assert wait_and_validate_device_attribute_value(
        tmc_mid.central_node.dish_leaf_node_list[1], "State", DevState.ON
    )
    assert wait_and_validate_device_attribute_value(
        tmc_mid.central_node.dish_leaf_node_list[2], "State", DevState.ON
    )
    assert wait_and_validate_device_attribute_value(
        tmc_mid.central_node.dish_leaf_node_list[1],
        "kValueValidationResult",
        str(int(ResultCode.FAILED)),
    )
    assert wait_and_validate_device_attribute_value(
        tmc_mid.central_node.dish_leaf_node_list[2],
        "kValueValidationResult",
        str(int(ResultCode.FAILED)),
    )


@then("Dish Leaf Node reports the discrepancy to the Central Node")
def check_kvalue_validation_result_event_received(tmc_mid, event_recorder):
    """Method to check Central Node received the kValueValidation
    attribute event from respective dish leaf nodes."""
    event_recorder.subscribe_event(
        tmc_mid.central_node.dish_leaf_node_list[1], "kValueValidationResult"
    )
    event_recorder.subscribe_event(
        tmc_mid.central_node.dish_leaf_node_list[2], "kValueValidationResult"
    )
    assert event_recorder.has_change_event_occurred(
        tmc_mid.central_node.dish_leaf_node_list[1],
        "kValueValidationResult",
        str(int(ResultCode.FAILED)),
    )
    assert event_recorder.has_change_event_occurred(
        tmc_mid.central_node.dish_leaf_node_list[2],
        "kValueValidationResult",
        str(int(ResultCode.FAILED)),
    )


@then(
    "the Central Node reports the same and prohibits any further"
    + " observation command execution"
)
def check_value_of_isdishvccconfigset_on_central_node(tmc_mid):
    """Method to verify isDishVccConfig attribute is true or
    false after dish leaf node report."""
    cspmln_validation_string = "TMC and CSP Master Dish Vcc Version is Same"
    central_node_dish_vcc_validation_status = {
        "SKA036": "k-value not identical",
        "SKA077": "k-value not identical",
        tmc_csp_master_leaf_node: cspmln_validation_string,
    }
    assert wait_and_validate_device_attribute_value(
        tmc_mid.central_node.central_node,
        "DishVccValidationStatus",
        json.dumps(central_node_dish_vcc_validation_status),
        is_json=True,
    )
    assert not tmc_mid.IsDishVccConfigSet
    # Central Node does not allow any command execution
    with pytest.raises(Exception) as e:
        tmc_mid.TelescopeOn()
    assert "Dish Vcc Config not Set" in str(e.value)
    # Restore to previous k-value
    tmc_mid.central_node.dish_leaf_node_list[1].SetKValue(222)
    tmc_mid.central_node.dish_leaf_node_list[2].SetKValue(333)

    assert wait_and_validate_device_attribute_value(
        tmc_mid.central_node.central_node,
        "isDishVccConfigSet",
        True,
    )
