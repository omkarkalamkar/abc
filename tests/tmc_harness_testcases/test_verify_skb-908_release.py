"""
This module defines a BDD (Behavior-Driven Development) test scenario
using pytest-bdd to verify the behavior of the Telescope Monitoring and
Control (TMC) system to verify the SKB-908.
"""


import json

import pytest
from assertpy import assert_that
from pytest_bdd import given, scenario, then, when
from ska_control_model import ObsState
from ska_tango_base.commands import ResultCode
from ska_tango_testing.integration import TangoEventTracer, log_events
from tango import DevState

from tests.resources.test_harness.central_node_mid import CentralNodeWrapperMid
from tests.resources.test_harness.helpers import (
    prepare_json_args_for_centralnode_commands,
)
from tests.resources.test_harness.simulator_factory import SimulatorFactory
from tests.resources.test_harness.utils.common_utils import JsonFactory
from tests.resources.test_harness.utils.enums import SimulatorDeviceType
from tests.resources.test_support.constant import TIMEOUT


@pytest.mark.batch2
@pytest.mark.SKA_mid
@scenario(
    "../features/skb_908.feature",
    "Verify SKB-908 for release resources flow",
)
def test_verify_skb_908_release():
    """BDD test scenario for verifying SKB-908"""


@given("the telescope is in the ON state")
def given_a_telescope_is_in_on(
    central_node_mid: CentralNodeWrapperMid, event_tracer: TangoEventTracer
):
    """
    This method invokes On command from central node and verifies
    the state of telescope after the invocation.
    Args:
        central_node (CentralNodeWrapperMid): Object of Central node wrapper
        event_tracer(TangoEventTracer): object of TangoEventTracer used for
        managing the device events
    """
    event_tracer.subscribe_event(
        central_node_mid.central_node, "telescopeState"
    )
    event_tracer.subscribe_event(
        central_node_mid.central_node, "longRunningCommandResult"
    )
    central_node_mid.set_subarray_id("1")
    event_tracer.subscribe_event(central_node_mid.subarray_node, "obsState")
    log_events(
        {
            central_node_mid.central_node: [
                "telescopeState",
                "longRunningCommandResult",
            ],
            central_node_mid.subarray_node: ["obsState"],
        }
    )
    central_node_mid.set_subarray_id("2")
    event_tracer.subscribe_event(central_node_mid.subarray_node, "obsState")
    log_events(
        {
            central_node_mid.subarray_node: ["obsState"],
        }
    )
    central_node_mid.move_to_on()
    assert_that(event_tracer).described_as(
        'FAILED ASSUMPTION IN "GIVEN" STEP: '
        "'the telescope is is ON state'"
        "Central Node device"
        f"({central_node_mid.central_node.dev_name()}) "
        "is expected to be in TelescopeState ON",
    ).within_timeout(TIMEOUT).has_change_event_occurred(
        central_node_mid.central_node,
        "telescopeState",
        DevState.ON,
    )


@given("subarray 1 and 2 are in the IDLE ObsState")
def verify_subarrys_in_idle(
    central_node_mid: CentralNodeWrapperMid,
    command_input_factory: JsonFactory,
    event_tracer: TangoEventTracer,
):
    """Verifies subarray in IDLE ObsState."""
    central_node_mid.set_subarray_id("1")
    assign_input_json = prepare_json_args_for_centralnode_commands(
        "assign_resources_mid", command_input_factory
    )
    assign_data1 = json.loads(assign_input_json)
    assign_data1["dish"]["receptor_ids"] = ["SKA001", "SKA036"]
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
    assign_data["dish"]["receptor_ids"] = ["SKA077", "SKA100"]
    assign_data["sdp"]["execution_block"]["eb_id"] = "eb-test-20220917-00000"
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


