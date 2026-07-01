"""
Test case to validate negative scenario for
   Dish Vcc map configuration feature
"""
import json

import pytest
from pytest_bdd import given, parsers, scenario, then, when
from ska_tango_base.control_model import AdminMode
from ska_tango_testing.mock.placeholders import Anything
from tango import DevState

from tests.conftest import LOGGER
from tests.resources.test_harness.helpers import (
    prepare_json_args_for_centralnode_commands,
)
from tests.resources.test_harness.utils.enums import SimulatorDeviceType
from tests.resources.test_support.common_utils.result_code import ResultCode
from tests.resources.test_support.constant import (
    COMMAND_COMPLETED,
    ERROR_PROPAGATION_DEFECT,
    RESET_DEFECT,
)


@pytest.mark.batch1
@pytest.mark.SKA_mid
@scenario(
    "../features/load_dish_cfg_command_negative_scenario.feature",
    "TMC returns error message when non existent file is provided "
    "in configuration",
)
def test_central_node_return_error_for_invalid_file():
    """This test validate that when non existent file
    provided in dish vcc configuration json then command is rejected
    with error
    Glossary:
    - "central_node_mid": fixture for a TMC CentralNode Mid under test
    which provides simulated master devices
    - "event_recorder": fixture for a MockTangoEventCallbackGroup
    for validating the subscribing and receiving events.
    - "simulator_factory": fixture for creating simulator devices for
    mid Telescope respectively.
    """


@pytest.mark.batch1
@pytest.mark.SKA_mid
@scenario(
    "../features/load_dish_cfg_command_negative_scenario.feature",
    "TMC returns error when invalid dish id is provided in configuration",
)
def test_central_node_return_error_for_invalid_dish_id():
    """This test validate that when invalid dish id provided
    in dish vcc map json then command is rejected with error
    """


@pytest.mark.batch1
@pytest.mark.SKA_mid
@scenario(
    "../features/load_dish_cfg_command_negative_scenario.feature",
    "TMC returns error when duplicate vcc id is provided in configuration",
)
def test_central_node_return_error_for_duplicate_vcc_id():
    """This test validate that when duplicate vcc id provided
    in dish vcc map json then command is rejected with error
    """


@pytest.mark.batch1
@pytest.mark.SKA_mid
@scenario(
    "../features/load_dish_cfg_command_negative_scenario.feature",
    "TMC handling exception from CSP Subarray",
)
def test_central_node_handle_exception():
    """This test validate that when exception is raised on csp controller
    device then the csp master should raise the error to central node and
    dishVccConfig and sourceDishVccConfig attributes are not updated at
    csp master leaf node device
    """


@pytest.mark.batch1
@pytest.mark.SKA_mid
@scenario(
    "../features/dish_vcc_initialization/xtp_78417.feature",
    "TMC reject LoadDishCfg command if existing dish vcc "
    "config is in progress",
)
def test_central_node_reject_load_dish_cfg():
    """This test validate that central node reject load dish cfg
    command if existing load dish cfg command is in progress
    Glossary:
    - "central_node_mid": fixture for a TMC CentralNode Mid under test
    which provides simulated master devices
    - "event_recorder": fixture for a MockTangoEventCallbackGroup
    for validating the subscribing and receiving events.
    - "simulator_factory": fixture for creating simulator devices for
    mid Telescope respectively.
    """


@given("a TMC")
def given_tmc():
    """Given a TMC"""


@given("CSP master in OFF state")
def csp_master_in_off_state(central_node_mid, event_recorder):
    """Move CSP master to OFF state"""
    event_recorder.subscribe_event(central_node_mid.csp_master, "State")
    central_node_mid.csp_master.adminmode = AdminMode.ONLINE
    assert event_recorder.has_change_event_occurred(
        central_node_mid.csp_master, "State", DevState.OFF
    )


@when(
    parsers.parse(
        "I issue the command LoadDishCfg on TMC with non "
        "existent file {file_name} in configuration"
    )
)
def invoke_load_dish_cfg(central_node_mid, command_input_factory, file_name):
    """Call load_dish_cfg method which invoke LoadDishCfg
    command on CentralNode
    """
    # Prepare input for load dish configuration
    load_dish_cfg_json = prepare_json_args_for_centralnode_commands(
        f"load_dish_cfg_{file_name}", command_input_factory
    )

    result_code, unique_id = central_node_mid.load_dish_vcc_configuration(
        load_dish_cfg_json
    )
    result_code == ResultCode.QUEUED
    pytest.command_id = unique_id[0]


