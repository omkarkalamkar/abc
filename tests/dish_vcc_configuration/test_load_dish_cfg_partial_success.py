import ast
import json
from time import sleep

import pytest
from pytest_bdd import given, scenario, then, when
from ska_control_model import AdminMode
from ska_integration_test_harness.actions.utils.generate_eb_pb_ids import (
    generate_eb_pb_ids,
)
from ska_tango_testing.mock.placeholders import Anything
from tango import DevState

from tests.conftest import LOGGER
from tests.resources.test_harness.helpers import get_master_device_simulators
from tests.resources.test_harness.utils.enums import ResultCode
from tests.resources.test_support.constant import (
    COMMAND_COMPLETED,
    ERROR_PROPAGATION_DEFECT,
    RESET_DEFECT,
    TMC_MID_VCC_CONFIG_INPUT,
)
from tests.tmc_csp_new_ITH.utils.my_file_json_input import MyFileJSONInput


@pytest.mark.batch1
@pytest.mark.SKA_mid
@scenario(
    "../features/dish_vcc_initialization/"
    "load_dish_cfg_partial_success.feature",
    "TMC allows partial success for LoadDishCfg and blocks further commands "
    "on device state and kValue issues",
)
def test_dish_id_vcc_partial_success():
    """This test case validates LoadDishCfg command
    partial success if it gets passed on any of the dish.
    """


@given(
    "a TMC with CSP Controller in OFF state and one functional dish out "
    "of allocated dishes"
)
def csp_master_in_off_state(
    central_node_mid, event_recorder, simulator_factory
):
    """CSP controller is in OFF state and only one dish is working as expected
    Args
    :param central_node_mid: fixture for a TMC CentralNode Mid under test
    which provides simulated master devices
    :param event_recorder: fixture for a MockTangoEventCallbackGroup
    for validating the subscribing and receiving events.
    :param simulator_factory: fixture for SimulatorFactory class,
    which provides simulated subarray and master devices
    event_recorder: fixture for EventRecorder class
    """
    event_recorder.subscribe_event(central_node_mid.csp_master, "State")
    central_node_mid.csp_master.adminmode = AdminMode.ONLINE
    assert event_recorder.has_change_event_occurred(
        central_node_mid.csp_master, "State", DevState.OFF
    )

    _, _, *dish_master_sims = get_master_device_simulators(simulator_factory)
    pytest.errorless_dish = dish_master_sims.pop(0)
    pytest.dish_master_sims = dish_master_sims
    for dish_master_sim in dish_master_sims:
        dish_master_sim.SetDefective(ERROR_PROPAGATION_DEFECT)


@when("I issue LoadDishCfg with Dish and VCC configuration file")
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