@when("I release resources from both the subarrays simultaneously")
def central_node_assign_resources(
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
    central_node_mid.set_subarray_id("2")
    release_data = json.loads(release_input_json)
    release_data["subarray_id"] = 2
    _, pytest.unique_id2 = central_node_mid.perform_action(
        "ReleaseResources", json.dumps(release_data)
    )


@then(
    "the TMC central node long running command results"
    " for both subarrays are OK"
)
def verify_result_ok(
    central_node_mid: CentralNodeWrapperMid,
    event_tracer: TangoEventTracer,
):
    """Verifies result code OK"""
    assert_that(event_tracer).described_as(
        "Central Node device"
        f"({central_node_mid.central_node.dev_name()}) "
        "is expected have longRunningCommand as"
        '(unique_id,(ResultCode.OK,"Command Completed"))',
    ).within_timeout(TIMEOUT).has_change_event_occurred(
        central_node_mid.central_node,
        "longRunningCommandResult",
        (
            pytest.unique_id[0],
            json.dumps((int(ResultCode.OK), "Command Completed")),
        ),
    )
    assert_that(event_tracer).described_as(
        "Central Node device"
        f"({central_node_mid.central_node.dev_name()}) "
        "is expected have longRunningCommand as"
        '(unique_id,(ResultCode.OK,"Command Completed"))',
    ).within_timeout(TIMEOUT).has_change_event_occurred(
        central_node_mid.central_node,
        "longRunningCommandResult",
        (
            pytest.unique_id2[0],
            json.dumps((int(ResultCode.OK), "Command Completed")),
        ),
    )


@then("the TMC, CSP, SDP subarray 1 and 2 transition to the EMPTY obsState")
def verify_subarrays_in_idle(
    central_node_mid: CentralNodeWrapperMid,
    event_tracer: TangoEventTracer,
    simulator_factory: SimulatorFactory,
):
    """Method checks the subarray node observation state EMPTY after
    ReleaseResources is invoked on central node."""
    central_node_mid.set_subarray_id("1")
    sdp_sim = simulator_factory.get_or_create_simulator_device(
        SimulatorDeviceType.MID_SDP_DEVICE
    )
    csp_sim = simulator_factory.get_or_create_simulator_device(
        SimulatorDeviceType.MID_CSP_DEVICE
    )
    event_tracer.subscribe_event(csp_sim, "obsState")
    event_tracer.subscribe_event(sdp_sim, "obsState")

    event_tracer.subscribe_event(
        central_node_mid.csp_subarray_leaf_node, "cspSubarrayObsState"
    )
    event_tracer.subscribe_event(
        central_node_mid.sdp_subarray_leaf_node, "sdpSubarrayObsState"
    )
    log_events(
        {
            csp_sim: ["obsState"],
            sdp_sim: ["obsState"],
            central_node_mid.csp_subarray_leaf_node: ["cspSubarrayObsState"],
            central_node_mid.sdp_subarray_leaf_node: ["sdpSubarrayObsState"],
        }
    )
    assert_that(event_tracer).described_as(
        "Subarray Node device"
        f"({central_node_mid.subarray_node.dev_name()}) "
        "is expected to be in EMPTY obstate",
    ).within_timeout(TIMEOUT).has_change_event_occurred(
        central_node_mid.subarray_node,
        "obsState",
        ObsState.EMPTY,
    )
    assert_that(event_tracer).described_as(
        "SDP subarray device"
        f"({sdp_sim.dev_name()}) "
        "is expected to be in EMPTY obstate",
    ).within_timeout(TIMEOUT).has_change_event_occurred(
        sdp_sim,
        "obsState",
        ObsState.EMPTY,
    )
    assert_that(event_tracer).described_as(
        "SDP subarray leaf device"
        f"({central_node_mid.sdp_subarray_leaf_node.dev_name()}) "
        "is expected to be in EMPTY obstate",
    ).within_timeout(TIMEOUT).has_change_event_occurred(
        central_node_mid.sdp_subarray_leaf_node,
        "sdpSubarrayObsState",
        ObsState.EMPTY,
    )
    assert_that(event_tracer).described_as(
        "CSP subarray leaf device"
        f"({central_node_mid.csp_subarray_leaf_node.dev_name()}) "
        "is expected to be in EMPTY obstate",
    ).within_timeout(TIMEOUT).has_change_event_occurred(
        central_node_mid.csp_subarray_leaf_node,
        "cspSubarrayObsState",
        ObsState.EMPTY,
    )
    assert_that(event_tracer).described_as(
        "CSP subarray device"
        f"({csp_sim.dev_name()}) "
        "is expected to be in EMPTY obstate",
    ).within_timeout(TIMEOUT).has_change_event_occurred(
        csp_sim,
        "obsState",
        ObsState.EMPTY,
    )

    central_node_mid.set_subarray_id("2")
    sdp_sim2 = simulator_factory.get_or_create_simulator_device(
        SimulatorDeviceType.MID_SDP_DEVICE2
    )
    csp_sim2 = simulator_factory.get_or_create_simulator_device(
        SimulatorDeviceType.MID_CSP_DEVICE2
    )
    event_tracer.subscribe_event(csp_sim2, "obsState")
    event_tracer.subscribe_event(sdp_sim2, "obsState")

    event_tracer.subscribe_event(
        central_node_mid.csp_subarray_leaf_node, "cspSubarrayObsState"
    )
    event_tracer.subscribe_event(
        central_node_mid.sdp_subarray_leaf_node, "sdpSubarrayObsState"
    )
    log_events(
        {
            csp_sim2: ["obsState"],
            sdp_sim2: ["obsState"],
            central_node_mid.csp_subarray_leaf_node: ["cspSubarrayObsState"],
            central_node_mid.sdp_subarray_leaf_node: ["sdpSubarrayObsState"],
        }
    )
    assert_that(event_tracer).described_as(
        "Subarray Node device"
        f"({central_node_mid.subarray_node.dev_name()}) "
        "is expected to be in EMPTY obstate",
    ).within_timeout(TIMEOUT).has_change_event_occurred(
        central_node_mid.subarray_node,
        "obsState",
        ObsState.EMPTY,
    )
    assert_that(event_tracer).described_as(
        "SDP subarray device"
        f"({sdp_sim2.dev_name()}) "
        "is expected to be in EMPTY obstate",
    ).within_timeout(TIMEOUT).has_change_event_occurred(
        sdp_sim2,
        "obsState",
        ObsState.EMPTY,
    )
    assert_that(event_tracer).described_as(
        "SDP subarray leaf device"
        f"({central_node_mid.sdp_subarray_leaf_node.dev_name()}) "
        "is expected to be in EMPTY obstate",
    ).within_timeout(TIMEOUT).has_change_event_occurred(
        central_node_mid.sdp_subarray_leaf_node,
        "sdpSubarrayObsState",
        ObsState.EMPTY,
    )
    central_node_mid.set_subarray_id("1")
