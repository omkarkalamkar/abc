"""
This module defines a test scenario
to verify the behavior of the Telescope Monitoring and
Control (TMC) subarray observation with dish 500,999.
"""


import json

import pytest
from assertpy import assert_that
from ska_control_model import ObsState
from ska_tango_base.commands import ResultCode
from ska_tango_testing.integration import TangoEventTracer, log_events
from tango import DevState

from tests.resources.test_harness.central_node_mid import CentralNodeWrapperMid
from tests.resources.test_harness.helpers import (
    prepare_json_args_for_centralnode_commands,
    prepare_json_args_for_commands,
)
from tests.resources.test_harness.subarray_node import SubarrayNodeWrapper
from tests.resources.test_harness.utils.common_utils import JsonFactory
from tests.resources.test_harness.utils.enums import DishMode, PointingState
from tests.resources.test_support.constant import TIMEOUT


def _on(
    central_node_mid: CentralNodeWrapperMid, event_tracer: TangoEventTracer
):
    """Invoke telescopeOn command"""
    central_node_mid.move_to_on()
    assert_that(event_tracer).described_as(
        "Central Node device"
        f"({central_node_mid.central_node.dev_name()}) "
        "is expected to be in TelescopeState ON",
    ).within_timeout(TIMEOUT).has_change_event_occurred(
        central_node_mid.central_node,
        "telescopeState",
        DevState.ON,
    )
    assert_that(event_tracer).described_as(
        "FAILED UNEXPECTED INITIAL OBSSTATE: "
        "Subarray Node device"
        f"({central_node_mid.subarray_node.dev_name()}) "
        "is expected to be in EMPTY obstate",
    ).within_timeout(TIMEOUT).has_change_event_occurred(
        central_node_mid.subarray_node,
        "obsState",
        ObsState.EMPTY,
    )


def _assign_resources(
    central_node_mid: CentralNodeWrapperMid,
    event_tracer: TangoEventTracer,
    command_input_factory: JsonFactory,
):
    """Invoke Assign Resources command"""
    assign_input_json = prepare_json_args_for_centralnode_commands(
        "assign_resources_mid_500_999", command_input_factory
    )
    pytest.assign_json = json.loads(assign_input_json)
    _, unique_id = central_node_mid.store_resources(assign_input_json)
    assert_that(event_tracer).described_as(
        "Subarray Node device"
        f"({central_node_mid.subarray_node.dev_name()}) "
        "is expected to be in IDLE obstate",
    ).within_timeout(TIMEOUT).has_change_event_occurred(
        central_node_mid.subarray_node,
        "obsState",
        ObsState.IDLE,
    )
    assert_that(event_tracer).described_as(
        "Subarray Node device"
        f"({central_node_mid.central_node.dev_name()}) "
        "is expected have longRunningCommand as"
        '(unique_id,(ResultCode.OK,"Command Completed"))',
    ).within_timeout(TIMEOUT).has_change_event_occurred(
        central_node_mid.central_node,
        "longRunningCommandResult",
        (unique_id[0], json.dumps((int(ResultCode.OK), "Command Completed"))),
    )


def _configure_resources(
    central_node_mid: CentralNodeWrapperMid,
    subarray_node: SubarrayNodeWrapper,
    event_tracer: TangoEventTracer,
    command_input_factory: JsonFactory,
):
    """Invoke Configure command."""

    configure_input_json = prepare_json_args_for_commands(
        "configure_mid", command_input_factory
    )
    _, unique_id = subarray_node.execute_transition(
        "Configure", configure_input_json
    )

    assert_that(event_tracer).described_as(
        "Subarray Node device"
        f"({central_node_mid.subarray_node.dev_name()}) "
        "is expected to be in READY obstate",
    ).within_timeout(TIMEOUT).has_change_event_occurred(
        central_node_mid.dish_leaf_node_dict["SKA500"],
        "dishMode",
        DishMode.OPERATE,
    )
    assert_that(event_tracer).described_as(
        "Subarray Node device"
        f"({central_node_mid.subarray_node.dev_name()}) "
        "is expected to be in READY obstate",
    ).within_timeout(TIMEOUT).has_change_event_occurred(
        central_node_mid.dish_leaf_node_dict["SKA500"],
        "pointingState",
        PointingState.TRACK,
    )
    assert_that(event_tracer).described_as(
        "Subarray Node device"
        f"({central_node_mid.subarray_node.dev_name()}) "
        "is expected to be in READY obstate",
    ).within_timeout(TIMEOUT).has_change_event_occurred(
        central_node_mid.dish_leaf_node_dict["SKA500"],
        "dishMode",
        DishMode.OPERATE,
    )
    assert_that(event_tracer).described_as(
        "Subarray Node device"
        f"({central_node_mid.subarray_node.dev_name()}) "
        "is expected to be in READY obstate",
    ).within_timeout(TIMEOUT).has_change_event_occurred(
        central_node_mid.dish_leaf_node_dict["SKA500"],
        "pointingState",
        PointingState.TRACK,
    )
    assert_that(event_tracer).described_as(
        "Subarray Node device"
        f"({central_node_mid.subarray_node.dev_name()}) "
        "is expected to be in READY obstate",
    ).within_timeout(TIMEOUT).has_change_event_occurred(
        central_node_mid.subarray_node,
        "obsState",
        ObsState.READY,
    )
    assert_that(event_tracer).described_as(
        "Subarray Node device"
        f"({central_node_mid.subarray_node.dev_name()}) "
        "is expected have longRunningCommand as"
        '(unique_id,(ResultCode.OK,"Command Completed"))',
    ).within_timeout(TIMEOUT).has_change_event_occurred(
        central_node_mid.subarray_node,
        "longRunningCommandResult",
        (unique_id[0], json.dumps((int(ResultCode.OK), "Command Completed"))),
    )