@then("LoadDishCfg completes with partial success")
def tmc_loads_dish_cfg_partial_success(central_node_mid, event_recorder):
    """LoadDishCfg completes its execution with partial success
    Args
    :param central_node_mid: fixture for a TMC CentralNode Mid under test
    which provides simulated master devices
    :param event_recorder: fixture for a MockTangoEventCallbackGroup
    for validating the subscribing and receiving events.
    """

    # Subscribe for longRunningCommandResult attribute
    event_recorder.subscribe_event(
        central_node_mid.central_node, "longRunningCommandResult"
    )

    event_recorder.subscribe_event(
        central_node_mid.central_node, "isDishVccConfigSet"
    )

    err_msg = "LoadDishCfg completed with partial success"

    event_recorder.has_change_event_occurred(
        central_node_mid.central_node,
        "isDishVccConfigSet",
        True,
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

    assert json.loads(assertion_data["attribute_value"][1])[0] == (
        ResultCode.OK
    )
    error_message = json.loads(assertion_data["attribute_value"][1])[1]
    assert err_msg in error_message
    brace_index = error_message.find("{")
    dict_str = error_message[brace_index:]
    error_dict = ast.literal_eval(dict_str)
    msg = "Exception occurred, command failed"
    assert all(msg in error for error in error_dict.values())

    for dish_master_sim in pytest.dish_master_sims:
        dish_master_sim.SetDefective(RESET_DEFECT)

    # Make Dish VCC flag true
    _, unique_id = central_node_mid.load_dish_vcc_configuration(
        json.dumps(TMC_MID_VCC_CONFIG_INPUT)
    )

    event_recorder.has_change_event_occurred(
        central_node_mid.central_node,
        "longRunningCommandResult",
        (unique_id[0], COMMAND_COMPLETED),
        lookahead=5,
    )

    assert central_node_mid.central_node.isDishVccConfigSet

    event_recorder.subscribe_event(central_node_mid.csp_master, "State")
    central_node_mid.move_to_on()
    assert event_recorder.has_change_event_occurred(
        central_node_mid.csp_master, "State", DevState.ON
    )


@then(
    "TMC does not allow LoadDishCfg in any ObsState as CSP " "Controller is ON"
)
def invoke_load_dish_cfg_in_any_obsstate(central_node_mid, event_recorder):
    """Invoke load dish cfg in any obsState
    Args
    :param central_node_mid: fixture for a TMC CentralNode Mid under test
    which provides simulated master devices
    :param event_recorder: fixture for a MockTangoEventCallbackGroup
    for validating the subscribing and receiving events.
    """

    _, unique_id = central_node_mid.load_dish_vcc_configuration(
        json.dumps(TMC_MID_VCC_CONFIG_INPUT)
    )

    event_recorder.subscribe_event(central_node_mid.csp_master, "State")
    msg = "LoadDishCfg command is allowed in CSP Master DevState.OFF only."
    err_msg = f"[6, {msg}]"
    event_recorder.has_change_event_occurred(
        central_node_mid.central_node,
        "longRunningCommandResult",
        (unique_id[0], err_msg),
        lookahead=5,
    )

    assert not central_node_mid.central_node.isDishVccConfigSet

    central_node_mid.csp_master.off([])

    assert event_recorder.has_change_event_occurred(
        central_node_mid.csp_master,
        "State",
        DevState.OFF,
        lookahead=10,
    )

    _, unique_id = central_node_mid.load_dish_vcc_configuration(
        json.dumps(TMC_MID_VCC_CONFIG_INPUT)
    )

    event_recorder.has_change_event_occurred(
        central_node_mid.central_node,
        "longRunningCommandResult",
        (unique_id[0], COMMAND_COMPLETED),
        lookahead=5,
    )
    assert central_node_mid.central_node.isDishVccConfigSet
    central_node_mid.csp_master.on([])
    assert event_recorder.has_change_event_occurred(
        central_node_mid.csp_master, "State", DevState.ON
    )


@then("TMC does not allow AssignResources as kValue issue on dish")
def dish_with_kvalue_issue(central_node_mid, event_recorder):
    """TMC mid dish(es) with kValue issue on any of the dish
    Args
    :param central_node_mid: fixture for a TMC CentralNode Mid under test
    which provides simulated master devices
    :param event_recorder: fixture for a MockTangoEventCallbackGroup
    for validating the subscribing and receiving events.
    """

    kvalue = pytest.errorless_dish.kValue
    pytest.errorless_dish.SetKValue(234)
    timeout = 10
    flag = False
    while timeout > 0:
        status = json.loads(
            central_node_mid.central_node.DishVccValidationStatus
        )
        if any("not identical" in value for value in status.values()):
            flag = True
            break
        timeout -= 1
        sleep(1)
    assert flag

    error_msg = "Can't assign receptors with k-value issues"
    assign_input = MyFileJSONInput("centralnode", "assign_resources_mid")
    cmd_input = generate_eb_pb_ids(assign_input)
    LOGGER.info("Invoking AssignResources command: %s", assign_input)
    _, uid = central_node_mid.central_node.AssignResources(cmd_input.as_str())
    assertion_data = event_recorder.has_change_event_occurred(
        central_node_mid.central_node,
        "longRunningCommandResult",
        (uid[0], Anything),
        lookahead=5,
    )

    LOGGER.info(
        "Command_result is: %s %s",
        central_node_mid.central_node.DishVccValidationStatus,
        assertion_data,
    )

    assert json.loads(assertion_data["attribute_value"][1])[0] == (
        ResultCode.NOT_ALLOWED
    )

    error_message = json.loads(assertion_data["attribute_value"][1])[1]
    assert error_msg in error_message

    pytest.errorless_dish.SetKValue(kvalue)
    timeout = 10
    while timeout > 0:
        status = json.loads(
            central_node_mid.central_node.DishVccValidationStatus
        )
        if any("ALL DISH OK" in value for value in status.values()):
            flag = True
            break
        timeout -= 1
        sleep(1)
    assert flag
