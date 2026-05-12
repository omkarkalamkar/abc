"""Test case to verify fixed trajectory works as expected
"""
import json
import time

import numpy as np
import pytest
from assertpy import assert_that
from pytest_bdd import given, parsers, scenario, then, when
from ska_control_model import ObsState
from ska_integration_test_harness.facades import DishesFacade
from ska_integration_test_harness.facades.csp_facade import CSPFacade
from ska_integration_test_harness.facades.sdp_facade import SDPFacade
from ska_integration_test_harness.facades.tmc_facade import TMCFacade
from ska_integration_test_harness.inputs.json_input import DictJSONInput
from ska_integration_test_harness.inputs.test_harness_inputs import (
    TestHarnessInputs,
)
from ska_tango_testing.integration import TangoEventTracer

from tests.conftest import LOGGER
from tests.tmc_csp_new_ITH.conftest import (
    ASSERTIONS_TIMEOUT,
    SubarrayTestContextData,
)
from tests.tmc_csp_new_ITH.utils.my_file_json_input import MyFileJSONInput
from tests.tmc_new_ITH.utils.dpd_facade import DishPointingDevicesFacade
from tests.tmc_new_ITH.utils.enums import Band
from tests.tmc_new_ITH.utils.utils import (
    setup_event_dish_subscription,
    setup_event_subscriptions,
)


def update_configuration_json(config_json: dict, config_data: str):
    """Update config json based on config data provided
    Args:
        config_json(dict): Json for partial configuration
        config_data(str): type of data to add/update
    """
    if config_data == "configuration_with_only_trajectory":
        config_json["pointing"].pop("wrap_sector", None)
    elif config_data == "configuration_with_only_band":
        config_json["pointing"].clear()
        config_json["pointing"]["wrap_sector"] = 0
        config_json["dish"] = {"receiver_band": "2"}
    elif config_data == "configuration_with_only_collimation_offsets":
        config_json["pointing"] = {
            "ca_offset_arcsec": 0.0,
            "ie_offset_arcsec": 5.0,
        }
    elif config_data == "configuration_with_traj_coll_offsets":
        config_json["pointing"].pop("wrap_sector", None)
        config_json["pointing"]["groups"][0]["trajectory"]["attrs"] = {
            "x": 5.0,
            "y": 1.0,
        }
        config_json["pointing"].update(
            {
                "ca_offset_arcsec": 0.0,
                "ie_offset_arcsec": 5.0,
            }
        )
    elif config_data == "configuration_with_only_wrap_sector":
        config_json["pointing"]["wrap_sector"] = 0


@pytest.mark.batch1
@pytest.mark.SKA_mid
@scenario(
    "../tmc_new_ITH/features/xtp_81618_partial_configuration.feature",
    "TMC Behaviour when partial configuration is provided",
)
def test_verify_partial_configuration():
    """Test TMC handle partial configuration when only partial configuration
    provided
    """


@given("a TMC")
def given_a_tmc(
    tmc: TMCFacade,
    sdp: SDPFacade,
    csp: CSPFacade,
    event_tracer: TangoEventTracer,
    dishes: DishesFacade,
):
    """Given a TMC"""
    setup_event_subscriptions(tmc, csp, sdp, event_tracer)
    setup_event_dish_subscription(event_tracer, dishes.dish_master_list)


@given("TMC SubarrayNode is in Ready ObsState")
def subarray_in_ready_state(
    context_fixt: SubarrayTestContextData,
    tmc: TMCFacade,
    sdp: SDPFacade,
    csp: CSPFacade,
    event_tracer: TangoEventTracer,
    dish_pointng_devices: DishPointingDevicesFacade,
):
    """Ensure the subarray is in the READY state."""
    context_fixt.starting_state = ObsState.IDLE
    tmc.force_change_of_obs_state(
        ObsState.READY,
        TestHarnessInputs(
            assign_input=MyFileJSONInput(
                "centralnode", "assign_resources_mid"
            ),
            configure_input=MyFileJSONInput(
                "subarray", "configure_holography_adr106"
            ),
        ),
        wait_termination=True,
    )
    # Verify wrap sector applied correctly
    for dish_pointing_device in dish_pointng_devices.dish_pointing_device_list:
        program_track_table = json.loads(
            dish_pointing_device.pointingprogramtracktable
        )
        dpd_target_data = json.loads(dish_pointing_device.targetdata)
        assert dpd_target_data["pointing"]["wrap_sector"] == -1
        # Assert azimuth value getting updated as per value of wrap_sector
        assert program_track_table[1] < 0


@when(
    parsers.parse(
        "I execute partial configure command with {configuration_data}"
    )
)
def send_partial_configure_command(
    context_fixt: SubarrayTestContextData,
    tmc: TMCFacade,
    configuration_data: str,
):
    """Update partial configuration json as per configuration data
    and execute configure command
    """
    json_input = MyFileJSONInput("subarray", "partial_configure_trajectory")
    config_json = json.loads(json_input.as_str())
    update_configuration_json(config_json, configuration_data)
    pytest.configuration_data = configuration_data
    context_fixt.when_action_result = tmc.configure(
        DictJSONInput(config_json), wait_termination=True
    )


