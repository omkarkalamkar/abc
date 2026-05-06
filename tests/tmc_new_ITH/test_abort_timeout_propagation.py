"""
Test for Abort() error propagation verification
"""
import json
import logging
import time

import pytest
from assertpy import assert_that
from pytest_bdd import given, parsers, scenario, then, when
from ska_control_model import ObsState
from ska_integration_test_harness.facades.csp_facade import CSPFacade
from ska_integration_test_harness.facades.dishes_facade import DishesFacade
from ska_integration_test_harness.facades.sdp_facade import SDPFacade
from ska_integration_test_harness.facades.tmc_facade import TMCFacade
from ska_integration_test_harness.inputs.test_harness_inputs import (
    TestHarnessInputs,
)
from ska_ser_logging import configure_logging
from ska_tango_testing.integration import TangoEventTracer, log_events

from tests.resources.test_support.enum import PointingState
from tests.tmc_csp_new_ITH.conftest import SubarrayTestContextData
from tests.tmc_new_ITH.conftest import get_abort_command_timeout

configure_logging(logging.DEBUG)
LOGGER = logging.getLogger(__name__)

COMMAND_RESULT_CSP = (
    '[3, "Exception occurred on the following devices: '
    'mid-tmc/subarray-leaf-node-csp/01: Timeout has occurred, command failed"]'
)
COMMAND_RESULT_SDP = (
    '[3, "Exception occurred on the following devices:'
    " mid-tmc/subarray-leaf-node-sdp/01: Timeout has occurred, "
    'command failed"]'
)
COMMAND_RESULT_DISH = (
    '[3, "Exception occurred on the following devices:'
    " mid-tmc/leaf-node-dish/ska001: Timeout has occurred, "
    'command failed"]'
)

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
    dishes: DishesFacade,
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
        dishes.dish_master_dict["dish_001"], "pointingState"
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
    "../tmc_new_ITH/features/timeout_handling.feature",
    "Timeout reported by TMC Mid Abort command for subsystem subarray",
)
def test_verify_timeout_error_propagation():
    """Test for Abort command timeout error propagation."""


@given("the TMC subarray is in the READY observation state")
def subarray_in_idle_obsstate(
    context_fixt: SubarrayTestContextData,
    tmc: TMCFacade,
    sdp: SDPFacade,
    csp: CSPFacade,
    dishes: DishesFacade,
    event_tracer: TangoEventTracer,
    default_commands_inputs: TestHarnessInputs,
):
    """Ensure the subarray is in READY obsstate."""

    _setup_event_subscriptions(tmc, csp, sdp, dishes, event_tracer)
    context_fixt.starting_state = ObsState.READY

    tmc.force_change_of_obs_state(
        ObsState.READY,
        default_commands_inputs,
        wait_termination=True,
    )


@when(
    parsers.parse(
        "Abort is invoked on tmc with command timeout on {subsystem}"
    )
)
def send_abort_command(
    context_fixt: SubarrayTestContextData,
    tmc: TMCFacade,
    csp: CSPFacade,
    sdp: SDPFacade,
    dishes: DishesFacade,
    subsystem: str,
):
    """
    Send the Abort command to the subarray.

    This step uses the tmc to send an Abort command to the
    specified subarray with provided defective subsystem.
    """
    # Delay is set more than Abort command timeout to
    # generate Abort command timeout on the subarray node
    # Use DELAY_MULTIPLIER to scale with timeout
    delay = int(ABORT_COMMAND_TIMEOUT * DELAY_MULTIPLIER)
    if subsystem == "CSP":
        csp.csp_subarray.SetDelayInfo(json.dumps({"Abort": delay}))
    if subsystem == "SDP":
        sdp.sdp_subarray.SetDelayInfo(json.dumps({"Abort": delay}))
    if subsystem == "Dish":
        dish1 = dishes.dish_master_dict["dish_001"]
        dish1.SetDelayInfo(json.dumps({"Abort": delay}))
    context_fixt.when_action_name = "Abort"
    _, pytest.unique_id = tmc.subarray_node.Abort()


