"""Verify delay generation for TLE/Alt-Az/Galactic targets in TMC Mid.

This end-to-end test configures the TMC Mid subarray with an ADR-63
pointing group (`groups[].field.reference_frame`) for each of the
reference frames (icrs, special, tle, altaz, galactic) and verifies
that the CSP Subarray Leaf Node produces a valid delay model for it
and correctly resets the model on End.
"""
import json
import logging

import pytest
from pytest_bdd import given, parsers, scenario, then, when
from ska_control_model import ObsState
from tango import DevState

from tests.conftest import MID_DELAY_JSON
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

ADR63_POINTING_SAMPLES = {
    "icrs": {
        "groups": [
            {
                "field": {
                    "target_name": "Polaris Australis",
                    "reference_frame": "icrs",
                    "attrs": {"c1": 317.199, "c2": -88.95636},
                }
            }
        ]
    },
    "tle": {
        "groups": [
            {
                "field": {
                    "target_name": "ANGOSAT 2",
                    "reference_frame": "tle",
                    "attrs": {
                        "line1": "1 54033U 22131A   26187.02363267  "
                        ".00000150  00000+0  00000+0 0  9991",
                        "line2": "2 54033   0.0192 123.5880 0000094 "
                        "274.7177 277.2087  1.00271785 13664",
                    },
                }
            }
        ]
    },
    "altaz": {
        "groups": [
            {
                "field": {
                    "target_name": "South Celestial Pole",
                    "reference_frame": "altaz",
                    "attrs": {"c1": 180.0, "c2": 30.71},
                }
            }
        ]
    },
    "gal": {
        "groups": [
            {
                "field": {
                    "target_name": "Galactic Centre",
                    "reference_frame": "gal",
                    "attrs": {"c1": 0.0, "c2": 0.0},
                }
            }
        ]
    },
    "special": {
        "groups": [
            {
                "field": {
                    "target_name": "Sun",
                    "reference_frame": "special",
                }
            }
        ]
    },
}


EXPECTED_RECEPTORS = ["SKA001", "SKA036", "SKA077", "SKA100"]


@pytest.mark.batch1
@pytest.mark.SKA_mid
@scenario(
    "../features/test_harness/check_delay_for_ref_frames.feature",
    "Generate valid delay model for <reference_frame> target via TMC Mid",
)
def test_delay_model_for_adr63_ref_frames() -> None:
    """Scenario runner for ADR-63 delay model verification via TMC."""
    pass


@given("a TMC in ON state")
def tmc_in_on_state(
    central_node_mid: CentralNodeWrapperMid, event_recorder: EventRecorder
) -> None:
    """Ensure the TMC (Central Node) is in ON state."""
    central_node_mid.move_to_on()
    event_recorder.subscribe_event(
        central_node_mid.central_node, "telescopeState"
    )
    assert event_recorder.has_change_event_occurred(
        central_node_mid.central_node, "telescopeState", DevState.ON
    )


@given("subarray is in IDLE ObsState")
def subarray_in_idle_obsstate(
    central_node_mid: CentralNodeWrapperMid,
    subarray_node: SubarrayNodeWrapper,
    event_recorder: EventRecorder,
    command_input_factory: JsonFactory,
) -> None:
    """Assign resources so TMC Subarray reaches IDLE."""
    central_node_mid.set_subarray_id("1")
    assign_input_json = prepare_json_args_for_centralnode_commands(
        "assign_resources_mid", command_input_factory
    )
    assign_input = json.loads(assign_input_json)
    assign_input["subarray_id"] = 1
    central_node_mid.store_resources(json.dumps(assign_input))

    event_recorder.subscribe_event(subarray_node.subarray_node, "obsState")
    assert event_recorder.has_change_event_occurred(
        subarray_node.subarray_node, "obsState", ObsState.IDLE
    )


@when(
    parsers.parse(
        "I configure the TMC subarray with a pointing group "
        'using "{reference_frame}" reference frame'
    )
)
def configure_with_adr63_pointing_group(
    subarray_node: SubarrayNodeWrapper,
    command_input_factory: JsonFactory,
    event_recorder: EventRecorder,
    reference_frame: str,
) -> None:
    """Override pointing.groups in the configure_mid template for the requested
    ADR-63 reference frame, invoke Configure via TMC SubarrayNode, and wait
    for READY (and implicit LRC success).
    """
    configure_input_json = prepare_json_args_for_commands(
        "configure_mid", command_input_factory
    )
    config = json.loads(configure_input_json)

    ref_key = reference_frame.lower()
    if ref_key not in ADR63_POINTING_SAMPLES:
        pytest.fail(f"Unsupported reference_frame in test: {reference_frame}")

    config["pointing"] = ADR63_POINTING_SAMPLES[ref_key]

    configure_json_str = json.dumps(config)
    LOGGER.info(
        "Invoking Configure with ADR-63 pointing for ref_frame=%s",
        reference_frame,
    )

    subarray_node.store_configuration_data(configure_json_str)

    event_recorder.subscribe_event(subarray_node.subarray_node, "obsState")
    assert event_recorder.has_change_event_occurred(
        subarray_node.subarray_node, "obsState", ObsState.READY
    )


@then("CSP Subarray Leaf Node generates a valid delayModel for the target")
def csp_leafnode_generates_delaymodel(
    subarray_node: SubarrayNodeWrapper,
) -> None:
    """Verify non-default, structurally valid delayModel with one entry per
    assigned receptor (receptor + xypol_coeffs_ns list + ypol_offset_ns).
    """
    cspsal_node = subarray_node.csp_subarray_leaf_node

    delay_json_dict, generated_time = wait_till_delay_values_are_populated(
        cspsal_node
    )
    LOGGER.info("Delay model generated at %s", generated_time)

    assert (
        delay_json_dict != MID_DELAY_JSON
    ), "delayModel must not be the default/empty JSON after successful "
    "Configure with ADR-63 target"

    receptor_delays = delay_json_dict.get("receptor_delays", [])
    assert len(receptor_delays) == len(EXPECTED_RECEPTORS), (
        f"Expected {len(EXPECTED_RECEPTORS)} receptor delay entries , "
        f"got {len(receptor_delays)}"
    )

    for entry in receptor_delays:
        assert entry.get("receptor") in EXPECTED_RECEPTORS
        xypol = entry.get("xypol_coeffs_ns")
        assert isinstance(xypol, list) and len(xypol) > 0
        assert isinstance(entry.get("ypol_offset_ns"), (int, float))

    LOGGER.info(
        "Verified valid non-default delayModel (%d receptors) "
        "for ADR-63 %s target.",
        len(receptor_delays),
        "ref frame",
    )


@then("I end the observation")
def end_the_observation(
    subarray_node: SubarrayNodeWrapper, event_recorder: EventRecorder
) -> None:
    """Invoke End and wait for IDLE (triggers delay manager stop + reset)."""
    subarray_node.end_observation()
    event_recorder.subscribe_event(subarray_node.subarray_node, "obsState")
    assert event_recorder.has_change_event_occurred(
        subarray_node.subarray_node, "obsState", ObsState.IDLE
    )


@then("CSP Subarray Leaf Node resets the delayModel to default")
def then_csp_leafnode_resets_delaymodel_to_default(
    subarray_node: SubarrayNodeWrapper,
) -> None:
    """CSP Subarray Leaf Node must publish the default empty delayModel."""
    cspsal_node = subarray_node.csp_subarray_leaf_node
    delay_json = json.loads(cspsal_node.read_attribute("delayModel").value)

    assert (
        delay_json == MID_DELAY_JSON
    ), f"Expected default delayModel after End, got {delay_json}"
