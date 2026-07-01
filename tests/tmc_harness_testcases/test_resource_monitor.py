"""
Test case for verifying Resource Monitor updates when SubarrayNode assigned
and released resources change in the system.

This test verifies that the ResourceMonitor device correctly updates its
dishes attribute after resources are assigned and released through the
SubarrayNode
"""

import json

import pytest
from assertpy import assert_that
from pytest_bdd import given, scenario, then, when
from ska_tango_base.control_model import ObsState
from ska_tango_testing.integration import TangoEventTracer, log_events
from tango import DeviceProxy, DevState

from tests.resources.test_harness.central_node_mid import CentralNodeWrapperMid
from tests.resources.test_harness.helpers import (
    prepare_json_args_for_centralnode_commands,
    wait_and_validate_device_attribute_value,
)
from tests.resources.test_harness.utils.common_utils import JsonFactory
from tests.resources.test_support.constant import TIMEOUT, tmc_resource_monitor


@pytest.mark.batch1
@pytest.mark.SKA_mid
@pytest.mark.skip(reason="TC is failing")
@scenario(
    "../features/resource_monitor.feature",
    "Check ResourceMonitor updates after resource assignment and release",
)
def test_resource_monitor_updates():
    """BDD scenario for verifying Resource Monitor updates."""


@given("the telescope is in ON state")
def given_tmc_on(
    event_tracer: TangoEventTracer, central_node_mid: CentralNodeWrapperMid
):
    """
    Ensure that the TMC and ResourceMonitor devices are available and ON.
    """
    resource_monitor = DeviceProxy(tmc_resource_monitor)

    event_tracer.subscribe_event(
        central_node_mid.central_node, "telescopeState"
    )
    event_tracer.subscribe_event(
        central_node_mid.subarray_node, "assignedResources"
    )
    event_tracer.subscribe_event(resource_monitor, "dishes")
    central_node_mid.set_subarray_id("1")
    event_tracer.subscribe_event(central_node_mid.subarray_node, "obsState")
    log_events(
        {
            central_node_mid.central_node: ["telescopeState"],
            central_node_mid.subarray_node: ["obsState", "assignedResources"],
            resource_monitor: ["dishes"],
        }
    )
    central_node_mid.set_subarray_id("2")
    event_tracer.subscribe_event(central_node_mid.subarray_node, "obsState")
    central_node_mid.move_to_on()

    assert_that(event_tracer).described_as(
        "FAILED ASSUMPTION: CentralNode should be ON"
    ).within_timeout(TIMEOUT).has_change_event_occurred(
        central_node_mid.central_node, "telescopeState", DevState.ON
    )

    pytest.resource_monitor = resource_monitor
    event_tracer.clear_events()


@given(
    "the resources are assigned to subarray 1 and subarray 2, and the "
    "subarrays are in the IDLE ObsState"
)
def given_subarray_idle(
    command_input_factory: JsonFactory,
    event_tracer: TangoEventTracer,
    central_node_mid: CentralNodeWrapperMid,
):
    """Verifies subarray in IDLE ObsState."""
    central_node_mid.set_subarray_id("1")
    assign_input_json = prepare_json_args_for_centralnode_commands(
        "assign_resources_mid", command_input_factory
    )
    assign_data1 = json.loads(assign_input_json)
    assign_data1["dish"]["receptor_ids"] = ["SKA001", "SKA036", "SKA500"]

    central_node_mid.store_resources(json.dumps(assign_data1))
    assert_that(event_tracer).described_as(
        "TMC subarray device"
        f"({central_node_mid.subarray_node.dev_name()}) "
        "is expected to be in IDLE obstate",
    ).within_timeout(TIMEOUT).has_change_event_occurred(
        central_node_mid.subarray_node,
        "obsState",
        ObsState.IDLE,
    )
    central_node_mid.set_subarray_id("2")
    assign_data = json.loads(assign_input_json)
    assign_data["subarray_id"] = 2
    assign_data["dish"]["receptor_ids"] = ["SKA077", "SKA100", "SKA999"]
    central_node_mid.perform_action("AssignResources", json.dumps(assign_data))
    assert_that(event_tracer).described_as(
        "TMC subarray device"
        f"({central_node_mid.subarray_node.dev_name()}) "
        "is expected to be in IDLE obstate",
    ).within_timeout(TIMEOUT).has_change_event_occurred(
        central_node_mid.subarray_node,
        "obsState",
        ObsState.IDLE,
    )
    pytest.assign_input_json = assign_input_json
    pytest.assign_sa1 = assign_data1["dish"]["receptor_ids"]
    pytest.assign_sa2 = assign_data["dish"]["receptor_ids"]


