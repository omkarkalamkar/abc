"""
BDD tests to verify Dish Leaf Node validation failures
(kValue / GPM) degrade Dish, Subarray, and Telescope health.
"""

import json
import logging
import time

import pytest
from assertpy import assert_that
from pytest_bdd import given, parsers, scenario, then, when
from ska_control_model import AdminMode, HealthState
from ska_integration_test_harness.facades.csp_facade import CSPFacade
from ska_integration_test_harness.facades.dishes_facade import DishesFacade
from ska_integration_test_harness.facades.sdp_facade import SDPFacade
from ska_integration_test_harness.facades.tmc_facade import TMCFacade
from ska_tango_testing.integration import TangoEventTracer
from ska_tango_testing.mock.placeholders import Anything
from tango import DeviceProxy

from tests.resources.test_harness.helpers import (
    wait_and_validate_device_attribute_value,
)
from tests.resources.test_harness.utils.enums import CapabilityStates
from tests.resources.test_support.common_utils.result_code import ResultCode
from tests.resources.test_support.common_utils.tmc_helpers import (
    tear_down_configured_alarms,
)
from tests.resources.test_support.constant import (
    alarm_handler1,
    tmc_dish_leaf_node1,
)
from tests.tmc_csp_new_ITH.conftest import SubarrayTestContextData
from tests.tmc_csp_new_ITH.utils.my_file_json_input import MyFileJSONInput
from tests.tmc_new_ITH.conftest import ASSERTIONS_TIMEOUT
from tests.tmc_new_ITH.utils.utils import get_mid_csp_sdp_subarrays_proxies

LOGGER = logging.getLogger(__name__)


def _setup_event_subscriptions(
    tmc: TMCFacade,
    csp: CSPFacade,
    sdp: SDPFacade,
    dishes: DishesFacade,
    event_tracer: TangoEventTracer,
):
    """Subscribe TMC, CSP and SDP devices to track and log obsState events.

    :param tmc: the TMC facade.
    :param csp: the CSP facade.
    :param sdp: the SDP facade.
    :param event_tracer: the event tracer.
    """

    event_tracer.subscribe_event(tmc.subarray_node, "healthState")
    event_tracer.subscribe_event(tmc.subarray_node, "healthInfo")
    event_tracer.subscribe_event(csp.csp_master, "healthState")
    event_tracer.subscribe_event(sdp.sdp_master, "healthState")
    event_tracer.subscribe_event(csp.csp_subarray, "healthState")
    event_tracer.subscribe_event(sdp.sdp_subarray, "healthState")
    event_tracer.subscribe_event(tmc.central_node, "telescopeHealthState")

    event_tracer.subscribe_event(
        tmc.dish_leaf_node_list[0], "kvaluevalidationresult"
    )
    event_tracer.subscribe_event(
        tmc.dish_leaf_node_list[0], "gpmValidationResult"
    )
    event_tracer.subscribe_event(tmc.dish_leaf_node_list[0], "healthState")

    event_tracer.subscribe_event(
        tmc.dish_leaf_node_list[0], "globalPointingModelParams"
    )

    event_tracer.subscribe_event(
        dishes.dish_master_dict["dish_001"], "healthState"
    )
    event_tracer.subscribe_event(
        dishes.dish_master_dict["dish_036"], "healthState"
    )
    event_tracer.subscribe_event(
        dishes.dish_master_dict["dish_063"], "healthState"
    )
    event_tracer.subscribe_event(
        dishes.dish_master_dict["dish_100"], "healthState"
    )

    mid_subarrays = get_mid_csp_sdp_subarrays_proxies()

    for subarray in mid_subarrays.values():
        event_tracer.subscribe_event(subarray, "healthState")


