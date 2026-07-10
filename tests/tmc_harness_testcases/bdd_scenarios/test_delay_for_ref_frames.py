"""Verify delay generation for TLE/Alt-Az/Galactic targets in TMC Mid.

This end-to-end test configures the TMC Mid subarray with an ADR-63
pointing group (`groups[].field.reference_frame`) for each of the
reference frames (icrs, special, tle, altaz, galactic) and verifies
that the CSP Subarray Leaf Node produces a valid delay model for it
and correctly resets the model on End.
"""

import json

import pytest
from assertpy import assert_that
from pytest_bdd import given, parsers, scenario, then, when
from ska_control_model import ObsState
from ska_tango_testing.integration import log_events
from tango import DevState

from tests.conftest import (
    ASSIGNED_RECEPTORS,
    MID_DELAY_JSON,
    POINTING_CONFIGS,
    pick_visible_solar_system_target,
)
from tests.resources.test_harness.central_node_mid import CentralNodeWrapperMid
from tests.resources.test_harness.helpers import (
    prepare_json_args_for_centralnode_commands,
    prepare_json_args_for_commands,
    wait_till_delay_values_are_populated,
)
from tests.resources.test_harness.subarray_node import SubarrayNodeWrapper
from tests.resources.test_harness.utils.common_utils import JsonFactory
from tests.resources.test_support.constant import COMMAND_COMPLETED

TIMEOUT = 50

LOGGER = __import__("logging").getLogger(__name__)


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
    central_node_mid: CentralNodeWrapperMid, event_tracer
) -> None:
    """Ensure the TMC (Central Node) is in ON state."""
    event_tracer.subscribe_event(
        central_node_mid.central_node, "telescopeState"
    )
    event_tracer.subscribe_event(
        central_node_mid.central_node, "longRunningCommandResult"
    )
    event_tracer.subscribe_event(central_node_mid.subarray_node, "obsState")
    event_tracer.subscribe_event(
        central_node_mid.subarray_node, "longRunningCommandResult"
    )

    # Logging setup
    log_events(
        {
            central_node_mid.central_node: [
                "telescopeState",
                "longRunningCommandResult",
            ],
            central_node_mid.subarray_node: [
                "obsState",
                "longRunningCommandResult",
            ],
        }
    )

    central_node_mid.move_to_on()

    assert_that(event_tracer).described_as(
        "FAILED ASSUMPTION AFTER ON COMMAND: "
        f"Central Node device ({central_node_mid.central_node.dev_name()}) "
        "is expected to be in TelescopeState ON",
    ).within_timeout(TIMEOUT).has_change_event_occurred(
        central_node_mid.central_node, "telescopeState", DevState.ON
    )


@given("subarray is in IDLE ObsState")
def subarray_in_idle_obsstate(
    central_node_mid: CentralNodeWrapperMid,
    subarray_node: SubarrayNodeWrapper,
    event_tracer,
    command_input_factory: JsonFactory,
) -> None:
    """Assign resources so TMC Subarray reaches IDLE."""
    central_node_mid.set_subarray_id("1")
    assign_input_json = prepare_json_args_for_centralnode_commands(
        "assign_resources_mid", command_input_factory
    )
    assign_input = json.loads(assign_input_json)
    assign_input["subarray_id"] = 1

    _, unique_id = central_node_mid.store_resources(json.dumps(assign_input))

    assert_that(event_tracer).described_as(
        "FAILED ASSUMPTION AFTER ASSIGNRESOURCES COMMAND: "
        f"Subarray Node device ({subarray_node.subarray_node.dev_name()}) "
        "is expected to be in IDLE obstate",
    ).within_timeout(TIMEOUT).has_change_event_occurred(
        subarray_node.subarray_node, "obsState", ObsState.IDLE
    )

    assert_that(event_tracer).described_as(
        "FAILED ASSUMPTION AFTER ASSIGNRESOURCES COMMAND: "
        f"'the subarray is in IDLE obsState' "
        f"Subarray Node device ({central_node_mid.central_node.dev_name()}) "
        f"is expected have longRunningCommand as ({unique_id[0]},"
        f"{COMMAND_COMPLETED})",
    ).within_timeout(TIMEOUT).has_change_event_occurred(
        central_node_mid.central_node,
        "longRunningCommandResult",
        (unique_id[0], COMMAND_COMPLETED),
    )

    event_tracer.clear_events()


