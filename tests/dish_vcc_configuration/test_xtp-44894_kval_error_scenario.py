import pytest
from pytest_bdd import scenario, then, when
from ska_tango_base.control_model import HealthState

from tests.dish_vcc_configuration.utils import get_load_dish_vcc_json
from tests.resources.test_harness.central_node_mid import CentralNodeWrapperMid
from tests.resources.test_harness.event_recorder import EventRecorder
from tests.resources.test_harness.helpers import (
    check_for_device_command_event,
    prepare_json_args_for_commands,
)
from tests.resources.test_harness.subarray_node import SubarrayNodeWrapper
from tests.resources.test_harness.utils.common_utils import JsonFactory
from tests.resources.test_support.common_utils.result_code import ResultCode
from tests.resources.test_support.constant import COMMAND_COMPLETED


@pytest.mark.batch1
@pytest.mark.SKA_mid
@scenario(
    "../features/dish_vcc_initialization/xtp_44894_kvalue_validation.feature",
    "TMC Validates the kValue when multiple kvalues are same",
)
def test_kvalue_validation_error_scenario():
    """This test validate that TMC is able to stop command operation when the
    multiple kvalues are same. For eg [1,1,2]
    """


@when("I issue the command LoadDishCfg on TMC with multiple same kValue")
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
        file_name="mulitple_same_kvalue.json"
    )

    _, unique_id = central_node_mid.load_dish_vcc_configuration(
        load_dish_cfg_json
    )

    assert event_recorder.has_change_event_occurred(
        central_node_mid.central_node,
        "longRunningCommandResult",
        (unique_id[0], COMMAND_COMPLETED),
        lookahead=5,
    )


@when("I invoke Configure command on TMC")
def invoke_configure(
    subarray_node: SubarrayNodeWrapper,
    command_input_factory: JsonFactory,
):
    """
    A method to invoke Configure command
    :param subarray_node: fixture for a TMC SubarrayNode under test
    :param command_input_factory: fixture for creating input required
    for command
    """
    input_json = prepare_json_args_for_commands(
        "configure_mid", command_input_factory
    )
    pytest.result, pytest.unique_id = subarray_node.execute_transition(
        "Configure", argin=input_json
    )
    assert pytest.unique_id[0].endswith("Configure")
    assert pytest.result[0] == ResultCode.QUEUED


@then("the command is failed and the health state of the subarray is DEGRADED")
def test_tmc_rejects_command_with_error(
    subarray_node: SubarrayNodeWrapper, event_recorder: EventRecorder
):
    """
    Test validate that command failed with error message
    :param subarray_node: fixture for a TMC SubarrayNode under test
    :param event_recorder: fixture for a MockTangoEventCallbackGroup
    for validating the subscribing and receiving events.
    """
    event_recorder.subscribe_event(
        subarray_node.subarray_node, "longRunningCommandResult"
    )
    exception_message = "K-values must be either all same or all different"
    assert check_for_device_command_event(
        subarray_node.subarray_node,
        "longRunningCommandResult",
        exception_message,
        event_recorder,
        "Configure",
    )
    event_recorder.subscribe_event(subarray_node.subarray_node, "healthState")
    assert event_recorder.has_change_event_occurred(
        subarray_node.subarray_node,
        "healthState",
        HealthState.DEGRADED,
    )