@then("the TMC SubarrayNode transitions to obsState READY")
def verify_ready_state(
    context_fixt: SubarrayTestContextData,
    tmc: TMCFacade,
    csp: CSPFacade,
    sdp: SDPFacade,
    event_tracer: TangoEventTracer,
):
    """
    Verify the subarray's transition to the READY state.

    This step checks that the ObsState attribute of the TMC Subarray Node,
    CSP Subarray, and SDP Subarray devices all transition from the starting
    state to the READY state. It uses the event_tracer to assert that these
    state changes occur within a specified timeout. After verification, it
    updates the starting state in the context fixture for subsequent steps.
    """
    context_fixt.starting_state = ObsState.CONFIGURING
    assert_that(event_tracer).described_as(
        f"Both TMC Subarray Node device ({tmc.subarray_node})"
        f", CSP Subarray device ({csp.csp_subarray}) "
        f"and SDP Subarray device ({sdp.sdp_subarray}) "
        "ObsState attribute values should move "
        f"from {str(context_fixt.starting_state)} to READY."
    ).within_timeout(ASSERTIONS_TIMEOUT).has_change_event_occurred(
        tmc.subarray_node,
        "obsState",
        ObsState.READY,
        previous_value=context_fixt.starting_state,
    ).has_change_event_occurred(
        csp.csp_subarray,
        "obsState",
        ObsState.READY,
        previous_value=context_fixt.starting_state,
    ).has_change_event_occurred(
        sdp.sdp_subarray,
        "obsState",
        ObsState.READY,
        previous_value=context_fixt.starting_state,
    )
    context_fixt.starting_state = ObsState.READY


def verify_band(dishes: DishesFacade):
    """
    Verify that all dishes have the configured band set.
    Args:
        dishes (DishesFacade): Facade providing access to dish objects.
    """
    for dish in dishes.dish_master_list:
        assert dish.configuredBand == Band.B2


def verify_coff(tmc: TMCFacade):
    """
    Verify that selected dishes (SKA036, SKA100) in the TMC dish leaf node list
    have the expected source offset values.
    Args:
        tmc (TMCFacade): Facade providing access to TMC dish leaf nodes.
    """
    for dish in tmc.dish_leaf_node_list:
        # Check only for SKA036 and SKA100
        if hasattr(dish, "name") and dish.name in ["SKA036", "SKA100"]:
            assert list(dish.sourceOffset) == [0.0, 5.0]


def verify_only_trajectory(dish_pointng_devices: DishPointingDevicesFacade):
    """
    Verify that the trajectory attributes in the target data of dish pointing
    devices are correctly applied.
    Args:
        dish_pointng_devices (DishPointingDevicesFacade):
        Facade for dish pointing devices.
    """
    for (
        dpd_name,
        dpd,
    ) in dish_pointng_devices.dish_pointing_device_dict.items():
        if dpd_name in ["SKA036", "SKA100"]:
            expected = {"x": -5, "y": 5}
        else:
            expected = {"x": 0, "y": 0}
        assert (
            json.loads(dpd.targetData)["pointing"]["trajectory"]["attrs"]
            == expected
        )


def verify_traj_and_coff(
    tmc: TMCFacade,
    dish_pointng_devices: DishPointingDevicesFacade,
    event_tracer,
):
    """
    Verify that both trajectory attributes and collimation offsets
    are correctly applied on dishes.

    Args:
        event_tracer:
        tmc (TMCFacade): Facade providing access to TMC dish leaf nodes.
        dish_pointng_devices (DishPointingDevicesFacade): Facade for
        dish pointing devices.
    """
    for dish, dpd_name in zip(
        tmc.dish_leaf_node_list,
        dish_pointng_devices.dish_pointing_device_dict.keys(),
    ):
        dpd = dish_pointng_devices.dish_pointing_device_dict[dpd_name]
        if dpd_name in ["SKA036", "SKA100"]:
            expected_attr_val = np.array([5.0, 1.0])
            retries = 0
            attr_val = np.array(dish.sourceOffset)
            LOGGER.info("Dish=%s,sourceOffset=%s", dish, attr_val)
            while retries < 6:
                attr_val = np.array(dish.sourceOffset)
                if np.array_equal(attr_val, expected_attr_val):
                    break
                time.sleep(2)
                retries += 1

            assert np.array_equal(attr_val, expected_attr_val), (
                f"sourceOffset of {dish} didn't attain value "
                f"{expected_attr_val}; current value is {attr_val}"
            )
            expected = {"x": 5, "y": 1}
        else:
            expected = {"x": 0, "y": 0}
        json_data = json.loads(dpd.targetData)["pointing"]["trajectory"][
            "attrs"
        ]
        assert json_data == expected


def verify_wrap_sector(
    dish_pointng_devices: DishPointingDevicesFacade,
):
    """
    Verify that the wrap sector is correctly applied on dish pointing devices.
    Args:
        dish_pointng_devices (DishPointingDevicesFacade): Facade for
        dish pointing devices.
    """
    for dish_pointing_device in dish_pointng_devices.dish_pointing_device_list:
        dpd_target_data = json.loads(dish_pointing_device.targetdata)
        assert dpd_target_data["pointing"]["wrap_sector"] == 0


@then("provided configuration data applied on dish leaf node")
def verify_configuration_data(
    context_fixt: SubarrayTestContextData,
    tmc: TMCFacade,
    dishes: DishesFacade,
    dish_pointng_devices: DishPointingDevicesFacade,
    event_tracer,
):
    """Verify that configuration data is applied correctly on dishes"""
    dispatch = {
        "configuration_with_only_band": lambda: verify_band(dishes),
        "configuration_with_only_collimation_offsets": lambda: verify_coff(
            tmc
        ),
        "configuration_with_only_trajectory": lambda: verify_only_trajectory(
            dish_pointng_devices
        ),
        "configuration_with_traj_coll_offsets": lambda: verify_traj_and_coff(
            tmc, dish_pointng_devices, event_tracer
        ),
        "configuration_with_only_wrap_sector": lambda: verify_wrap_sector(
            dish_pointng_devices
        ),
    }

    func = dispatch.get(pytest.configuration_data)
    func()
