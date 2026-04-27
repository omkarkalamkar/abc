"""
Test for Abort() error propagation verification
"""
import json
import logging

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
    'mid-sdp/subarray/01: Exception occurred, command failed."]'
)

COMMAND_RESULT_DISH = (
    '[3, "Exception occurred on the following devices: '
    "mid-tmc/leaf-node-dish/ska001: Exception occurred on devices: "
    'mid-dish/dish-manager/ska001: Exception occurred, command failed."]'
)


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
    "../tmc_new_ITH/features/error_propagation.feature",
    "Error Propagation Reported by TMC Mid Abort command for"
    " defective subsystem subarray",
)
def test_verify_abort_error_propagation():
    """Test for Abort command error propagation."""


@given("the TMC subarray is in the READY observation state")
def subarray_in_ready_obsstate(
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
        "Abort is invoked on a defective subsystem {defective_subsystem}"
    )
)
def send_abort_command(
    context_fixt: SubarrayTestContextData,
    tmc: TMCFacade,
    csp: CSPFacade,
    sdp: SDPFacade,
    dishes: DishesFacade,
    defective_subsystem: str,
):
    """
    Send the Abort command to the subarray.

    This step uses the tmc to send an Abort command to the
    specified subarray with provided defective subsystem.
    """
    if defective_subsystem == "CSP":
        csp.csp_subarray.SetDefective(ERROR_PROPAGATION_DEFECT)
    if defective_subsystem == "SDP":
        sdp.sdp_subarray.SetDefective(FAILED_RESULT_DEFECT)
    if defective_subsystem == "Dish":
        dish1 = dishes.dish_master_dict["dish_001"]
        dish1.SetDefective(ERROR_PROPAGATION_DEFECT)
    context_fixt.when_action_name = "Abort"
    _, pytest.unique_id = tmc.subarray_node.Abort()


@then("the TMC SubarrayNode obsstate changes to FAULT obsState")
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
        "the command failure is reported by subarray with error"
        " message with {defective_subsystem}"
    )
)
def verify_error_message(
    tmc: TMCFacade,
    csp: CSPFacade,
    sdp: SDPFacade,
    dishes: DishesFacade,
    event_tracer: TangoEventTracer,
    defective_subsystem: str,
):
    """
    Verify the subarray's reports exception on its LRCR.
    """
    if defective_subsystem == "CSP":
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

        csp.csp_subarray.SetDefective(json.dumps({"enabled": False}))

    if defective_subsystem == "SDP":
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
        sdp.sdp_subarray.SetDirectObsState(ObsState.FAULT)
        sdp.sdp_subarray.SetDefective(json.dumps({"enabled": False}))

    if defective_subsystem == "Dish":
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
        dish1 = dishes.dish_master_dict["dish_001"]
        dish1.SetDefective(json.dumps({"enabled": False}))
