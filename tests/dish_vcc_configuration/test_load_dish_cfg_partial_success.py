import json
from time import sleep

import pytest
from pytest_bdd import given, scenario, then, when
from ska_control_model import AdminMode
from ska_tango_testing.mock.placeholders import Anything
from tango import DevState

from tests.resources.test_harness.helpers import get_master_device_simulators
from tests.resources.test_support.constant import (
    COMMAND_COMPLETED,
    ERROR_PROPAGATION_DEFECT,
    LOGGER,
    RESET_DEFECT,
    TMC_MID_VCC_CONFIG_INPUT,
)


@pytest.mark.batch1
@pytest.mark.SKA_mid
@pytest.mark.test_dish_vcc
@scenario(
    "../dish_vcc_initialization/features/"
    "load_dish_cfg_partial_success.feature",
    "TMC allows partial success for load Dish and VCC configuration file",
)
def test_dish_id_vcc_configuration_failure():
    """This test case validates LoadDishCfg command
    fails if it fails on all the dishes.
    """


@given("a TMC")
def given_tmc(central_node_mid):
    """Given a TMC"""

    # Verify no LoadDishCfg command is in progress
    timeout = 100
    while timeout > 0:
        # 3 = DishVccCommandStatus.FAILED
        if int(central_node_mid.central_node.DishVccCommandStatus) == 3:
            break
        timeout -= 1
        sleep(1)


@given("CSP Controller is in OFF state")
def csp_master_in_off_state(central_node_mid, event_recorder):
    """CSP controller is in OFF state
    Args
    :param central_node_mid: fixture for a TMC CentralNode Mid under test
    which provides simulated master devices
    :param event_recorder: fixture for a MockTangoEventCallbackGroup
    for validating the subscribing and receiving events.
    """
    event_recorder.subscribe_event(central_node_mid.csp_master, "State")
    central_node_mid.csp_master.adminmode = AdminMode.ONLINE
    assert event_recorder.has_change_event_occurred(
        central_node_mid.csp_master, "State", DevState.OFF
    )


@given("All the dishes set to throw exception")
def dishes_set_to_throws_exception(simulator_factory):
    """Move Telescope to ON state
    Args
        simulator_factory: fixture for SimulatorFactory class,
        which provides simulated subarray and master devices
        event_recorder: fixture for EventRecorder class
    """

    _, _, *dish_master_sims = get_master_device_simulators(simulator_factory)
    pytest.dish_master_sims = dish_master_sims
    for dish_master_sim in dish_master_sims:
        dish_master_sim.SetDefective(ERROR_PROPAGATION_DEFECT)


@when(
    "I issue the command LoadDishCfg on TMC with Dish and VCC "
    "configuration file"
)
def invoke_load_dish_cfg(
    central_node_mid,
):
    """Call load_dish_cfg method which invoke LoadDishCfg
    command on CentralNode
    Args:
    :param central_node_mid: fixture for a TMC CentralNode Mid under test
    which provides simulated master devices
    """

    _, unique_id = central_node_mid.load_dish_vcc_configuration(
        json.dumps(TMC_MID_VCC_CONFIG_INPUT)
    )

    pytest.command_uid = unique_id[0]


@then("TMC fails to set the Dish-VCC map")
def tmc_fails_to_set_vcc_map(central_node_mid, event_recorder):
    """Test validate that in progress load dish cfg complete"""
    # Subscribe for longRunningCommandResult attribute

    event_recorder.subscribe_event(
        central_node_mid.central_node, "longRunningCommandResult"
    )

    event_recorder.subscribe_event(
        central_node_mid.central_node, "isDishVccConfigSet"
    )

    err_msg = "LoadDishCfg command failed"

    event_recorder.has_change_event_occurred(
        central_node_mid.central_node,
        "isDishVccConfigSet",
        False,
        lookahead=5,
    )

    assertion_data = event_recorder.has_change_event_occurred(
        central_node_mid.central_node,
        "longRunningCommandResult",
        (pytest.command_uid, Anything),
        lookahead=5,
    )

    LOGGER.info(
        "Command_result is: %s %s",
        central_node_mid.central_node.DishVccCommandStatus,
        assertion_data,
    )
    assert err_msg in json.loads(assertion_data["attribute_value"][1])[1]
    for dish_master_sim in pytest.dish_master_sims:
        dish_master_sim.SetDefective(RESET_DEFECT)

    # Make Dish VCC flag true
    _, unique_id = central_node_mid.load_dish_vcc_configuration(
        json.dumps(TMC_MID_VCC_CONFIG_INPUT)
    )

    event_recorder.has_change_event_occurred(
        central_node_mid.central_node,
        "isDishVccConfigSet",
        True,
        lookahead=5,
    )

    event_recorder.has_change_event_occurred(
        central_node_mid.central_node,
        "longRunningCommandResult",
        (unique_id[0], COMMAND_COMPLETED),
        lookahead=5,
    )
