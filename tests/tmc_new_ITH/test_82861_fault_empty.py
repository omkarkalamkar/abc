"""
Verify TMC subarray moves to EMPTY from FAULT when all sub system are in empty
"""
import pytest
from assertpy import assert_that
from pytest_bdd import given, scenario, then, when
from ska_control_model import ObsState
from ska_integration_test_harness.facades.csp_facade import CSPFacade
from ska_integration_test_harness.facades.sdp_facade import SDPFacade
from ska_integration_test_harness.facades.tmc_facade import TMCFacade
from ska_integration_test_harness.inputs.test_harness_inputs import (
    TestHarnessInputs,
)
from ska_tango_testing.integration import TangoEventTracer

from tests.tmc_csp_new_ITH.conftest import ASSERTIONS_TIMEOUT
from tests.tmc_new_ITH.utils.utils import (
    reset_defects,
    set_subsystem_defects,
    setup_event_subscriptions,
)


@pytest.mark.SKA_tmc_mid_restart
@pytest.mark.SKA_mid
@scenario(
    "../tmc_new_ITH/features/xtp_82861_fault_empty.feature",
    "Test Restart Command when TMC subarray transitions to "
    "FAULT observation state",
)
def test_restart_command_from_observation_state_resourcing_fault():
    """BDD test scenario for verifying execution of the Restart
    command in FAULT obsState in TMC."""


@given(
    "a TMC Subarray transitioned from RESOURCING to FAULT observation state "
    "after command failure"
)
def verify_tmc_subarray_resourcing_fault(
    tmc: TMCFacade,
    csp: CSPFacade,
    sdp: SDPFacade,
    default_commands_inputs: TestHarnessInputs,
    event_tracer: TangoEventTracer,
):
    """Verifies TMC Subarray Observation state into FAULT after
    AssignResources failure.
    """
    setup_event_subscriptions(tmc, csp, sdp, event_tracer)
    set_subsystem_defects(csp, sdp, "IDLE", "EMPTY", "AssignResources")
    tmc.assign_resources(
        default_commands_inputs.assign_input, wait_termination=False
    )
    assert_that(event_tracer).described_as(
        f"TMC Subarray Node device ({tmc.subarray_node})"
        "ObsState attribute value should move "
        f"to {ObsState.RESOURCING}."
    ).within_timeout(ASSERTIONS_TIMEOUT).has_change_event_occurred(
        tmc.subarray_node, "obsState", ObsState.RESOURCING
    )
    assert_that(event_tracer).described_as(
        f"TMC Subarray Node device ({tmc.subarray_node})"
        "ObsState attribute value should move "
        f"to {ObsState.FAULT}."
    ).within_timeout(ASSERTIONS_TIMEOUT).has_change_event_occurred(
        tmc.subarray_node, "obsState", ObsState.FAULT
    )
    assert_that(event_tracer).described_as(
        f"CSP Subarray device ({csp.csp_subarray})"
        "ObsState attribute value should move "
        f"from {ObsState.IDLE}."
    ).within_timeout(ASSERTIONS_TIMEOUT).has_change_event_occurred(
        csp.csp_subarray, "obsState", ObsState.IDLE
    )
    assert_that(event_tracer).described_as(
        f"CSP SubarrayLN device ({tmc.csp_subarray_leaf_node.dev_name()})"
        "ObsState attribute value should move "
        f"from {ObsState.IDLE}."
    ).within_timeout(ASSERTIONS_TIMEOUT).has_change_event_occurred(
        tmc.csp_subarray_leaf_node, "CspSubarrayObsState", ObsState.IDLE
    )


@given("CSP and SDP in observation state IDLE and EMPTY")
def verify_csp_mccs_sdp_obs_state_empty(csp: CSPFacade, sdp: SDPFacade):
    """Verifies observation states of the subsystems."""
    assert csp.csp_subarray.obsState == ObsState.IDLE
    assert sdp.sdp_subarray.obsState == ObsState.EMPTY
    reset_defects(csp, sdp)


@given(
    "CSP transitions to observation state EMPTY after resources are released"
)
def invoke_release_on_csp_subarray(
    tmc: TMCFacade, csp: CSPFacade, event_tracer: TangoEventTracer
):
    """Invokes release command on csp subarray"""
    csp.csp_subarray.ReleaseAllResources()
    assert_that(event_tracer).described_as(
        f"CSP Subarray device ({csp.csp_subarray})"
        "ObsState attribute value should move "
        f"from {ObsState.EMPTY}."
    ).within_timeout(ASSERTIONS_TIMEOUT).has_change_event_occurred(
        csp.csp_subarray, "obsState", ObsState.EMPTY
    )
    assert_that(event_tracer).described_as(
        f"CSP SubarrayLN device ({tmc.csp_subarray_leaf_node.dev_name()})"
        "ObsState attribute value should move "
        f"from {ObsState.EMPTY}."
    ).within_timeout(ASSERTIONS_TIMEOUT).has_change_event_occurred(
        tmc.csp_subarray_leaf_node, "CspSubarrayObsState", ObsState.EMPTY
    )


@when("I invoke Restart Command on the TMC Subarray")
def invoke_restart_command(tmc: TMCFacade):
    """Invokes restart command on TMC Subarray."""
    tmc.restart()


@then("TMC subarray transitions to observation state EMPTY")
def verify_tmc_subarray_transitions_to_obs_state_empty(
    event_tracer: TangoEventTracer, tmc: TMCFacade
):
    """Verifies TMC subarray observation state EMPTY after restart
    command."""
    assert_that(event_tracer).described_as(
        f"TMC Subarray Node device ({tmc.subarray_node})"
        "ObsState attribute value should move "
        f"from {ObsState.FAULT} to EMPTY."
    ).within_timeout(ASSERTIONS_TIMEOUT).has_change_event_occurred(
        tmc.subarray_node, "obsState", ObsState.EMPTY
    )
