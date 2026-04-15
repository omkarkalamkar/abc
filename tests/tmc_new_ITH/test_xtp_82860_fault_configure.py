"""Test case to verify Restart after Assign Resource Fails
"""

import pytest
from assertpy import assert_that
from pytest_bdd import given, parsers, scenario, then, when
from ska_control_model import ObsState
from ska_integration_test_harness.facades import DishesFacade
from ska_integration_test_harness.facades.csp_facade import CSPFacade
from ska_integration_test_harness.facades.sdp_facade import SDPFacade
from ska_integration_test_harness.facades.tmc_facade import TMCFacade
from ska_integration_test_harness.inputs.test_harness_inputs import (
    TestHarnessInputs,
)
from ska_tango_base.commands import ResultCode
from ska_tango_testing.integration import TangoEventTracer, log_events
from ska_tango_testing.mock.placeholders import Anything

from tests.resources.test_harness.utils.enums import DishMode, PointingState
from tests.tmc_csp_new_ITH.conftest import ASSERTIONS_TIMEOUT
from tests.tmc_new_ITH.conftest import TestContextData
from tests.tmc_new_ITH.utils.utils import (
    invoke_command_with_defect,
    reset_defects,
    setup_event_dish_subscription,
    setup_event_subscriptions,
)


def _check_abort_flow(
    csp: CSPFacade,
    sdp: SDPFacade,
    context_data: TestContextData,
    event_tracer: TangoEventTracer,
):
    """This function checks obstates for abort and
    tracks abort flow if it will be aborted.
    """
    abort_not_allowed_obs_states = [
        ObsState.ABORTED,
        ObsState.FAULT,
        ObsState.EMPTY,
    ]
    if context_data.csp_obsstate not in abort_not_allowed_obs_states:
        assert_that(event_tracer).described_as(
            f"CSP Subarray device ({csp.csp_subarray}) "
            "ObsState attribute values should move "
            f"to ABORTED."
        ).within_timeout(ASSERTIONS_TIMEOUT).has_change_event_occurred(
            csp.csp_subarray,
            "obsState",
            ObsState.ABORTED,
            previous_value=ObsState.ABORTING,
        )

    if context_data.sdp_obsstate not in abort_not_allowed_obs_states:
        assert_that(event_tracer).described_as(
            f"SDP Subarray device ({sdp.sdp_subarray}) "
            "ObsState attribute values should move "
            f"to ABORTED."
        ).within_timeout(ASSERTIONS_TIMEOUT).has_change_event_occurred(
            sdp.sdp_subarray,
            "obsState",
            ObsState.ABORTED,
            previous_value=ObsState.ABORTING,
        )


@pytest.mark.SKA_tmc_mid_restart
@pytest.mark.SKA_mid
@scenario(
    "../tmc_new_ITH/features/xtp_82860_fault_configure.feature",
    "Test Restart Command during failure of Configure Command - Part 1",
)
def test_verify_fault_after_configure_part1():
    """Test Restart command behaviour after configure command fails - Part 1"""


@pytest.mark.SKA_tmc_mid_device_restart
@pytest.mark.SKA_mid
@scenario(
    "../tmc_new_ITH/features/xtp_82860_fault_configure.feature",
    "Test Restart Command during failure of Configure Command - Part 2",
)
def test_verify_fault_after_configure_part2():
    """Test Restart command behaviour after configure command fails - Part 2"""


@given(
    parsers.parse(
        "CSP, SDP and DISH in {csp_obsstate},{sdp_obsstate},"
        "{dish_pointingstates} and {dish_dishmodes} after {command}"
    )
)
def subarray_in_ready_state(
    tmc: TMCFacade,
    sdp: SDPFacade,
    csp: CSPFacade,
    dishes: DishesFacade,
    event_tracer: TangoEventTracer,
    default_commands_inputs: TestHarnessInputs,
    csp_obsstate,
    sdp_obsstate,
    dish_pointingstates,
    dish_dishmodes,
    command,
    context_data: TestContextData,
):
    """Ensure the subarray is in the IDLE state."""
    setup_event_subscriptions(tmc, csp, sdp, event_tracer)
    setup_event_dish_subscription(event_tracer, dishes.dish_master_list)
    invoke_command_with_defect(
        tmc,
        default_commands_inputs,
        csp,
        sdp,
        csp_obsstate,
        sdp_obsstate,
        command,
        dish_pointingstates.split(","),
        dishes.dish_master_list,
        dish_dishmodes.split(","),
    )
    assert_that(event_tracer).described_as(
        f"CSP Subarray device ({csp.csp_subarray})"
        "ObsState attribute value should move "
        f"to {csp_obsstate}."
    ).within_timeout(ASSERTIONS_TIMEOUT).has_change_event_occurred(
        csp.csp_subarray, "obsState", ObsState[csp_obsstate]
    )

    assert_that(event_tracer).described_as(
        f"SDP Subarray device ({sdp.sdp_subarray})"
        "ObsState attribute value should move "
        f" to {sdp_obsstate}."
    ).within_timeout(ASSERTIONS_TIMEOUT).has_change_event_occurred(
        sdp.sdp_subarray, "obsState", ObsState[sdp_obsstate]
    )
    for dish, dish_pointingstate, dish_mode in zip(
        dishes.dish_master_list,
        dish_pointingstates.split(","),
        dish_dishmodes.split(","),
    ):
        if dish_mode != "CONFIG":
            assert_that(event_tracer).described_as(
                f"Dish device ({dish})"
                "PointingState attribute value should move "
                f"to {dish_pointingstate}."
            ).within_timeout(ASSERTIONS_TIMEOUT).has_change_event_occurred(
                dish,
                "pointingState",
                PointingState[dish_pointingstate],
            )
        if dish_mode != "STANDBY_FP":
            assert_that(event_tracer).described_as(
                f"Dish device ({dish})"
                "Dish Mode attribute value should move "
                f"to {dish_mode}."
            ).within_timeout(ASSERTIONS_TIMEOUT).has_change_event_occurred(
                dish,
                "dishMode",
                DishMode[dish_mode],
            )
    context_data.csp_obsstate = ObsState[csp_obsstate]
    context_data.sdp_obsstate = ObsState[sdp_obsstate]