@then("the TMC SubarrayNode obsstate changes to FAULT obsState after timeout")
def verify_fault_obsstate(
    tmc: TMCFacade,
    event_tracer: TangoEventTracer,
):
    """
    Verify the subarray's transition to the FAULT observation state.
    """
    assert_that(event_tracer).described_as(
        'FAILED ASSUMPTION IN "THEN" STEP: '
        "'the tmc subarray must be in the ABORTING obsState' "
        "TMC Subarray device"
        f"({tmc.subarray_node.dev_name()}) "
        "is expected to be in ABORTING obstate",
    ).within_timeout(ASSERTIONS_TIMEOUT).has_change_event_occurred(
        tmc.subarray_node,
        "obsState",
        ObsState.ABORTING,
    )

    assert_that(event_tracer).described_as(
        'FAILED ASSUMPTION IN "THEN" STEP: '
        "'the tmc subarray must be in the FAULT obsState' "
        "TMC Subarray device"
        f"({tmc.subarray_node.dev_name()}) "
        "is expected to be in FAULT obstate",
    ).within_timeout(ASSERTIONS_TIMEOUT).has_change_event_occurred(
        tmc.subarray_node,
        "obsState",
        ObsState.FAULT,
    )


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
    dishes: DishesFacade,
    event_tracer: TangoEventTracer,
    subsystem: str,
):
    """
    Verify the tmc subarray reports timeout on its LRCR.
    """
    if subsystem == "CSP":
        assert_that(event_tracer).described_as(
            'FAILED ASSUMPTION IN "THEN" STEP: '
            "'the subarray is in FAULT obsState' "
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
        # FAULT obsState is not considered in tear_down
        csp.csp_subarray.ResetDelayInfo()

        assert_that(event_tracer).described_as(
            'FAILED ASSUMPTION IN "THEN" STEP: '
            "'the csp subarray must be in the ABORTED obsState'"
            "CSP Subarray device"
            f"({csp.csp_subarray.dev_name()}) "
            "is expected to be in ABORTED obstate",
        ).within_timeout(ASSERTIONS_TIMEOUT).has_change_event_occurred(
            csp.csp_subarray,
            "obsState",
            ObsState.ABORTED,
        )

    if subsystem == "SDP":
        assert_that(event_tracer).described_as(
            'FAILED ASSUMPTION IN "THEN" STEP: '
            "'the subarray is in FAULT obsState' "
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
        # FAULT obsState is not considered in tear_down
        sdp.sdp_subarray.ResetDelayInfo()
        assert_that(event_tracer).described_as(
            'FAILED ASSUMPTION IN "THEN" STEP: '
            "'the sdp subarray must be in the ABORTED obsState'"
            "SDP Subarray device"
            f"({sdp.sdp_subarray.dev_name()}) "
            "is expected to be in ABORTED obstate",
        ).within_timeout(ASSERTIONS_TIMEOUT).has_change_event_occurred(
            sdp.sdp_subarray,
            "obsState",
            ObsState.ABORTED,
        )

    if subsystem == "Dish":
        assert_that(event_tracer).described_as(
            'FAILED ASSUMPTION IN "THEN" STEP: '
            "'the subarray is in FAULT obsState' "
            "TMC Subarray Node device "
            f"({tmc.subarray_node.dev_name()}) "
            "is expected have longRunningCommandResult as "
            "(unique_id, COMMAND_RESULT)",
        ).within_timeout(ASSERTIONS_TIMEOUT).has_change_event_occurred(
            tmc.subarray_node,
            "longRunningCommandResult",
            (pytest.unique_id[0], COMMAND_RESULT_DISH),
        )
        # tear_down as TMC is inconsistent state. Also
        # FAULT obsState is not considered in tear_down
        dish1 = dishes.dish_master_dict["dish_001"]
        dish1.ResetDelayInfo()
        assert_that(event_tracer).described_as(
            'FAILED ASSUMPTION IN "THEN" STEP: '
            "'the dish must be in the READY pointingState' "
            "Dish device"
            f"({dish1.dev_name()}) "
            "is expected to be in READY pointingState",
        ).within_timeout(ASSERTIONS_TIMEOUT).has_change_event_occurred(
            dish1,
            "pointingState",
            PointingState.READY,
        )

    # After the TMC SubarrayNode reaches the FAULT obsState, we need to bring
    # it back to EMPTY by sending a restart command.
    # Before sending the restart, we wait briefly to ensure that the CSP
    # subarray leaf node has reported the ABORTED obsState to the TMC
    # subarray node. This ensures the restart command will be processed
    # correctly.
    # In some cases, if the ABORTED obsState event from the CSP subarray
    # leaf node is not received by the TMC subarray node, the restart
    # command will not be sent to the CSP subarray leaf node. Therefore,
    # this sleep is necessary to allow event propagation.
    # It needs to be updated once required support to check
    # leaf nodes obsState is implemented in the ITH.
    time.sleep(0.5)
    tmc.restart()