@given("a LoadDishCfg command is currently in progress")
def load_dish_cfg_in_progress(
    central_node_mid, event_recorder, command_input_factory
):
    """Call load_dish_cfg method which invoke LoadDishCfg
    command on CentralNode
    """
    event_recorder.subscribe_event(
        central_node_mid.central_node, "DishVccCommandStatus"
    )
    event_recorder.subscribe_event(
        central_node_mid.central_node, "longRunningCommandResult"
    )
    # Prepare input for load dish configuration
    load_dish_cfg_json = prepare_json_args_for_centralnode_commands(
        "load_dish_cfg", command_input_factory
    )

    result_code, message = central_node_mid.load_dish_vcc_configuration(
        load_dish_cfg_json
    )
    pytest.command_result_code = result_code
    pytest.command_result_message = message
    assert event_recorder.has_change_event_occurred(
        central_node_mid.central_node,
        "DishVccCommandStatus",
        2,
    )


@when("another LoadDishCfg command is issued")
def invoke_another_load_dish_cfg(central_node_mid, command_input_factory):
    """Call load_dish_cfg method which invoke LoadDishCfg
    command on CentralNode
    """
    # Prepare input for load dish configuration
    # Prepare input for load dish configuration
    load_dish_cfg_json = prepare_json_args_for_centralnode_commands(
        "load_dish_cfg", command_input_factory
    )

    result_code, message = central_node_mid.load_dish_vcc_configuration(
        load_dish_cfg_json
    )
    pytest.failed_command_result_code = result_code
    pytest.failed_command_result_message = message


@then("TMC should reject the new LoadDishCfg command")
def test_tmc_rejects_load_dish_cfg():
    """Test validate that command failed with error message"""
    assert pytest.failed_command_result_code == ResultCode.REJECTED


@then("the in-progress LoadDishCfg command should complete")
def test_in_progress_load_dish_cfg_complete(central_node_mid, event_recorder):
    """Test validate that in progress load dish cfg complete"""
    assert event_recorder.has_change_event_occurred(
        central_node_mid.central_node,
        "longRunningCommandResult",
        (pytest.command_result_message[0], COMMAND_COMPLETED),
        lookahead=5,
    )


@then("the DishVccCommandStatus should transition to COMPLETED")
def test_dish_vcc_command_status_complete(central_node_mid, event_recorder):
    """Test validate that in progress load dish cfg complete"""
    assert event_recorder.has_change_event_occurred(
        central_node_mid.central_node,
        "DishVccCommandStatus",
        3,
        lookahead=5,
    )


@then(parsers.parse("TMC rejects the command with error {error_message}"))
def test_tmc_rejects_command_with_error(
    error_message, event_recorder, central_node_mid
):
    """Test validate that command failed with error message"""
    event_recorder.subscribe_event(
        central_node_mid.central_node, "longRunningCommandResult"
    )
    assertion_data = event_recorder.has_change_event_occurred(
        central_node_mid.central_node,
        "longRunningCommandResult",
        (pytest.command_id, Anything),
        lookahead=10,
    )
    LOGGER.info(
        ">>>>>>>>> command_result is: %s",
        assertion_data,
    )
    assert error_message in json.loads(assertion_data["attribute_value"][1])[1]


@then(
    parsers.parse(
        "TMC updates longrunningcommandresult with error {error_message}"
    )
)
def test_validates_longrunningcommandresult_with_error(
    error_message, central_node_mid, event_recorder
):
    """Test validate that command failed with error message"""
    # Subscribe for longRunningCommandResult attribute
    event_recorder.subscribe_event(
        central_node_mid.central_node, "longRunningCommandResult"
    )
    assertion_data = event_recorder.has_change_event_occurred(
        central_node_mid.central_node,
        "longRunningCommandResult",
        (
            pytest.command_id,
            Anything,
        ),
        lookahead=10,
    )
    LOGGER.info(
        ">>>>>>>>> command_result is: %s",
        assertion_data,
    )
    assert error_message in json.loads(assertion_data["attribute_value"][1])[1]


@then(
    "TMC rejects the command with error due to Duplicate Vcc ids found in json"
)
def test_tmc_rejects_command_for_duplicate_vcc_id(
    event_recorder, central_node_mid
):
    """Test validate that command failed with error message"""

    exp_msg = "Duplicate Vcc ids found in json"
    event_recorder.subscribe_event(
        central_node_mid.central_node, "longRunningCommandResult"
    )
    assertion_data = event_recorder.has_change_event_occurred(
        central_node_mid.central_node,
        "longRunningCommandResult",
        (
            pytest.command_id,
            Anything,
        ),
        lookahead=5,
    )
    assert exp_msg in json.loads(assertion_data["attribute_value"][1])[1]