@when(
    parsers.parse(
        "I configure the TMC subarray with a pointing group "
        'using "{reference_frame}" reference frame'
    )
)
def configure_with_adr63_pointing_group(
    subarray_node: SubarrayNodeWrapper,
    command_input_factory: JsonFactory,
    event_tracer,
    reference_frame: str,
) -> None:
    """Override pointing.groups in the configure_mid template for the requested
    ADR-63 reference frame, invoke Configure, and assert both obsState + LRC.
    """
    configure_input_json = prepare_json_args_for_commands(
        "configure_mid", command_input_factory
    )
    config = json.loads(configure_input_json)

    ref_key = reference_frame.lower()
    if ref_key not in POINTING_CONFIGS:
        pytest.fail(f"Unsupported reference_frame in test: {reference_frame}")

    pointing_config = POINTING_CONFIGS[ref_key]

    if ref_key == "special":
        chosen = pick_visible_solar_system_target(ASSIGNED_RECEPTORS)
        pointing_config["groups"][0]["field"]["target_name"] = chosen
        LOGGER.info("Using dynamic special target for test: %s", chosen)

    config["pointing"] = pointing_config
    configure_json_str = json.dumps(config)

    LOGGER.info(
        "Invoking Configure with ADR-63 pointing for ref_frame=%s",
        reference_frame,
    )

    _, unique_id = subarray_node.execute_transition(
        "Configure", configure_json_str
    )

    assert_that(event_tracer).described_as(
        "FAILED ASSUMPTION AFTER CONFIGURE COMMAND: "
        f"Subarray Node device ({subarray_node.subarray_node.dev_name()}) "
        "is expected to be in READY obstate",
    ).within_timeout(TIMEOUT).has_change_event_occurred(
        subarray_node.subarray_node, "obsState", ObsState.READY
    )

    assert_that(event_tracer).described_as(
        "FAILED ASSUMPTION AFTER CONFIGURE COMMAND: "
        f"'the subarray is in READY obsState' "
        f"Subarray Node device ({subarray_node.subarray_node.dev_name()}) "
        f"is expected have longRunningCommand as ({unique_id[0]},"
        f"{COMMAND_COMPLETED})",
    ).within_timeout(TIMEOUT).has_change_event_occurred(
        subarray_node.subarray_node,
        "longRunningCommandResult",
        (unique_id[0], COMMAND_COMPLETED),
    )

    event_tracer.clear_events()


@then("CSP Subarray Leaf Node generates a valid delayModel for the target")
def csp_leafnode_generates_delaymodel(
    subarray_node: SubarrayNodeWrapper,
) -> None:
    """Verify non-default, structurally valid delayModel with one entry per
    assigned receptor.
    """
    cspsal_node = subarray_node.csp_subarray_leaf_node

    delay_json_dict, generated_time = wait_till_delay_values_are_populated(
        cspsal_node
    )
    LOGGER.info("Delay model generated at %s", generated_time)

    assert delay_json_dict != MID_DELAY_JSON, (
        "delayModel must not be the default/empty JSON after successful "
        "Configure with ADR-63 target"
    )
    receptor_delays = delay_json_dict.get("receptor_delays", [])
    assert len(receptor_delays) == len(ASSIGNED_RECEPTORS), (
        f"Expected {len(ASSIGNED_RECEPTORS)} receptor delay entries, "
        f"got {len(receptor_delays)}"
    )

    for entry in receptor_delays:
        assert entry.get("receptor") in ASSIGNED_RECEPTORS
        xypol = entry.get("xypol_coeffs_ns")
        assert isinstance(xypol, list) and len(xypol) > 0
        assert isinstance(entry.get("ypol_offset_ns"), (int, float))

    LOGGER.info(
        "Verified valid non-default delayModel (%d receptors) "
        "for ADR-63 target.",
        len(receptor_delays),
    )


@then("I end the observation")
def end_the_observation(
    subarray_node: SubarrayNodeWrapper, event_tracer
) -> None:
    """Invoke End and wait for IDLE (triggers delay manager stop + reset)."""
    _, unique_id = subarray_node.execute_transition("End")

    assert_that(event_tracer).described_as(
        "FAILED ASSUMPTION AFTER END COMMAND: "
        f"Subarray Node device ({subarray_node.subarray_node.dev_name()}) "
        "is expected to be in IDLE obstate",
    ).within_timeout(TIMEOUT).has_change_event_occurred(
        subarray_node.subarray_node, "obsState", ObsState.IDLE
    )

    assert_that(event_tracer).described_as(
        "FAILED ASSUMPTION AFTER END COMMAND: "
        f"'the subarray is in IDLE obsState' "
        f"Subarray Node device ({subarray_node.subarray_node.dev_name()}) "
        f"is expected have longRunningCommand as ({unique_id[0]},"
        f"{COMMAND_COMPLETED})",
    ).within_timeout(TIMEOUT).has_change_event_occurred(
        subarray_node.subarray_node,
        "longRunningCommandResult",
        (unique_id[0], COMMAND_COMPLETED),
    )

    event_tracer.clear_events()


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
