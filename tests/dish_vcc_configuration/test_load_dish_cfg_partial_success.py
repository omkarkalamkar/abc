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
    "TMC allows partial success for load Dish and VCC configuration file",
)
def test_dish_id_vcc_partial_success():
    """This test case validates LoadDishCfg command
    fails if it fails on all the dishes.
    """


@given("a TMC")
def given_tmc(central_node_mid):
    """Given a TMC"""


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


@given("one dish is working as expected out of allocated dishes")
def dishes_set_to_throws_exception(simulator_factory):
    """Move Telescope to ON state
    Args
        simulator_factory: fixture for SimulatorFactory class,
        which provides simulated subarray and master devices
        event_recorder: fixture for EventRecorder class
    """

    _, _, *dish_master_sims = get_master_device_simulators(simulator_factory)
    pytest.errorless_dish = dish_master_sims.pop(0)
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


@then("TMC loaddishcfg gets succeed partially")
def tmc_loads_dish_cfg_partial_success(central_node_mid, event_recorder):
    """Test validate that in progress load dish cfg complete
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


@when("I try to invoke loaddishcfg in obsstate empty")
def invoke_load_dish_cfg_in_empty_obsstate(central_node_mid):
    """Test validate that in progress load dish cfg complete
    Args
    :param central_node_mid: fixture for a TMC CentralNode Mid under test
    which provides simulated master devices
    """

    _, unique_id = central_node_mid.load_dish_vcc_configuration(
        json.dumps(TMC_MID_VCC_CONFIG_INPUT)
    )

    pytest.command_uid = unique_id[0]


@then("TMC not allow loaddishcfg as CSP controller is in ON state")
def tmc_not_allow_loaddishcfg(central_node_mid, event_recorder):
    """TMC not allows loaddishcfg as CSP controller is in ON state
    Args
    :param central_node_mid: fixture for a TMC CentralNode Mid under test
    which provides simulated master devices
    :param event_recorder: fixture for a MockTangoEventCallbackGroup
    for validating the subscribing and receiving events.
    """

    event_recorder.subscribe_event(central_node_mid.csp_master, "State")
    msg = "LoadDishCfg command is allowed in CSP Master DevState.OFF only."
    err_msg = f"[6, {msg}]"
    event_recorder.has_change_event_occurred(
        central_node_mid.central_node,
        "longRunningCommandResult",
        (pytest.command_uid, err_msg),
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


@when("TMC have kValue issue on any of the dish")
def dish_with_kvalue_issue(central_node_mid):
    """TMC mid dish with kValue issue on any of the dish
    Args
    :param central_node_mid: fixture for a TMC CentralNode Mid under test
    which provides simulated master devices
    """

    pytest.kvalue = pytest.errorless_dish.kValue
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


@then("TMC rejects the assign resources command if invoked")
def tmc_rejects_assign_resources(central_node_mid, event_recorder):
    """TMC mid rejects the assign resources command
    if invoked when any of the dish has kValue issue
    Args
    :param central_node_mid: fixture for a TMC CentralNode Mid under test
    which provides simulated master devices
    :param event_recorder: fixture for a MockTangoEventCallbackGroup
    for validating the subscribing and receiving events.
    """

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

    pytest.errorless_dish.SetKValue(pytest.kvalue)
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
