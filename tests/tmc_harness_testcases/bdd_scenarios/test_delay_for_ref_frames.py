"""HM-972: Verify delay generation for TLE/Alt-az/Galactic targets in TMC Mid.

This end-to-end test configures the TMC Mid subarray with a pointing target for
each of the reference frames added in HM-952 (tle, altaz, galactic) and
verifies that the CSP Subarray Leaf Node generates delay values for it (used
for holography testing by the AIV team).

Note:
    Requires the CSP Subarray Leaf Node with TLE/Alt-az support (HM-952) to be
    deployed. Against an older leaf node the Configure with these targets will
    be rejected and the subarray will not reach READY.
"""
import json
import logging

import pytest
from pytest_bdd import given, parsers, scenario, then, when
from ska_control_model import ObsState
from tango import DevState

from tests.conftest import MID_DELAY_JSON, REFERENCE_FRAME_FIELDS
from tests.resources.test_harness.central_node_mid import CentralNodeWrapperMid
from tests.resources.test_harness.event_recorder import EventRecorder
from tests.resources.test_harness.helpers import (
    prepare_json_args_for_centralnode_commands,
    prepare_json_args_for_commands,
    wait_till_delay_values_are_populated,
)
from tests.resources.test_harness.subarray_node import SubarrayNodeWrapper
from tests.resources.test_harness.utils.common_utils import JsonFactory

LOGGER = logging.getLogger(__name__)

# Interface that supports the tle/altaz/galactic pointing reference frames.
CONFIGURE_INTERFACE = "https://schema.skao.int/ska-tmc-configure/4.1"


@pytest.mark.batch1
@pytest.mark.SKA_mid
@scenario(
    "../features/test_harness/check_delay_for_ref_frames.feature",
    "Generate delay values for a <reference_frame> target",
)
def test_reference_frame_delay_generation() -> None:
    """Verify delay generation per reference frame through TMC Mid."""


@given("the telescope is in ON state")
def check_telescope_is_in_on_state(
    central_node_mid: CentralNodeWrapperMid, event_recorder: EventRecorder
) -> None:
    """Ensure the telescope is in the ON state."""
    central_node_mid.move_to_on()
    event_recorder.subscribe_event(
        central_node_mid.central_node, "telescopeState"
    )
    assert event_recorder.has_change_event_occurred(
        central_node_mid.central_node,
        "telescopeState",
        DevState.ON,
    )


@given(parsers.parse("TMC subarray {subarray_id} in ObsState IDLE"))
def move_subarray_node_to_idle_obsstate(
    central_node_mid: CentralNodeWrapperMid,
    event_recorder: EventRecorder,
    command_input_factory: JsonFactory,
    subarray_id: str,
) -> None:
    """Move the TMC Subarray to the IDLE ObsState."""
    central_node_mid.set_subarray_id(subarray_id)
    assign_input_json = prepare_json_args_for_centralnode_commands(
        "assign_resources_mid", command_input_factory
    )
    assign_input = json.loads(assign_input_json)
    assign_input["subarray_id"] = int(subarray_id)
    central_node_mid.store_resources(json.dumps(assign_input))

    event_recorder.subscribe_event(central_node_mid.subarray_node, "obsState")
    assert event_recorder.has_change_event_occurred(
        central_node_mid.subarray_node,
        "obsState",
        ObsState.IDLE,
    )


@when(
    parsers.parse(
        "I configure the TMC subarray with a {reference_frame} target"
    )
)
def invoke_configure_command_with_reference_frame(
    subarray_node: SubarrayNodeWrapper,
    command_input_factory: JsonFactory,
    event_recorder: EventRecorder,
    reference_frame: str,
) -> None:
    """Configure the subarray with a pointing target for the given frame."""
    configure_json = json.loads(
        prepare_json_args_for_commands("configure_mid", command_input_factory)
    )
    configure_json["interface"] = CONFIGURE_INTERFACE
    configure_json["pointing"] = {
        "groups": [{"field": REFERENCE_FRAME_FIELDS[reference_frame]}],
        "correction": "UPDATE",
    }
    subarray_node.store_configuration_data(json.dumps(configure_json))
    event_recorder.subscribe_event(subarray_node.subarray_node, "obsState")
    assert event_recorder.has_change_event_occurred(
        subarray_node.subarray_node,
        "obsState",
        ObsState.READY,
    )


@then("CSP Subarray Leaf Node generates delay values for the target")
def check_delay_values_generated(
    subarray_node: SubarrayNodeWrapper,
) -> None:
    """Verify delay values are generated for the configured target."""
    delay_json, delay_generated_time = wait_till_delay_values_are_populated(
        subarray_node.csp_subarray_leaf_node
    )
    LOGGER.info("Delay JSON generated for target: %s", delay_json)
    LOGGER.info("Delay generated at: %s", delay_generated_time)

    # Delays must have been generated (i.e. no longer the reset/initial value)
    assert delay_json != MID_DELAY_JSON
    receptor_delays = delay_json.get("receptor_delays")
    assert receptor_delays, "No receptor_delays generated for the target"
    for receptor_delay in receptor_delays:
        assert receptor_delay.get(
            "xypol_coeffs_ns"
        ), f"Missing delay coefficients for receptor {receptor_delay}"


@when("I end the observation")
def invoke_end_command(
    subarray_node: SubarrayNodeWrapper, event_recorder: EventRecorder
) -> None:
    """Invoke End and verify the subarray returns to IDLE."""
    subarray_node.end_observation()
    event_recorder.subscribe_event(subarray_node.subarray_node, "obsState")
    assert event_recorder.has_change_event_occurred(
        subarray_node.subarray_node,
        "obsState",
        ObsState.IDLE,
    )


@then("CSP Subarray Leaf Node stops generating delay values")
def check_delay_values_stopped(
    subarray_node: SubarrayNodeWrapper,
) -> None:
    """Verify delay generation stops after End."""
    cspsal_node = subarray_node.csp_subarray_leaf_node
    delay_json = json.loads(cspsal_node.read_attribute("delayModel").value)
    assert delay_json == MID_DELAY_JSON