def _scan(
    central_node_mid: CentralNodeWrapperMid,
    subarray_node: SubarrayNodeWrapper,
    event_tracer: TangoEventTracer,
    command_input_factory: JsonFactory,
):
    """Invoke Scan command."""

    scan_input_json = prepare_json_args_for_commands(
        "scan_mid", command_input_factory
    )
    _, unique_id = subarray_node.execute_transition("Scan", scan_input_json)
    assert_that(event_tracer).described_as(
        "Subarray Node device"
        f"({central_node_mid.subarray_node.dev_name()}) "
        "is expected to be in SCANNING obstate",
    ).within_timeout(TIMEOUT).has_change_event_occurred(
        central_node_mid.subarray_node,
        "obsState",
        ObsState.SCANNING,
    )
    assert_that(event_tracer).described_as(
        "Csp Subarray Node device"
        f"({subarray_node.csp_subarray_leaf_node.dev_name()}) "
        "is expected to be in SCANNING obstate",
    ).within_timeout(TIMEOUT).has_change_event_occurred(
        subarray_node.csp_subarray_leaf_node,
        "cspSubarrayObsState",
        ObsState.SCANNING,
    )
    assert_that(event_tracer).described_as(
        "Subarray Node device"
        f"({subarray_node.sdp_subarray_leaf_node.dev_name()}) "
        "is expected to be in SCANNING obstate",
    ).within_timeout(TIMEOUT).has_change_event_occurred(
        subarray_node.sdp_subarray_leaf_node,
        "sdpSubarrayObsState",
        ObsState.SCANNING,
    )
    assert_that(event_tracer).described_as(
        "Subarray Node device"
        f"({central_node_mid.subarray_node.dev_name()}) "
        "is expected have longRunningCommand as"
        '(unique_id,(ResultCode.OK,"Command Completed"))',
    ).within_timeout(TIMEOUT).has_change_event_occurred(
        central_node_mid.subarray_node,
        "longRunningCommandResult",
        (unique_id[0], json.dumps((int(ResultCode.OK), "Command Completed"))),
    )


def _end_scan(
    central_node_mid: CentralNodeWrapperMid,
    subarray_node: SubarrayNodeWrapper,
    event_tracer: TangoEventTracer,
):
    """Invoke EndScan command."""

    _, unique_id = subarray_node.remove_scan_data()
    assert_that(event_tracer).described_as(
        "Subarray Node device"
        f"({central_node_mid.subarray_node.dev_name()}) "
        "is expected to be in READY obstate",
    ).within_timeout(TIMEOUT).has_change_event_occurred(
        central_node_mid.subarray_node,
        "obsState",
        ObsState.READY,
    )
    assert_that(event_tracer).described_as(
        "Subarray Node device"
        f"({central_node_mid.subarray_node.dev_name()}) "
        "is expected have longRunningCommand as"
        '(unique_id,(ResultCode.OK,"Command Completed"))',
    ).within_timeout(TIMEOUT).has_change_event_occurred(
        central_node_mid.subarray_node,
        "longRunningCommandResult",
        (unique_id[0], json.dumps((int(ResultCode.OK), "Command Completed"))),
    )


def _end(
    central_node_mid: CentralNodeWrapperMid,
    subarray_node: SubarrayNodeWrapper,
    event_tracer: TangoEventTracer,
):
    """Invoke End command."""

    _, unique_id = subarray_node.end_observation()
    assert_that(event_tracer).described_as(
        "Subarray Node device"
        f"({central_node_mid.subarray_node.dev_name()}) "
        "is expected to be in IDLE obstate",
    ).within_timeout(TIMEOUT).has_change_event_occurred(
        central_node_mid.subarray_node,
        "obsState",
        ObsState.IDLE,
    )
    assert_that(event_tracer).described_as(
        "Subarray Node device"
        f"({central_node_mid.subarray_node.dev_name()}) "
        "is expected have longRunningCommand as"
        '(unique_id,(ResultCode.OK,"Command Completed"))',
    ).within_timeout(TIMEOUT).has_change_event_occurred(
        central_node_mid.subarray_node,
        "longRunningCommandResult",
        (unique_id[0], json.dumps((int(ResultCode.OK), "Command Completed"))),
    )


