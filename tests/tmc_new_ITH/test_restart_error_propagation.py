"""
Test for Restart() error propagation verification
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

from tests.resources.test_support.constant import (
    ERROR_PROPAGATION_DEFECT,
    FAILED_RESULT_DEFECT,
)
from tests.tmc_csp_new_ITH.conftest import (
    ASSERTIONS_TIMEOUT,
    SubarrayTestContextData,
)

configure_logging(logging.DEBUG)
LOGGER = logging.getLogger(__name__)

COMMAND_RESULT_CSP = (
    '[3, "Exception occurred on the following devices: '
    "mid-tmc/subarray-leaf-node-csp/01: Exception occurred on devices: "
    'mid-csp/subarray/01: Exception occurred, command failed."]'
)

COMMAND_RESULT_SDP = (
    '[3, "Exception occurred on the following devices: '
    "mid-tmc/subarray-leaf-node-sdp/01: Exception occurred on devices: "
    'mid-sdp/subarray/01: Exception occurred, command failed"]'
)


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
    event_tracer.subscribe_event(tmc.central_node, "longRunningCommandResult")
    event_tracer.subscribe_event(tmc.subarray_node, "longRunningCommandResult")
    event_tracer.subscribe_event(
        tmc.csp_subarray_leaf_node, "cspSubarrayObsState"
    )
    event_tracer.subscribe_event(
        tmc.sdp_subarray_leaf_node, "sdpSubarrayObsState"
    )

    log_events(
        {
            tmc.subarray_node: [
                "obsState",
                "longRunningCommandResult",
            ],
            csp.csp_subarray: ["obsState"],
            sdp.sdp_subarray: ["obsState"],
            tmc.central_node: ["longRunningCommandResult"],
        },
        event_enum_mapping={"obsState": ObsState},
    )


@pytest.mark.batch1
@pytest.mark.SKA_mid
@scenario(
    "../tmc_new_ITH/features/error_propagation.feature",
    "Error Propagation Reported by TMC Mid Restart command for"
    " defective subsystem subarray",
)
def test_verify_abort_restart_propagation():
    """Test for Abort command restart propagation."""


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
        "Restart is invoked on a defective subsystem {defective_subsystem}"
    )
)
def send_restart_command(
    context_fixt: SubarrayTestContextData,
    tmc: TMCFacade,
    csp: CSPFacade,
    sdp: SDPFacade,
    defective_subsystem: str,
):
    """
    Send the Restart command to the subarray.

    This step uses the tmc to send an Abort command to the
    specified subarray with provided defective subsystem.
    """
    if defective_subsystem == "CSP":
        csp.csp_subarray.SetDefective(ERROR_PROPAGATION_DEFECT)
    if defective_subsystem == "SDP":
        sdp.sdp_subarray.SetDefective(FAILED_RESULT_DEFECT)
    context_fixt.when_action_name = "Restart"
    _, pytest.unique_id = tmc.subarray_node.Restart()


@then("the TMC SubarrayNode obsstate stuck into RESTARTING obsState")
def verify_restarting_obsstate(
    tmc: TMCFacade,
    event_tracer: TangoEventTracer,
):
    """
    Verify the subarray's stuck into the RESTARTING observation state.
    """
    assert_that(event_tracer).described_as(
        'FAILED ASSUMPTION IN "THEN" STEP: '
        "'the tmc subarray must be in the RESTARTING obsState' "
        "TMC Subarray device"
        f"({tmc.subarray_node.dev_name()}) "
        "is expected to be in RESTARTING obstate",
    ).within_timeout(ASSERTIONS_TIMEOUT).has_change_event_occurred(
        tmc.subarray_node,
        "obsState",
        ObsState.RESTARTING,
    )


@then(
    parsers.parse(
        "the command failure is reported by subarray with error"
        " message with {defective_subsystem}"
    )
)
def verify_error_message(
    tmc: TMCFacade,
    csp: CSPFacade,
    sdp: SDPFacade,
    event_tracer: TangoEventTracer,
    defective_subsystem: str,
):
    """
    Verify the subarray's reports exception on its LRCR.
    """
    if defective_subsystem == "CSP":
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
            (pytest.unique_id[0], COMMAND_RESULT_CSP),
        )

        # tear_down as TMC is inconsistent state. Also
        # no command is allowed in RESTARTING obsState
        csp.csp_subarray.SetDefective(
            json.dumps({"enabled": False, "fault_type": 0})
        )
        csp.csp_subarray.Restart()
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
        assert_that(event_tracer).described_as(
            'FAILED ASSUMPTION IN "THEN" STEP: '
            "'the csp subarray must be in the EMPTY obsState'"
            "CSP Subarray device"
            f"({csp.csp_subarray.dev_name()}) "
            "is expected to be in EMPTY obstate",
        ).within_timeout(ASSERTIONS_TIMEOUT).has_change_event_occurred(
            csp.csp_subarray,
            "obsState",
            ObsState.EMPTY,
        )
        csp.csp_subarray.SetDirectObsState(ObsState.EMPTY)

    if defective_subsystem == "SDP":
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
            (pytest.unique_id[0], COMMAND_RESULT_SDP),
        )
        # tear_down as TMC is inconsistent state. Also
        # no command is allowed in RESTARTING obsState
        sdp.sdp_subarray.SetDefective(
            json.dumps({"enabled": False, "fault_type": 0})
        )
        sdp.sdp_subarray.Restart()
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
        assert_that(event_tracer).described_as(
            'FAILED ASSUMPTION IN "THEN" STEP: '
            "'the sdp subarray must be in the EMPTY obsState'"
            "SDP Subarray device"
            f"({sdp.sdp_subarray.dev_name()}) "
            "is expected to be in EMPTY obstate",
        ).within_timeout(ASSERTIONS_TIMEOUT).has_change_event_occurred(
            sdp.sdp_subarray,
            "obsState",
            ObsState.EMPTY,
        )
        sdp.sdp_subarray.SetDirectObsState(ObsState.EMPTY)