def assert_gpm_validation_result_mid(
    event_tracer,
    dish_ln,
    band_name: str,
    expected_result: str,
    timeout: float,
    poll_interval: float = 1.0,
):
    """
    MID integration safe assertion for GPM validation.

    - Waits for gpmValidationResult CHANGE_EVENTs
    - Repeatedly reads attribute value
    - Logs every observed transition
    - Passes only when target band reaches expected_result
    """

    end_time = time.time() + timeout
    last_seen = None

    LOGGER.info(
        "Waiting for gpmValidationResult: %s -> %s (timeout=%ss)",
        band_name,
        expected_result,
        timeout,
    )

    while time.time() < end_time:
        # Ensure at least one change event has occurred
        assert_that(event_tracer).within_timeout(
            poll_interval
        ).has_change_event_occurred(
            dish_ln,
            "gpmValidationResult",
            Anything,
        )

        # Read latest attribute value
        current_value = json.loads(dish_ln.gpmValidationResult)

        if current_value != last_seen:
            LOGGER.info(
                "GPM validation transition observed: %s",
                current_value,
            )
            last_seen = current_value

        if current_value.get(band_name) == expected_result:
            LOGGER.info(
                "GPM validation reached expected state: %s=%s",
                band_name,
                expected_result,
            )
            return current_value

        time.sleep(poll_interval)

    raise AssertionError(
        f"GPM validation did not reach {band_name}={expected_result}. "
        f"Last seen value: {last_seen}"
    )


@pytest.fixture
def preserve_dish_state(
    tmc: TMCFacade, dishes: DishesFacade, event_tracer: TangoEventTracer
):
    """
    Preserve and restore Dish Master and Dish Leaf Node state so
    subsequent tests are not affected.
    """

    dish_ln = tmc.dish_leaf_node_list[0]
    dish_master = dishes.dish_master_dict["dish_001"]

    # Preserve original values
    original_kvalue_dln = dish_ln.kValue
    original_kvalue_master = dish_master.kValue
    original_band1_params = list(dish_master.band1PointingModelParams)

    yield

    # Restore kValue
    dish_ln.SetKValue(original_kvalue_dln)
    dish_master.SetKValue(original_kvalue_master)

    # Restore Band-1
    dish_master.band1PointingModelParams = original_band1_params

    # Allow validation to settle
    time.sleep(2)

    assert int(dish_ln.kvaluevalidationresult) == ResultCode.OK.value

    gpm_result = json.loads(dish_ln.gpmValidationResult)
    assert gpm_result.get("Band_1") == "OK"

    assert tmc.central_node.IsDishVccConfigSet is True


@pytest.mark.batch1
@pytest.mark.SKA_mid
@scenario(
    "../tmc_new_ITH/features/xtp_97749_dish_validation_health.feature",
    "Dish validation failure impacts telescope health",
)
def test_dish_validation_impacts_health():
    """BDD Scenario Outline test"""


@given("a TMC")
def given_a_tmc(
    tmc: TMCFacade,
    sdp: SDPFacade,
    csp: CSPFacade,
    dishes: DishesFacade,
    event_tracer: TangoEventTracer,
):
    """
    Given a TMC
    :param tmc: TMC facade providing access to Central, Subarray,
            and Dish Leaf Node components.
    :param event_tracer: Utility used to trace and assert Tango events.
    """

    _setup_event_subscriptions(tmc, csp, sdp, dishes, event_tracer)

    pytest.capability_dict = json.dumps(
        {
            "B1": CapabilityStates.STANDBY,
            "B2": CapabilityStates.STANDBY,
            "B3": CapabilityStates.STANDBY,
            "B4": CapabilityStates.STANDBY,
            "B5a": CapabilityStates.STANDBY,
            "B5b": CapabilityStates.STANDBY,
        }
    )
    dishes.dish_master_dict["dish_001"].SetDirectCapabilityState(
        pytest.capability_dict
    )
    dishes.dish_master_dict["dish_036"].SetDirectCapabilityState(
        pytest.capability_dict
    )
    dishes.dish_master_dict["dish_063"].SetDirectCapabilityState(
        pytest.capability_dict
    )
    dishes.dish_master_dict["dish_100"].SetDirectCapabilityState(
        pytest.capability_dict
    )

    csp.csp_subarray.SetDirectHealthState(HealthState.OK)
    sdp.sdp_subarray.SetDirectHealthState(HealthState.OK)
    csp.csp_master.SetDirectHealthState(HealthState.OK)
    sdp.sdp_master.SetDirectHealthState(HealthState.OK)
    dishes.dish_master_dict["dish_001"].SetDirectHealthState(HealthState.OK)
    dishes.dish_master_dict["dish_036"].SetDirectHealthState(HealthState.OK)
    dishes.dish_master_dict["dish_063"].SetDirectHealthState(HealthState.OK)
    dishes.dish_master_dict["dish_100"].SetDirectHealthState(HealthState.OK)
    mid_subarrays = get_mid_csp_sdp_subarrays_proxies()

    # Set all MID subarrays health to OK
    for subarray in mid_subarrays.values():
        subarray.SetDirectHealthState(HealthState.OK)

    # Toggle CSP subarrays adminMode
    for key in ("csp_1", "csp_2"):
        mid_subarrays[key].adminMode = AdminMode.OFFLINE

    time.sleep(0.2)

    for key in ("csp_1", "csp_2"):
        mid_subarrays[key].adminMode = AdminMode.ONLINE


