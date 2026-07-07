"""Verify delay generation for TLE/Alt-Az/Galactic targets in TMC Mid.

This end-to-end test configures the TMC Mid subarray with an ADR-63
pointing group (`groups[].field.reference_frame`) for each of the new
reference frames added in HM-952 (tle, altaz, galactic) and verifies
that the CSP Subarray Leaf Node produces a valid delay model for it
and correctly resets the model on End.
"""
import json

import pytest
from assertpy import assert_that
from pytest_bdd import given, parsers, scenario, then, when
from ska_control_model import ObsState
from ska_tango_testing.integration import TangoEventTracer, log_events
from tango import DevState

from tests.conftest import REFERENCE_FRAME_FIELDS
from tests.resources.test_harness.central_node_mid import CentralNodeWrapperMid
from tests.resources.test_harness.helpers import (
    prepare_json_args_for_centralnode_commands,
    prepare_json_args_for_commands,
    wait_for_delay_updates_stop_on_delay_model,
    wait_till_delay_values_are_populated,
)
from tests.resources.test_harness.subarray_node import SubarrayNodeWrapper
from tests.resources.test_harness.utils.common_utils import JsonFactory
from tests.resources.test_support.constant import COMMAND_COMPLETED

TIMEOUT = 110

CONFIGURE_INTERFACE = "https://schema.skao.int/ska-tmc-configure/4.1"


@pytest.mark.batch1
@pytest.mark.SKA_mid
@scenario(
    "../features/test_harness/check_delay_for_ref_frames.feature",
    "Generate delay values for different reference frames in TMC Mid",
)
def test_reference_frame_delay_generation():
    """Verify delay generation per reference frame through TMC Mid."""


@given("a TMC in ON state")
def given_tmc_on(
    central_node_mid: CentralNodeWrapperMid,
    subarray_node: SubarrayNodeWrapper,
    event_tracer: TangoEventTracer,
):
    """Bring TMC to ON and confirm the subarray starts out EMPTY."""
    event_tracer.subscribe_event(
        central_node_mid.central_node, "telescopeState"
    )
    event_tracer.subscribe_event(
        central_node_mid.central_node, "longRunningCommandResult"
    )
    event_tracer.subscribe_event(subarray_node.subarray_node, "obsState")
    event_tracer.subscribe_event(
        subarray_node.subarray_node, "longRunningCommandResult"
    )
    log_events(
        {
            central_node_mid.central_node: [
                "telescopeState",
                "longRunningCommandResult",
            ],
            subarray_node.subarray_node: [
                "obsState",
                "longRunningCommandResult",
            ],
        }
    )

    central_node_mid.move_to_on()

    assert_that(event_tracer).described_as(
        "TelescopeState is expected to be ON",
    ).within_timeout(TIMEOUT).has_change_event_occurred(
        central_node_mid.central_node,
        "telescopeState",
        DevState.ON,
    )
    assert_that(event_tracer).described_as(
        "Subarray is expected to be in EMPTY obsState initially",
    ).within_timeout(TIMEOUT).has_change_event_occurred(
        subarray_node.subarray_node,
        "obsState",
        ObsState.EMPTY,
    )
    event_tracer.clear_events()


@given("subarray is in IDLE ObsState")
def given_subarray_idle(
    central_node_mid: CentralNodeWrapperMid,
    subarray_node: SubarrayNodeWrapper,
    event_tracer: TangoEventTracer,
    command_input_factory: JsonFactory,
):
    """Assign resources and wait until the subarray reaches IDLE."""
    assign_input_json = prepare_json_args_for_centralnode_commands(
        "assign_resources_mid", command_input_factory
    )
    _, unique_id = central_node_mid.store_resources(assign_input_json)

    assert_that(event_tracer).described_as(
        "Subarray is expected to reach IDLE obsState after AssignResources",
    ).within_timeout(TIMEOUT).has_change_event_occurred(
        subarray_node.subarray_node,
        "obsState",
        ObsState.IDLE,
    )
    assert_that(event_tracer).described_as(
        "AssignResources LRCR should complete OK",
    ).within_timeout(TIMEOUT).has_change_event_occurred(
        central_node_mid.central_node,
        "longRunningCommandResult",
        (unique_id[0], COMMAND_COMPLETED),
    )
    event_tracer.clear_events()


@when(
    parsers.parse(
        "I configure the TMC subarray with a {reference_frame} pointing target"
    )
)
def configure_with_reference_frame(
    subarray_node: SubarrayNodeWrapper,
    command_input_factory: JsonFactory,
    event_tracer: TangoEventTracer,
    reference_frame: str,
):
    """Build  Configure JSON with the ADR-63 groups[].field pointing block."""
    configure_json = json.loads(
        prepare_json_args_for_commands("configure_mid", command_input_factory)
    )
    configure_json["interface"] = CONFIGURE_INTERFACE
    configure_json["pointing"] = {
        "groups": [{"field": REFERENCE_FRAME_FIELDS[reference_frame]}],
        "correction": "UPDATE",
    }

    _, unique_id = subarray_node.execute_transition(
        "Configure", json.dumps(configure_json)
    )

    assert_that(event_tracer).described_as(
        f"Subarray should reach READY after Configure({reference_frame})",
    ).within_timeout(TIMEOUT).has_change_event_occurred(
        subarray_node.subarray_node,
        "obsState",
        ObsState.READY,
    )
    assert_that(event_tracer).described_as(
        "Configure LRCR should complete OK",
    ).within_timeout(TIMEOUT).has_change_event_occurred(
        subarray_node.subarray_node,
        "longRunningCommandResult",
        (unique_id[0], COMMAND_COMPLETED),
    )
    event_tracer.clear_events()


@then("CSP Subarray Leaf Node generates delay values for the target")
def delays_are_generated(subarray_node: SubarrayNodeWrapper):
    """Verify a non-default delay model is published,
    one entry per receptor."""
    delay_json, _ = wait_till_delay_values_are_populated(
        subarray_node.csp_subarray_leaf_node
    )

    receptor_delays = delay_json.get("receptor_delays") or []
    assert receptor_delays, "No receptor_delays generated for the target"
    for entry in receptor_delays:
        assert entry.get("receptor"), f"Empty receptor field in {entry}"
        assert entry.get(
            "xypol_coeffs_ns"
        ), f"Missing delay polynomial for receptor {entry['receptor']}"


@then("I end the observation")
def invoke_end(
    subarray_node: SubarrayNodeWrapper, event_tracer: TangoEventTracer
):
    """Invoke End and wait for IDLE."""
    subarray_node.end_observation()
    assert_that(event_tracer).described_as(
        "Subarray should return to IDLE after End",
    ).within_timeout(TIMEOUT).has_change_event_occurred(
        subarray_node.subarray_node,
        "obsState",
        ObsState.IDLE,
    )


@then("CSP Subarray Leaf Node stops generating delay values")
def delays_are_reset(subarray_node: SubarrayNodeWrapper):
    """Verify delayModel is reset to the initial default after End."""
    wait_for_delay_updates_stop_on_delay_model(
        subarray_node.csp_subarray_leaf_node
    )