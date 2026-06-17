import pytest
from pytest_bdd import scenario, when

from tests.dish_vcc_configuration.utils import get_load_dish_vcc_json
from tests.resources.test_harness.central_node_mid import CentralNodeWrapperMid
from tests.resources.test_harness.event_recorder import EventRecorder
from tests.resources.test_harness.utils.common_utils import JsonFactory
from tests.resources.test_support.constant import COMMAND_COMPLETED


@pytest.mark.batch1
@pytest.mark.SKA_mid
@scenario(
    "../features/dish_vcc_initialization/"
    "xtp_44895_kval_validation_success.feature",
    "TMC Validates the kValue when all kvalues are different",
)
def test_kvalue_validation_all_kvalues_unique():
    """This test validate that TMC is able to validate that all
    kvalues are unique. For eg [1,2,3]
    """


@when("I issue the command LoadDishCfg on TMC with all different kValue")
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
    load_dish_cfg_json = get_load_dish_vcc_json("unique_kvalue.json")

    _, unique_id = central_node_mid.load_dish_vcc_configuration(
        load_dish_cfg_json
    )

    assert event_recorder.has_change_event_occurred(
        central_node_mid.central_node,
        "longRunningCommandResult",
        (unique_id[0], COMMAND_COMPLETED),
        lookahead=5,
    )
