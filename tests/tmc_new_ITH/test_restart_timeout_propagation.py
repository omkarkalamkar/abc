"""
Test for Restart timeout error propagation verification
"""
import json
import logging

import pytest
from assertpy import assert_that
from pytest_bdd import given, parsers, scenario, then, when
from ska_control_model import ObsState
from ska_integration_test_harness.facades.csp_facade import CSPFacade
from ska_integration_test_harness.facades.sdp_facade import SDPFacade
from ska_integration_test_harness.facades.tmc_facade import TMCFacade
from ska_integration_test_harness.inputs.test_harness_inputs import (
    TestHarnessInputs,
)
from ska_ser_logging import configure_logging
from ska_tango_testing.integration import TangoEventTracer, log_events

from tests.tmc_csp_new_ITH.conftest import SubarrayTestContextData
from tests.tmc_new_ITH.conftest import get_abort_command_timeout

configure_logging(logging.DEBUG)
LOGGER = logging.getLogger(__name__)

exception_messages = {
    "CSP": (
        '[3, "Exception occurred on the following devices: '
        "mid-tmc/subarray-leaf-node-csp/01: Timeout has occurred,"
        ' command failed"]'
    ),
    "SDP": (
        '[3, "Exception occurred on the following devices:'
        " mid-tmc/subarray-leaf-node-sdp/01: Timeout has occurred, "
        'command failed"]'
    ),
}

ABORT_COMMAND_TIMEOUT = get_abort_command_timeout()
# It is expected that required event will get generated
# once command timeout is captured on the subarraynode
ASSERTIONS_TIMEOUT = ABORT_COMMAND_TIMEOUT + 10

# Delay multiplier: In CI (60s timeout), use 1.2x;
# In local builds (130s timeout), use 1.05x to avoid unnecessary waiting
DELAY_MULTIPLIER = 1.2 if ABORT_COMMAND_TIMEOUT < 100 else 1.05


def _setup_event_subscriptions(
    tmc: TMCFacade,
    csp: CSPFacade,
    sdp: SDPFacade,
    event_tracer: TangoEventTracer,
):
    """Subscribe TMC, CSP and SDP devices to track and log obsState events.

    :param tmc: the TMC facade.
    :param csp: the CSP facade.
    :param sdp: the SDP facade.
    :param event_tracer: the event tracer.
    """
    event_tracer.subscribe_event(tmc.subarray_node, "obsState")
    event_tracer.subscribe_event(csp.csp_subarray, "obsState")
    event_tracer.subscribe_event(sdp.sdp_subarray, "obsState")
    event_tracer.subscribe_event(
        tmc.csp_subarray_leaf_node, "cspSubarrayObsState"
    )
    event_tracer.subscribe_event(
        tmc.sdp_subarray_leaf_node, "sdpSubarrayObsState"
    )
    event_tracer.subscribe_event(tmc.central_node, "longRunningCommandResult")
    event_tracer.subscribe_event(tmc.subarray_node, "longRunningCommandResult")

    log_events(
        {
            tmc.subarray_node: [
                "obsState",
                "longRunningCommandResult",
            ],
            csp.csp_subarray: ["obsState"],
            sdp.sdp_subarray: ["obsState"],
            tmc.csp_subarray_leaf_node: ["cspSubarrayObsState"],
            tmc.sdp_subarray_leaf_node: ["sdpSubarrayObsState"],
            tmc.central_node: ["longRunningCommandResult"],
        },
        event_enum_mapping={"obsState": ObsState},
    )


@pytest.mark.SKA_mid
@scenario(
    "../tmc_new_ITH/features/timeout_handling.feature",
    "Timeout reported by TMC Mid Restart command for subsystem subarray",
)
def test_verify_restart_timeout_error_propagation():
    """Test for Restart command timeout error propagation."""