@given(
    "the ResourceMonitor dishes attribute should correctly reflect the "
    "resources assigned to both subarrays"
)
def then_verify_resource_monitor_update(event_tracer: TangoEventTracer):
    """
    Verify that ResourceMonitor dishes reflects the assigned resources.
    """
    resource_monitor = pytest.resource_monitor
    # Retrieve stored resources for both subarrays
    assigned_sa1 = pytest.assign_sa1  # ["SKA001", "SKA036","SKA500"]
    assigned_sa2 = pytest.assign_sa2  # ["SKA077", "SKA100","SKA999"]

    expected_dishes_data = {}

    # Subarray 1 → allocation = 1
    for receptor_id in assigned_sa1:
        expected_dishes_data[receptor_id] = {
            "subarray_allocation": 1,
            "availability": True,
        }

    # Subarray 2 → allocation = 2
    for receptor_id in assigned_sa2:
        expected_dishes_data[receptor_id] = {
            "subarray_allocation": 2,
            "availability": True,
        }
    results = json.dumps(expected_dishes_data)
    assert wait_and_validate_device_attribute_value(
        resource_monitor, "dishes", results, is_json=True
    )


@when("all assigned resources are released")
def when_release_all_resources(
    event_tracer: TangoEventTracer,
    central_node_mid: CentralNodeWrapperMid,
    command_input_factory: JsonFactory,
):
    """Invokes release resources on two subarrays."""
    central_node_mid.set_subarray_id("1")
    release_input_json = prepare_json_args_for_centralnode_commands(
        "release_resources_mid", command_input_factory
    )
    _, pytest.unique_id = central_node_mid.perform_action(
        "ReleaseResources", release_input_json
    )
    assert_that(event_tracer).described_as(
        "FAILED ASSUMPTION: Subarray should return to EMPTY obsState after "
        "ReleaseAllResources"
    ).within_timeout(TIMEOUT).has_change_event_occurred(
        central_node_mid.subarray_node, "obsState", ObsState.EMPTY
    )
    central_node_mid.set_subarray_id("2")
    release_data = json.loads(release_input_json)
    release_data["subarray_id"] = 2
    _, pytest.unique_id2 = central_node_mid.perform_action(
        "ReleaseResources", json.dumps(release_data)
    )
    assert_that(event_tracer).described_as(
        "FAILED ASSUMPTION: Subarray should return to EMPTY obsState after "
        "ReleaseAllResources"
    ).within_timeout(TIMEOUT).has_change_event_occurred(
        central_node_mid.subarray_node, "obsState", ObsState.EMPTY
    )


@then(
    "the ResourceMonitor dishes attribute should reflect the updated "
    "state after resource release"
)
def then_verify_resource_monitor_empty(event_tracer: TangoEventTracer):
    """Verify that ResourceMonitor dishes becomes empty after release."""
    resource_monitor = pytest.resource_monitor
    # Retrieve previously assigned dishes for both subarrays
    assigned_sa1 = pytest.assign_sa1  # ["SKA001", "SKA036","SKA500"]
    assigned_sa2 = pytest.assign_sa2  # ["SKA077", "SKA100","SKA999"]
    # Combine all dishes
    all_assigned_dishes = assigned_sa1 + assigned_sa2
    expected_dishes_data = {}
    # After release: allocation = -1 for all dishes
    for receptor_id in all_assigned_dishes:
        expected_dishes_data[receptor_id] = {
            "subarray_allocation": -1,
            "availability": True,
        }
    results = json.dumps(expected_dishes_data)
    assert wait_and_validate_device_attribute_value(
        resource_monitor, "dishes", results, is_json=True
    )