@given("TMC Subarray in observation state FAULT")
def verify_tmc_subarray_observation_state_fault(
    event_tracer: TangoEventTracer,
    tmc: TMCFacade,
    csp: CSPFacade,
    sdp: SDPFacade,
    dishes: DishesFacade,
):
    """Verifies the TMC subarray observation state FAULT"""
    assert_that(event_tracer).described_as(
        f"TMC Subarray Node device ({tmc.subarray_node})"
        "ObsState attribute value should move "
        f" to FAULT."
    ).within_timeout(ASSERTIONS_TIMEOUT).has_change_event_occurred(
        tmc.subarray_node,
        "obsState",
        ObsState.FAULT,
    )

    log_events({tmc.subarray_node: ["longRunningCommandResult"]})

    assert_that(event_tracer).described_as(
        f"FAILED ASSUMPTION: "
        "Subarray Node device"
        f"({tmc.subarray_node}) "
        "is expected to have longRunningCommandResult"
        "(ResultCode.FAILED,Timeout has occurred, command failed)",
    ).within_timeout(
        ASSERTIONS_TIMEOUT
    ).has_desired_result_code_message_in_lrcr_event(
        tmc.subarray_node,
        ["occurred"],
        Anything,
        ResultCode.FAILED,
    )

    reset_defects(csp, sdp, dishes.dish_master_list)


@when("I invoke Restart Command on the TMC Subarray")
def invoke_restart_command(tmc: TMCFacade):
    """Invokes restart command on the TMC Subarray."""
    tmc.restart()


@then("CSP and SDP transitions to observation state EMPTY")
def verify_sdp_csp_in_empty_observation_state(
    event_tracer: TangoEventTracer,
    csp: CSPFacade,
    sdp: SDPFacade,
    context_data: TestContextData,
):
    """Verifies the observation states of SDP,CSP
    after command Restart.
    """
    _check_abort_flow(csp, sdp, context_data, event_tracer)
    (
        assert_that(event_tracer)
        .described_as(
            f", CSP Subarray device ({csp.csp_subarray}) "
            f"and SDP Subarray device ({sdp.sdp_subarray}) "
            "ObsState attribute values should move "
            f"to RESTARTING."
        )
        .within_timeout(ASSERTIONS_TIMEOUT)
        .has_change_event_occurred(
            csp.csp_subarray, "obsState", ObsState.RESTARTING
        )
        .has_change_event_occurred(
            sdp.sdp_subarray, "obsState", ObsState.RESTARTING
        )
    )

    assert_that(event_tracer).described_as(
        f", CSP Subarray device ({csp.csp_subarray}) "
        f"and SDP Subarray device ({sdp.sdp_subarray}) "
        "ObsState attribute values should move "
        f"to EMPTY."
    ).within_timeout(ASSERTIONS_TIMEOUT).has_change_event_occurred(
        csp.csp_subarray, "obsState", ObsState.EMPTY
    ).has_change_event_occurred(
        sdp.sdp_subarray, "obsState", ObsState.EMPTY
    )


@then("Dish transitions to dishMode StandbyFP and PointingState READY")
def verify_dishes_is_in_ready_state(
    event_tracer: TangoEventTracer,
    dishes: DishesFacade,
):
    """Verifies the observation states of SDP,CSP
    after command Restart.
    """
    for dish in dishes.dish_master_list:
        (
            assert_that(event_tracer)
            .described_as(
                f", Dish Device ({dish}) "
                "PointingState attribute values should move "
                f"to READY."
            )
            .within_timeout(ASSERTIONS_TIMEOUT)
            .has_change_event_occurred(
                dish, "pointingState", PointingState.READY
            )
        )


@then("TMC subarray transitions to observation state EMPTY")
def verify_tmc_subarray_in_empty_observation_state(
    event_tracer: TangoEventTracer, tmc: TMCFacade
):
    """Verifies the observation state of TMC Subarray."""
    assert_that(event_tracer).described_as(
        f"TMC Subarray Node device ({tmc.subarray_node})"
        "ObsState attribute value should move "
        f"from {ObsState.FAULT} to EMPTY."
    ).within_timeout(ASSERTIONS_TIMEOUT).has_change_event_occurred(
        tmc.subarray_node, "obsState", ObsState.EMPTY
    )