@when(
    parsers.parse(
        "I issue the command LoadDishCfg on TMC with invalid {dish_id}"
    )
)
def invoke_command_with_invalid_dish_id(
    central_node_mid, command_input_factory, dish_id
):
    """Call load dish cfg command with invalid dish id"""
    # Prepare input for load dish configuration
    load_dish_cfg_json = prepare_json_args_for_centralnode_commands(
        "load_dish_cfg_invalid_dish_id", command_input_factory
    )

    result_code, uid = central_node_mid.load_dish_vcc_configuration(
        load_dish_cfg_json
    )
    assert result_code == ResultCode.QUEUED
    pytest.command_id = uid[0]


@when(
    "I issue the command LoadDishCfg on TMC with duplicate "
    "vcc id in configuration"
)
def invoke_command_with_duplicate_vcc_id(
    central_node_mid, command_input_factory
):
    """Call load dish cfg command with invalid duplicate vcc id"""
    # Prepare input for load dish configuration
    load_dish_cfg_json = prepare_json_args_for_centralnode_commands(
        "load_dish_cfg_duplicate_vcc_id", command_input_factory
    )

    result_code, uid = central_node_mid.load_dish_vcc_configuration(
        load_dish_cfg_json
    )
    pytest.command_id = uid[0]
    result_code == ResultCode.QUEUED


@when(
    "I issue the command LoadDishCfg on TMC "
    "and CSP Controller raises an exception"
)
def invoke_command_load_cfg_on_defective_csp(
    central_node_mid,
    event_recorder,
    command_input_factory,
    simulator_factory,
):
    """Call load_dish_cfg method which invoke LoadDishCfg
    command on CentralNode
    Args:
    :param central_node_mid: fixture for a TMC CentralNode Mid under test
    which provides simulated master devices
    :param event_recorder: fixture for a MockTangoEventCallbackGroup
    for validating the subscribing and receiving events.
    :param simulator_factory: fixture for creating simulator devices for
    mid Telescope respectively.
    :param command_input_factory: fixture for creating input required
    for command
    """
    event_recorder.subscribe_event(
        central_node_mid.central_node, "longRunningCommandResult"
    )
    event_recorder.subscribe_event(
        central_node_mid.csp_master_leaf_node, "longRunningCommandResult"
    )
    # Prepare input for load dish configuration
    load_dish_cfg_json = prepare_json_args_for_centralnode_commands(
        "load_dish_cfg", command_input_factory
    )
    csp_sim = simulator_factory.get_or_create_simulator_device(
        SimulatorDeviceType.MID_CSP_MASTER_DEVICE
    )
    pytest.initial_dishVccConfig = (
        central_node_mid.csp_master_leaf_node.dishVccConfig
    )
    pytest.initial_sourceDishVccConfig = (
        central_node_mid.csp_master_leaf_node.sourceDishVccConfig
    )

    csp_sim.SetDefective(ERROR_PROPAGATION_DEFECT)
    _, unique_id = central_node_mid.load_dish_vcc_configuration(
        load_dish_cfg_json
    )
    cspln = central_node_mid.csp_master_leaf_node.dev_name()

    pytest.exception_msg = (
        f'"Exception occurred on the following devices: {cspln}'
    )

    pytest.command_result = event_recorder.has_change_event_occurred(
        central_node_mid.central_node,
        "longRunningCommandResult",
        (unique_id[0], Anything),
        lookahead=10,
    )
    LOGGER.info("LRCR: %s", pytest.command_result)
    LOGGER.info(
        "LRCR: %s", central_node_mid.central_node.longRunningCommandResult
    )
    csp_sim.SetDefective(RESET_DEFECT)


@then(
    "dishVccConfig and sourceDishVccConfig attributes "
    "remains unchanged on CSP Master Leaf Node"
)
def check_sys_param_source_sys_param_attributes(central_node_mid):
    """Test validate that dishVccConfig and sourceDishVccConfig attributes
    are not updated after error
    """
    assert (
        pytest.initial_dishVccConfig
        == central_node_mid.csp_master_leaf_node.dishVccConfig
    )
    assert (
        pytest.initial_sourceDishVccConfig
        == central_node_mid.csp_master_leaf_node.sourceDishVccConfig
    )


@then(parsers.parse("command returns with error message {error_message}"))
def check_return_msg():
    """Test validate that command failed with error message"""
    LOGGER.info(
        "command_result is: %s",
        pytest.command_result["attribute_value"],
    )
    assert pytest.exception_msg in pytest.command_result["attribute_value"][1]