@given("Telescope is in ON state")
def telescope_in_on_state(tmc: TMCFacade):
    """
    Ensure that the telescope is transitioned to the ON state.

    :param tmc: TMC facade used to control telescope state.
    """
    tmc.move_to_on(wait_termination=True, is_long_running_command=True)


@given("I assign resources to TMC Subarray")
def invoke_assign_resources(
    context_fixt: SubarrayTestContextData, tmc: TMCFacade
):
    """Invoke Assign Resources"""

    json_input = MyFileJSONInput(
        "centralnode", "assign_resources_mid"
    ).with_attribute("subarray_id", 1)

    context_fixt.when_action_result = tmc.assign_resources(
        json_input,
        wait_termination=True,
    )


@given(
    parsers.parse(
        'Dish Leaf Node has "{validation_type}" validation condition'
    )
)
def prepare_validation_condition(
    tmc: TMCFacade,
    dishes: DishesFacade,
    validation_type: str,
    event_tracer: TangoEventTracer,
    preserve_dish_state,
):
    """
    Prepare Dish Leaf Node validation condition and
    assert validation results immediately after setting.
        :param tmc: TMC facade providing access to Dish Leaf Nodes.
        :param dishes: Dishes facade providing access to Dish Masters.
        :param validation_type: Type of validation condition to apply.
        Supported values:
            - "all_ok": No validation failures present.
            - "kvalue mismatch": Dish Leaf Node and Dish Master kValue differ.
            - "gpm mismatch": Dish pointing model parameters are inconsistent.
        :param event_tracer: Utility used to capture and assert Tango
            change events emitted by the Dish Leaf Node.
        :param preserve_dish_state: Fixture that saves and restores
            Dish state to avoid side effects on subsequent tests.
    """

    dish_ln = tmc.dish_leaf_node_list[0]
    dish_master = dishes.dish_master_dict["dish_001"]

    if validation_type == "all_ok":
        assert int(dish_ln.kvaluevalidationresult) == ResultCode.OK.value
        gpm_result = json.loads(dish_ln.gpmValidationResult)
        assert any(value != "FAILED" for value in gpm_result.values())
        for band, value in gpm_result.items():
            LOGGER.info("  %s: %s", band, value)

    elif validation_type == "kvalue mismatch":
        # kValue mismatch
        dish_ln.SetKValue(1)
        dish_master.SetKValue(2)

        assert wait_and_validate_device_attribute_value(
            dish_ln,
            "kvaluevalidationresult",
            str(ResultCode.FAILED.value),
        )

        assert_that(event_tracer).described_as(
            "Dish Leaf Node kValueValidationResult should change to FAILED"
        ).within_timeout(ASSERTIONS_TIMEOUT).has_change_event_occurred(
            dish_ln,
            "kvaluevalidationresult",
            str(ResultCode.FAILED.value),
        )

    elif validation_type == "gpm mismatch":
        # Keep kValue consistent
        dish_ln.SetKValue(1)
        dish_master.SetKValue(1)

        assert wait_and_validate_device_attribute_value(
            dish_ln,
            "kvaluevalidationresult",
            str(ResultCode.OK.value),
        )

        assert_that(event_tracer).described_as(
            "Dish Leaf Node kValueValidationResult should change to Ok"
        ).within_timeout(ASSERTIONS_TIMEOUT).has_change_event_occurred(
            dish_ln,
            "kvaluevalidationresult",
            str(ResultCode.OK.value),
        )

        # Introduce GPM mismatch via Dish Master Band-3 params
        invalid_params = [0.0] * 18
        invalid_params[0] = 999.0

        dish_master.band1PointingModelParams = invalid_params

        gpm_result = assert_gpm_validation_result_mid(
            event_tracer=event_tracer,
            dish_ln=dish_ln,
            band_name="Band_1",
            expected_result="FAILED",
            timeout=ASSERTIONS_TIMEOUT,
        )

        LOGGER.info("Final GPM validation result: %s", gpm_result)

    else:
        raise ValueError(f"Unsupported validation_type: {validation_type}")


