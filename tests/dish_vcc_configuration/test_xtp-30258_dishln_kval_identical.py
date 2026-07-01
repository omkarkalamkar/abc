"""Test module for TMC-DISH Dish-VCC k-value validation functionality"""

import json

import pytest
from pytest_bdd import given, scenario, then, when
from tango import DevState

from tests.resources.test_harness.helpers import (
    LOGGER,
    wait_and_validate_device_attribute_value,
)
from tests.resources.test_support.common_utils.result_code import ResultCode
from tests.resources.test_support.constant import tmc_csp_master_leaf_node


@pytest.mark.SKA_tmc_mid_device_restart
@pytest.mark.SKA_mid
@scenario(
    "../features/dish_vcc_initialization/"
    "xtp_30258_dishln_kvalue_identical.feature",
    "TMC Validates and Reports K-Value set in Dish Leaf Nodes",
)
def test_tmc_validate_dln_kvalue_identical():
    """
    Test case to verify Dish-VCC validation functionality

    Glossary:
        - "event_recorder": fixture for EventRecorder class
        - "tmc_mid": fixture to give TMC mid device server commands
    """


@given("a TMC with already loaded Dish-VCC map version")
def given_tmc_with_already_loaded_dish_vcc_config_version(tmc_mid):
    """Given a TMC with loaded Dish-VCC map version"""
    cspmln_validation_string = "TMC and CSP Master Dish Vcc Version is Same"
    LOGGER.info(f"Expected validation status: {cspmln_validation_string}")
    LOGGER.info(f"VCC validation status: {tmc_mid.DishVccValidationStatus}")
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
    # [0, 1, 2, 3] are index for dish leaf node list
    tmc_mid.RestartServer("DISHLN_0")
    tmc_mid.RestartServer("DISHLN_1")
    tmc_mid.RestartServer("DISHLN_2")
    tmc_mid.RestartServer("DISHLN_3")


@when(
    "the Dish Leaf Node verifies k-value set on Dish Leaf Node"
    + " and Dish Manager are identical"
)
def check_dishln_is_on_and_kvalue_validation_accomplished(tmc_mid):
    """Method to check dish leaf node are up and k-value
    validation is completed"""
    assert wait_and_validate_device_attribute_value(
        tmc_mid.central_node.dish_leaf_node_list[0], "State", DevState.ON
    )
    assert wait_and_validate_device_attribute_value(
        tmc_mid.central_node.dish_leaf_node_list[1], "State", DevState.ON
    )
    assert wait_and_validate_device_attribute_value(
        tmc_mid.central_node.dish_leaf_node_list[2], "State", DevState.ON
    )
    assert wait_and_validate_device_attribute_value(
        tmc_mid.central_node.dish_leaf_node_list[3], "State", DevState.ON
    )
    assert wait_and_validate_device_attribute_value(
        tmc_mid.central_node.dish_leaf_node_list[0],
        "kValueValidationResult",
        str(int(ResultCode.OK)),
    )
    assert wait_and_validate_device_attribute_value(
        tmc_mid.central_node.dish_leaf_node_list[1],
        "kValueValidationResult",
        str(int(ResultCode.OK)),
    )
    assert wait_and_validate_device_attribute_value(
        tmc_mid.central_node.dish_leaf_node_list[2],
        "kValueValidationResult",
        str(int(ResultCode.OK)),
    )
    assert wait_and_validate_device_attribute_value(
        tmc_mid.central_node.dish_leaf_node_list[3],
        "kValueValidationResult",
        str(int(ResultCode.OK)),
    )


@then("Dish Leaf Node reports it to the Central Node")
def check_kvalue_validation_result_event_received(tmc_mid, event_recorder):
    """Method to check Central Node received the kValueValidation
    attribute event from respective dish leaf nodes.
    """
    for i in range(0, len(tmc_mid.central_node.dish_leaf_node_list)):
        event_recorder.subscribe_event(
            tmc_mid.central_node.dish_leaf_node_list[i],
            "kValueValidationResult",
        )
    assert event_recorder.has_change_event_occurred(
        tmc_mid.central_node.dish_leaf_node_list[0],
        "kValueValidationResult",
        str(int(ResultCode.OK)),
    )
    assert event_recorder.has_change_event_occurred(
        tmc_mid.central_node.dish_leaf_node_list[1],
        "kValueValidationResult",
        str(int(ResultCode.OK)),
    )
    assert event_recorder.has_change_event_occurred(
        tmc_mid.central_node.dish_leaf_node_list[2],
        "kValueValidationResult",
        str(int(ResultCode.OK)),
    )
    assert event_recorder.has_change_event_occurred(
        tmc_mid.central_node.dish_leaf_node_list[3],
        "kValueValidationResult",
        str(int(ResultCode.OK)),
    )


@then(
    "the Central Node continues with current operation as"
    + " their are no discrepancies"
)
def check_value_of_isdishvccconfigset_on_central_node(tmc_mid):
    """Method to verify isDishVccConfig attribute is true or
    false after dish leaf node report."""
    assert wait_and_validate_device_attribute_value(
        tmc_mid.central_node.central_node,
        "isDishVccConfigSet",
        True,
    )
    assert tmc_mid.IsDishVccConfigSet
