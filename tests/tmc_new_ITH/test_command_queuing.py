"""Verifies bug SKB-918
"""
import json

import pytest
from assertpy import assert_that
from pytest_bdd import given, scenario, then, when
from ska_control_model import ObsState, ResultCode
from ska_integration_test_harness.facades.csp_facade import CSPFacade
from ska_integration_test_harness.facades.sdp_facade import SDPFacade
from ska_integration_test_harness.facades.tmc_facade import TMCFacade
from ska_integration_test_harness.inputs.json_input import DictJSONInput
from ska_integration_test_harness.inputs.test_harness_inputs import (
    TestHarnessInputs,
)
from ska_tango_testing.integration import TangoEventTracer, log_events

from tests.resources.test_support.constant import (
    EVENT_DEFECT,
    RECEIVE_ADDRESSES,
    RESET_DEFECT,
)
from tests.tmc_csp_new_ITH.conftest import (
    ASSERTIONS_TIMEOUT,
    SubarrayTestContextData,
)
from tests.tmc_csp_new_ITH.utils.my_file_json_input import MyFileJSONInput


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
    event_tracer.subscribe_event(sdp.sdp_subarray, "receiveAddresses")
    event_tracer.subscribe_event(sdp.sdp_subarray, "commandCallInfo")
    event_tracer.subscribe_event(tmc.central_node, "longRunningCommandResult")
    event_tracer.subscribe_event(tmc.subarray_node, "longRunningCommandResult")

    log_events(
        {
            tmc.subarray_node: [
                "obsState",
                "longRunningCommandResult",
            ],
            csp.csp_subarray: ["obsState"],
            sdp.sdp_subarray: [
                "obsState",
                "commandCallInfo",
                "receiveAddresses",
            ],
            tmc.central_node: ["longRunningCommandResult"],
        },
        event_enum_mapping={"obsState": ObsState},
    )


@pytest.mark.batch1
@pytest.mark.SKA_mid
@scenario(
    "../tmc_new_ITH/features/command_queue.feature",
    "Test command queuing",
)
def test_command_queuing():
    """Test command queuing"""


@given("the subarray is in the EMPTY state")
def subarray_in_empty_state(
    context_fixt: SubarrayTestContextData,
    tmc: TMCFacade,
    sdp: SDPFacade,
    csp: CSPFacade,
    event_tracer: TangoEventTracer,
    default_commands_inputs: TestHarnessInputs,
):
    """Ensure the subarray is in the EMPTY state."""
    _setup_event_subscriptions(tmc, csp, sdp, event_tracer)
    context_fixt.starting_state = ObsState.IDLE
    sdp.sdp_subarray.SetDirectreceiveAddresses("{}")
    sdp.sdp_subarray.SetDefective(EVENT_DEFECT)
    sdp.sdp_subarray.SetDirectreceiveAddresses(RECEIVE_ADDRESSES)
    sdp.sdp_subarray.SetDefective(RESET_DEFECT)
    tmc.force_change_of_obs_state(
        ObsState.EMPTY,
        default_commands_inputs,
        wait_termination=True,
    )


@when("I queue Configure and Scan command")
def invoke_all_commands(tmc: TMCFacade, event_tracer):
    """Invoke Assign Resources,"""
    json_input = MyFileJSONInput(
        "centralnode", "assign_resources_mid"
    ).with_attribute("subarray_id", 1)
    assign_json = json.loads(json_input.as_str())

    pytest.assign_result = tmc.assign_resources(
        DictJSONInput(assign_json),
        wait_termination=False,
    )
    assert_that(event_tracer).described_as(
        "AssignResources command should complete successfully"
    ).within_timeout(ASSERTIONS_TIMEOUT).has_change_event_occurred(
        tmc.central_node,
        "longRunningCommandResult",
        (
            pytest.assign_result[1][0],
            json.dumps(((ResultCode.OK), "Command Completed")),
        ),
    )
    json_input = MyFileJSONInput("subarray", "command_Configure")
    configure_json = json.loads(json_input.as_str())
    pytest.configure_result = tmc.configure(
        DictJSONInput(configure_json),
        wait_termination=False,
    )

    json_input = MyFileJSONInput("subarray", "scan_mid")
    pytest.scan_result = tmc.scan(
        json_input,
        wait_termination=False,
    )


@then("the command results of Configure and Scan transitions to OK")
def command_results_ok(event_tracer, tmc: TMCFacade):
    """Check all results ok"""

    assert_that(event_tracer).described_as(
        "Configure command should complete successfully"
    ).within_timeout(ASSERTIONS_TIMEOUT).has_change_event_occurred(
        tmc.subarray_node,
        "longRunningCommandResult",
        (
            pytest.configure_result[1][0],
            json.dumps(((ResultCode.OK), "Command Completed")),
        ),
    )

    assert_that(event_tracer).described_as(
        "Scan command should complete successfully"
    ).within_timeout(ASSERTIONS_TIMEOUT).has_change_event_occurred(
        tmc.subarray_node,
        "longRunningCommandResult",
        (
            pytest.scan_result[1][0],
            json.dumps(((ResultCode.OK), "Command Completed")),
        ),
    )


@then("the subarray transitions to the READY state")
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
    ).has_change_event_occurred(
        csp.csp_subarray,
        "obsState",
        ObsState.READY,
    ).has_change_event_occurred(
        sdp.sdp_subarray,
        "obsState",
        ObsState.READY,
    )