def _release_resources(
    central_node_mid: CentralNodeWrapperMid,
    event_tracer: TangoEventTracer,
    command_input_factory: JsonFactory,
):
    """Invoke ReleaseResources command."""

    release_input_json = prepare_json_args_for_centralnode_commands(
        "release_resources_mid", command_input_factory
    )
    _, unique_id = central_node_mid.invoke_release_resources(
        release_input_json
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
        "Central Node device"
        f"({central_node_mid.central_node.dev_name()}) "
        "is expected have longRunningCommand as"
        '(unique_id,(ResultCode.OK,"Command Completed"))',
    ).within_timeout(TIMEOUT).has_change_event_occurred(
        central_node_mid.central_node,
        "longRunningCommandResult",
        (unique_id[0], json.dumps((int(ResultCode.OK), "Command Completed"))),
    )


def _check_receptors_in_delays(subarray_node: SubarrayNodeWrapper):
    receptors = pytest.assign_json["dish"]["receptor_ids"]
    delays = json.loads(subarray_node.csp_subarray_leaf_node.delayModel)
    receptors_delays = delays["receptor_delays"]
    receptors_in_delay = [data["receptor"] for data in receptors_delays]
    for receptor in receptors:
        assert receptor in receptors_in_delay


def _tmc_setup(
    central_node_mid: CentralNodeWrapperMid,
    subarray_node: SubarrayNodeWrapper,
    event_tracer: TangoEventTracer,
):
    event_tracer.subscribe_event(
        central_node_mid.central_node, "telescopeState"
    )
    event_tracer.subscribe_event(
        central_node_mid.central_node, "longRunningCommandResult"
    )
    event_tracer.subscribe_event(
        subarray_node.subarray_node, "longRunningCommandResult"
    )
    event_tracer.subscribe_event(
        subarray_node.csp_subarray_leaf_node, "longRunningCommandResult"
    )
    event_tracer.subscribe_event(central_node_mid.subarray_node, "obsState")
    event_tracer.subscribe_event(
        subarray_node.csp_subarray_leaf_node, "cspSubarrayObsState"
    )
    event_tracer.subscribe_event(
        subarray_node.sdp_subarray_leaf_node, "sdpSubarrayObsState"
    )
    event_tracer.subscribe_event(
        central_node_mid.dish_leaf_node_dict["SKA500"], "DishMode"
    )
    event_tracer.subscribe_event(
        central_node_mid.dish_leaf_node_dict["SKA500"], "PointingState"
    )
    event_tracer.subscribe_event(
        central_node_mid.dish_leaf_node_dict["SKA999"], "DishMode"
    )
    event_tracer.subscribe_event(
        central_node_mid.dish_leaf_node_dict["SKA999"], "PointingState"
    )
    # Logging events
    log_events(
        {
            central_node_mid.central_node: [
                "telescopeState",
                "longRunningCommandResult",
            ],
            central_node_mid.subarray_node: [
                "longRunningCommandResult",
                "obsState",
            ],
            subarray_node.csp_subarray_leaf_node: ["cspSubarrayObsState"],
            subarray_node.sdp_subarray_leaf_node: ["sdpSubarrayObsState"],
            central_node_mid.dish_leaf_node_dict["SKA500"]: [
                "DishMode",
                "pointingState",
            ],
            central_node_mid.dish_leaf_node_dict["SKA999"]: [
                "DishMode",
                "pointingState",
            ],
        }
    )


@pytest.mark.batch1
@pytest.mark.SKA_mid
def test_verify_observation_500_999_dishes(
    central_node_mid: CentralNodeWrapperMid,
    subarray_node: SubarrayNodeWrapper,
    command_input_factory: JsonFactory,
    event_tracer: TangoEventTracer,
):
    """Test to verify TMC SubarrayNode observation flow with SKA500,
        SKA900 dishes
    Args:
        central_node_mid (CentralNodeWrapperMid): Object of Central node
            wrapper
        subarray_node (SubarrayNodeWrapper): Object of subarray
        node wrapper
        command_input_factory (JsonFactory): object of TangoEventTracer
        used for
        event_tracer(TangoEventTracer): object of TangoEventTracer used for
        managing the device events
    """
    _tmc_setup(central_node_mid, subarray_node, event_tracer)

    _on(central_node_mid, event_tracer)

    _assign_resources(central_node_mid, event_tracer, command_input_factory)

    _configure_resources(
        central_node_mid, subarray_node, event_tracer, command_input_factory
    )
    _check_receptors_in_delays(subarray_node)

    _scan(central_node_mid, subarray_node, event_tracer, command_input_factory)

    _end_scan(central_node_mid, subarray_node, event_tracer)

    _end(central_node_mid, subarray_node, event_tracer)

    _release_resources(central_node_mid, event_tracer, command_input_factory)

    event_tracer.clear_events()
