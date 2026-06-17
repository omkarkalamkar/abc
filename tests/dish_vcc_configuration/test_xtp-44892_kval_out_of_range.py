import json

import pytest
from pytest_bdd import parsers, scenario, then, when
from ska_tango_testing.mock.placeholders import Anything

from tests.dish_vcc_configuration.utils import get_load_dish_vcc_json
from tests.resources.test_harness.central_node_mid import CentralNodeWrapperMid
from tests.resources.test_harness.event_recorder import EventRecorder
from tests.resources.test_harness.utils.common_utils import JsonFactory
from tests.resources.test_support.common_utils.result_code import ResultCode


@pytest.mark.batch1
@pytest.mark.SKA_mid
@scenario(
    "../features/dish_vcc_initialization/xtp_44892_kval_out_of_range.feature",
    "TMC is able to reject command when kValue is out of range",
)
def test_dish_id_vcc_configuration_kvalue_out_of_range():
    """This test validate that TMC is able to reject the command
    if the kvalue is out of range (1 to 1177)
    """


@when(
    "I issue the command LoadDishCfg on TMC with Dish and VCC "
    "configuration file"
)
def invoke_load_dish_cfg(
    central_node_mid: CentralNodeWrapperMid,
    event_recorder: EventRecorder,
    command_input_factory: JsonFactory,
):
    """Call load_dish_cfg method which invoke LoadDishCfg
    command on CentralNode
    Args:
    :param central_node_mid: fixture for a TMC CentralNode Mid under test
    which provides simulated master devices
    :param event_recorder: fixture for a MockTangoEventCallbackGroup
    for validating the subscribing and receiving events.
    :param command_input_factory: fixture for creating input required
    for command
    """
    # Subscribe for longRunningCommandResult attribute
    event_recorder.subscribe_event(
        central_node_mid.central_node, "longRunningCommandResult"
    )
    # Prepare input for load dish configuration
    load_dish_cfg_json = get_load_dish_vcc_json(
        file_name="kvalue_out_of_range.json"
    )
    result_code, _ = central_node_mid.load_dish_vcc_configuration(
        load_dish_cfg_json
    )

    assert result_code == ResultCode.QUEUED


@then(parsers.parse("TMC rejects the command with error {error_message}"))
def test_tmc_rejects_command_with_error(
    error_message: str, event_recorder, central_node_mid
):
    """
    Test validate that command failed with error message
    :param error_message: error message to be validated for command rejection
    """

    event_recorder.subscribe_event(
        central_node_mid.central_node, "longRunningCommandResult"
    )

    assertion_data = event_recorder.has_change_event_occurred(
        central_node_mid.central_node,
        "longRunningCommandResult",
        (Anything, json.dumps([ResultCode.FAILED, error_message])),
        lookahead=5,
    )

    assert error_message in json.loads(assertion_data["attribute_value"][1])[1]
