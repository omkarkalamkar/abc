import pytest
from assertpy import assert_that
from ska_control_model import ObsState
from tango import DevState

from tests.resources.test_harness.helpers import (
    TIMEOUT,
    check_assigned_resources,
    get_device_simulators,
    prepare_json_args_for_centralnode_commands,
)
from tests.resources.test_support.constant import COMMAND_COMPLETED


class TestMidCentralNodeAssignResources(object):
    @pytest.mark.batch1
    @pytest.mark.SKA_mid
    @pytest.mark.parametrize(
        "input_json_name",
        ["assign_resources_mid"],
    )
    def test_mid_centralnode_assign_resources(
        self,
        input_json_name,
        central_node_mid,
        event_tracer,
        simulator_factory,
        command_input_factory,
    ):
        """
        Test to verify transitions that are triggered by AssignResources and
        ReleaseResource command and followed by a completion transition
        assuming that external subsystems work fine.
        Glossary:
        - "central_node_mid": fixture for a TMC CentralNode Mid under test
        which provides simulated master devices
        - "event_tracer": fixture for TangoEventTracer class
        for validating the subscribing and receiving events.
        - "simulator_factory": fixture for creating simulator devices for
        mid Telescope respectively.
        - "command_input_factory": fixture for JsonFactory class,
        which provides json files for CentralNode
        """

        assign_input_json = prepare_json_args_for_centralnode_commands(
            input_json_name, command_input_factory
        )
        csp_sim, sdp_sim, _, _, _, _ = get_device_simulators(simulator_factory)
        event_tracer.subscribe_event(csp_sim, "obsState")
        event_tracer.subscribe_event(sdp_sim, "obsState")
        event_tracer.subscribe_event(
            central_node_mid.subarray_node, "obsState"
        )
        event_tracer.subscribe_event(
            central_node_mid.central_node, "telescopeState"
        )
        event_tracer.subscribe_event(
            central_node_mid.subarray_node, "assignedResources"
        )
        event_tracer.subscribe_event(
            central_node_mid.central_node, "longRunningCommandResult"
        )
        event_tracer.subscribe_event(
            central_node_mid.central_node, "telescopeState"
        )
        central_node_mid.move_to_on()
        assert_that(event_tracer).described_as(
            "Expected State event for Central Node with DevState ON"
        ).within_timeout(TIMEOUT).has_change_event_occurred(
            central_node_mid.central_node, "telescopeState", DevState.ON
        )
        _, unique_id = central_node_mid.perform_action(
            "AssignResources", assign_input_json
        )
        assert_that(event_tracer).described_as(
            "Expected State event for SDP with ObsState.IDLE"
        ).within_timeout(TIMEOUT).has_change_event_occurred(
            sdp_sim,
            "obsState",
            ObsState.IDLE,
        )
        assert_that(event_tracer).described_as(
            "Expected State event for CSP with ObsState.IDLE"
        ).within_timeout(TIMEOUT).has_change_event_occurred(
            csp_sim,
            "obsState",
            ObsState.IDLE,
        )
        assert_that(event_tracer).described_as(
            "Expected State event for Subarray Node with ObsState.IDLE"
        ).within_timeout(TIMEOUT).has_change_event_occurred(
            central_node_mid.subarray_node,
            "obsState",
            ObsState.IDLE,
        )
        assert_that(event_tracer).described_as(
            "Expected longRunningCommandResult event with AssignResources "
            "success"
        ).within_timeout(TIMEOUT).has_change_event_occurred(
            central_node_mid.central_node,
            "longRunningCommandResult",
            (unique_id[0], COMMAND_COMPLETED),
        )
        assert check_assigned_resources(
            central_node_mid.subarray_node,
            ("SKA001", "SKA036", "SKA063", "SKA100"),
        )