@given("the TMC subarray is in the ABORTED observation state")
def subarray_in_aborted_obsstate(
    context_fixt: SubarrayTestContextData,
    tmc: TMCFacade,
    sdp: SDPFacade,
    csp: CSPFacade,
    event_tracer: TangoEventTracer,
    default_commands_inputs: TestHarnessInputs,
):
    """Ensure the subarray is in ABORTED obsstate."""
    _setup_event_subscriptions(tmc, csp, sdp, event_tracer)
    context_fixt.starting_state = ObsState.ABORTED

    tmc.force_change_of_obs_state(
        ObsState.ABORTED,
        default_commands_inputs,
        wait_termination=True,
    )


@when(
    parsers.parse(
        "Restart is invoked on tmc with command timeout on {subsystem}"
    )
)
def send_restart_command(
    context_fixt: SubarrayTestContextData,
    tmc: TMCFacade,
    csp: CSPFacade,
    sdp: SDPFacade,
    subsystem: str,
):
    """
    Send the Restart command to the subarray.

    This step uses the tmc to send an Restart command to the
    specified subarray with provided defective subsystem.
    """
    # Delay is set more than Restart command timeout to
    # generate restart command timeout on the subarray node
    # Use DELAY_MULTIPLIER to scale with timeout
    delay = int(ABORT_COMMAND_TIMEOUT * DELAY_MULTIPLIER)
    if subsystem == "CSP":
        csp.csp_subarray.SetDelayInfo(json.dumps({"Restart": delay}))
    if subsystem == "SDP":
        sdp.sdp_subarray.SetDelayInfo(json.dumps({"Restart": delay}))
    context_fixt.when_action_name = "Restart"

    _, pytest.unique_id = tmc.subarray_node.Restart()


@then(
    parsers.parse(
        "the command failure is reported by subarray with"
        " timeout error message with {subsystem}"
    )
)
def verify_error_message(
    tmc: TMCFacade,
    csp: CSPFacade,
    sdp: SDPFacade,
    event_tracer: TangoEventTracer,
    subsystem: str,
):
    """
    Verify the tmc subarray reports timeout on its LRCR.
    """
    expected_msg = exception_messages[subsystem]

    assert_that(event_tracer).described_as(
        'FAILED ASSUMPTION IN "THEN" STEP: '
        "'the subarray is in RESTARTING obsState' "
        "TMC Subarray Node device "
        f"({tmc.subarray_node.dev_name()}) "
        "is expected have longRunningCommandResult as "
        "(unique_id, COMMAND_RESULT)",
    ).within_timeout(ASSERTIONS_TIMEOUT).has_change_event_occurred(
        tmc.subarray_node,
        "longRunningCommandResult",
        (pytest.unique_id[0], expected_msg),
    )
    if subsystem == "CSP":
        csp.csp_subarray.ResetDelayInfo()
    elif subsystem == "SDP":
        sdp.sdp_subarray.ResetDelayInfo()

    assert_that(event_tracer).described_as(
        'FAILED ASSUMPTION IN "THEN" STEP: '
        "'the tmc subarray must be in the RESTARTING obsState' "
        "TMC Subarray device"
        f"({tmc.subarray_node.dev_name()}) "
        "is expected to be in FAULT obstate",
    ).within_timeout(ASSERTIONS_TIMEOUT).has_change_event_occurred(
        tmc.subarray_node,
        "obsState",
        ObsState.FAULT,
    )
    event_tracer.clear_events()
    if subsystem == "CSP":
        assert_that(event_tracer).described_as(
            'FAILED ASSUMPTION IN "THEN" STEP: '
            f"({tmc.csp_subarray_leaf_node.dev_name()}) "
            "is expected to be in EMPTY obstate",
        ).within_timeout(ASSERTIONS_TIMEOUT).has_change_event_occurred(
            tmc.csp_subarray_leaf_node,
            "cspSubarrayObsState",
            ObsState.EMPTY,
        )
    elif subsystem == "SDP":
        assert_that(event_tracer).described_as(
            'FAILED ASSUMPTION IN "THEN" STEP: '
            f"({tmc.sdp_subarray_leaf_node.dev_name()}) "
            "is expected to be in EMPTY obstate",
        ).within_timeout(ASSERTIONS_TIMEOUT).has_change_event_occurred(
            tmc.sdp_subarray_leaf_node,
            "sdpSubarrayObsState",
            ObsState.EMPTY,
        )