@when("Dish Leaf Node health is evaluated")
def evaluate_health(tmc: TMCFacade):
    """
    Health evaluation is triggered implicitly by validation callbacks.
    :param tmc: TMC facade
    """
    pass


@then(parsers.parse('Dish Leaf Node healthState shall be "{dln_health}"'))
def verify_dln_health(
    tmc: TMCFacade,
    event_tracer: TangoEventTracer,
    dln_health: str,
):
    """
    Verify the Dish Leaf Node health state.

    This step asserts that a Tango change event for the Dish
    Leaf Node healthState matches the expected value.

    :param tmc: TMC facade providing access to the Dish Leaf Node.
    :param event_tracer: Utility used to capture and assert change events.
    :param dln_health: Expected Dish Leaf Node health state.
    """

    dish_ln = tmc.dish_leaf_node_list[0]

    assert_that(event_tracer).described_as(
        "Dish Leaf Node healthState should change " f"to {dln_health}"
    ).within_timeout(ASSERTIONS_TIMEOUT).has_change_event_occurred(
        dish_ln,
        "healthState",
        HealthState[dln_health],
    )


@then(
    parsers.parse(
        'TMC Subarray Node healthState shall be "{propagated_health}"'
    )
)
def verify_subarray_health(
    tmc: TMCFacade,
    event_tracer: TangoEventTracer,
    propagated_health: str,
):
    """
    Verify the TMC Subarray Node health state.

    This step confirms that healthstate change
    propagates from the Dish Leaf Node to the Subarray Node.

    :param tmc: TMC facade providing access to the Subarray Node.
    :param event_tracer: Utility used to capture and assert change events.
    :param propagated_health: Expected Subarray health state.
    """

    LOGGER.info(
        "Checking TMC Subarray Node healthState expected=%s",
        propagated_health,
    )

    assert_that(event_tracer).described_as(
        "TMC Subarray Node healthState should change "
        f"to {propagated_health}"
    ).within_timeout(ASSERTIONS_TIMEOUT).has_change_event_occurred(
        tmc.subarray_node,
        "healthState",
        HealthState[propagated_health],
    )

    raw_health_info = tmc.subarray_node.healthInfo
    LOGGER.info("Raw Subarray healthInfo: %s", raw_health_info)
    health_info = json.loads(raw_health_info)

    LOGGER.info(
        "Parsed Subarray healthInfo:\n%s",
        json.dumps(health_info, indent=4),
    )


@then(parsers.parse('telescopeHealthState shall be "{propagated_health}"'))
def verify_telescope_health(
    tmc: TMCFacade,
    event_tracer: TangoEventTracer,
    propagated_health: str,
):
    """
    Verify the overall telescope health state.

    This step ensures that Dish-level validation failures
    propagate through the system hierarchy up to the
    Telescope (Central Node) health state.

    :param tmc: TMC facade providing access to the Central Node.
    :param event_tracer: Utility used to capture and assert change events.
    :param propagated_health: Expected telescope health state.
    """

    if propagated_health == "OK":
        # NO change event expected — state should already be OK
        assert tmc.central_node.telescopeHealthState == HealthState.OK
    else:
        assert_that(event_tracer).described_as(
            "Telescope healthState should change " f"to {propagated_health}"
        ).within_timeout(ASSERTIONS_TIMEOUT).has_change_event_occurred(
            tmc.central_node,
            "telescopeHealthState",
            HealthState[propagated_health],
        )


