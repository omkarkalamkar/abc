import json

import pytest
from pytest_bdd import given, scenario, then, when
from tango import DevState

from tests.resources.test_harness.helpers import (
    device_attribute_changed,
    get_master_device_simulators,
    prepare_json_args_for_centralnode_commands,
)
from tests.resources.test_support.constant import COMMAND_COMPLETED
from tests.resources.test_support.enum import DishMode


@pytest.mark.batch1
@pytest.mark.SKA_mid
@scenario(
    "../features/load_dish_cfg_command.feature",
    "TMC is able to load Dish and VCC configuration file",
)
def test_dish_id_vcc_configuration():
    """This test validate that TMC is able to load the dish vcc
    configuration file provided to LoadDishCfg command.
    Validate that k-numbers set on dish masters
    Validate dishVccConfig and sourceDishVccConfig attribute set on csp master
    leaf node
    """


@given("a TMC")
def given_tmc():
    """Given a TMC"""


@given("Telescope is in ON state")
def telescope_in_on_state(central_node_mid, event_recorder):
    """Move Telescope to ON state
    Args
    :param central_node_mid: fixture for a TMC CentralNode Mid under test
    which provides simulated master devices
    :param event_recorder: fixture for a MockTangoEventCallbackGroup
    for validating the subscribing and receiving events.
    """
    event_recorder.subscribe_event(central_node_mid.sdp_master, "State")
    event_recorder.subscribe_event(central_node_mid.csp_master, "State")
    for dish in central_node_mid.dish_leaf_node_list:
        event_recorder.subscribe_event(dish, "dishMode")
    central_node_mid.move_to_on()
    assert event_recorder.has_change_event_occurred(
        central_node_mid.sdp_master, "State", DevState.ON
    )
    assert event_recorder.has_change_event_occurred(
        central_node_mid.csp_master, "State", DevState.ON
    )
    for dish in central_node_mid.dish_leaf_node_list:
        assert event_recorder.has_change_event_occurred(
            dish, "dishMode", DishMode.STANDBY_FP
        )


@when(
    "I issue the command LoadDishCfg on TMC with Dish and VCC "
    "configuration file"
)
def invoke_load_dish_cfg(
    central_node_mid, event_recorder, command_input_factory
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
    load_dish_cfg_json = prepare_json_args_for_centralnode_commands(
        "load_dish_cfg", command_input_factory
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


@then("TMC should pass the configuration to CSP Controller")
def tmc_pass_configuration_to_csp_controller(simulator_factory):
    """Validate dishVccConfig and sourceDishVccConfig attribute set on Csp
    Master
    :param simulator_factory: fixture for creating simulator devices for
    mid Telescope respectively.
    """
    csp_master_sim, _, _, _, _, _ = get_master_device_simulators(
        simulator_factory
    )
    expected_dish_vcc_config = {
        "interface": "https://schema.skao.int/ska-mid-cbf-initsysparam/1.0",
        "dish_parameters": {
            "SKA001": {"k": 119, "vcc": 1},
            "SKA036": {"k": 1127, "vcc": 2},
            "SKA077": {"k": 620, "vcc": 3},
            "SKA100": {"k": 101, "vcc": 4},
        },
    }
    assert json.loads(csp_master_sim.dishVccConfig) == expected_dish_vcc_config


@then("TMC displays the current version of Dish and VCC configuration")
def validate_dish_vcc_config_attribute_set(central_node_mid):
    """Valdate dishVccConfig and sourceDishVccConfig attribute
    correctly set on csp master leaf node
    :param central_node_mid: fixture for a TMC CentralNode Mid under test
    which provides simulated master devices
    """
    interface_schema = "https://schema.skao.int/ska-mid-cbf-initsysparam/1.0"
    expected_dish_vcc_config = json.dumps(
        {
            "interface": interface_schema,
            "dish_parameters": {
                "SKA001": {"k": 119, "vcc": 1},
                "SKA036": {"k": 1127, "vcc": 2},
                "SKA077": {"k": 620, "vcc": 3},
                "SKA100": {"k": 101, "vcc": 4},
            },
        }
    )
    expected_source_dish_vcc_config = json.dumps(
        {
            "interface": interface_schema,
            "tm_data_sources": [
                "car://gitlab.com/ska-telescope/ska-tmc/ska-tmc-simulators?"
                + "1.13.1#tmdata"
            ],
            "tm_data_filepath": (
                "instrument/dishid_vcc_map_configuration/"
                "ska-mid-cbf-system-parameters.json"
            ),
        }
    )

    assert device_attribute_changed(
        device=central_node_mid.csp_master_leaf_node,
        attribute_name_list=["dishVccConfig", "sourceDishVccConfig"],
        attribute_value_list=[
            expected_dish_vcc_config,
            expected_source_dish_vcc_config,
        ],
        timeout=100,
    ), (
        "dishVccConfig and sourceDishVccConfig attribute value is not set "
        "on csp master leaf node"
    )


@then("TMC should set Dish k-numbers provided in file on dish master devices")
def validate_k_number_set(simulator_factory):
    """Validate k-numbers set on dish masters
    :param simulator_factory: fixture for creating simulator devices for
    mid Telescope respectively.
    """
    (
        _,
        _,
        dish_master_1_sim,
        dish_master_2_sim,
        _,
        _,
    ) = get_master_device_simulators(simulator_factory)
    assert dish_master_1_sim.kValue == 119
    assert dish_master_2_sim.kValue == 1127