@then(parsers.parse('HealthInfo will be updated for "{validation_type}"'))
def verify_health_info_update(
    tmc: TMCFacade,
    event_tracer: TangoEventTracer,
    validation_type: str,
):
    """
    Verify the HealthInfo update for the specified validation type.

    :param tmc: TMC facade providing access to the relevant nodes.
    :param event_tracer: Utility used to capture and assert change events.
    :param validation_type: The type of validation being checked.
    """
    LOGGER.info(
        "Verifying HealthInfo update for validation_type=%s",
        validation_type,
    )

    assert_that(event_tracer).described_as(
        f"HealthInfo should be updated for {validation_type}"
    ).within_timeout(ASSERTIONS_TIMEOUT).has_change_event_occurred(
        tmc.subarray_node,
        "healthInfo",
        Anything,
    )

    raw_health_info = tmc.subarray_node.healthInfo
    LOGGER.info("Raw HealthInfo: %s", raw_health_info)
    health_info = json.loads(raw_health_info)

    LOGGER.info(
        "Parsed HealthInfo:\n%s",
        json.dumps(health_info, indent=4),
    )
    if isinstance(health_info, dict):
        messages = []
        for v in health_info.values():
            if isinstance(v, list):
                messages.extend(v)

    if validation_type == "kvalue mismatch":
        expected_substring = "KValue validation failed."

        assert any(expected_substring in msg for msg in messages), (
            f"Expected '{expected_substring}' in healthInfo messages, "
            f"but got: {health_info}"
        )

    elif validation_type == "gpm mismatch":
        expected_substring = "GPM validation failed"

        assert any(expected_substring in msg for msg in messages), (
            f"Expected '{expected_substring}' in healthInfo messages, "
            f"but got: {health_info}"
        )

        # target_device = tmc.dish_leaf_node_list[0]
    elif validation_type == "all_ok":
        assert not messages, "Expected messages to be blank"

    else:
        raise ValueError(f"Unsupported validation_type: {validation_type}")


@then(
    parsers.parse(
        'an alarm shall be raised for "{validation_type}" validation failure'
    )
)
def verify_alarm_raised(validation_type):
    """
    Verify alarm is raised based on Dish Leaf Node healthState.
    Alarm logic is driven by DEGRADED health, not raw validation attributes.
    """
    LOGGER.info(
        "Verifying alarm behavior for validation_type=%s",
        validation_type,
    )

    alarm_handler = DeviceProxy(alarm_handler1)

    # No alarm expected when everything is OK
    if validation_type == "all_ok":
        LOGGER.info("Validation type all_ok: no alarm expected")
        return

    # Alarm metadata differs, formula is Same
    if validation_type == "kvalue mismatch":
        expected_tag = "DishLeafNode_Degraded_kValue"
        message = (
            "Dish Leaf Node health degraded due to "
            "kValue validation failure"
        )

    elif validation_type == "gpm mismatch":
        expected_tag = "DishLeafNode_Degraded_GPM"
        message = (
            "Dish Leaf Node health degraded due to " "GPM validation failure"
        )

    else:
        raise ValueError(f"Unsupported validation_type: {validation_type}")

    alarm_formula = (
        f"tag={expected_tag};"
        f"formula=({tmc_dish_leaf_node1}/healthState == 'DEGRADED');"
        "priority=log;"
        "group=none;"
        f'message="{message}"'
    )

    LOGGER.info("Loading alarm formula: %s", alarm_formula)

    alarm_handler.Load(alarm_formula)

    alarm_list = alarm_handler.alarmList
    LOGGER.info("Current alarm list: %s", alarm_list)

    assert expected_tag.lower() in alarm_list

    # Cleanup
    tear_down_configured_alarms(alarm_handler, alarm_list)
