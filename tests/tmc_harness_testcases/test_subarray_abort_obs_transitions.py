import json
import logging

import pytest
from assertpy import assert_that
from ska_tango_base.control_model import ObsState

from tests.resources.test_harness.subarray_node import TIMEOUT
from tests.resources.test_support.constant import ABORT_COMPLETED
from tests.resources.test_support.enum import PointingState


class TestSubarrayNodeAbortCommandObsStateTransitions(object):
    @pytest.mark.parametrize(
        "source_obs_state",
        [
            "READY",
            "RESOURCING",
            "IDLE",
            "CONFIGURING",
            "SCANNING",
        ],
    )
    @pytest.mark.batch2
    @pytest.mark.SKA_mid
    def test_subarray_obs_transitions_valid_data(
        self,
        subarray_node,
        event_tracer,
        command_input_factory,
        source_obs_state,
    ):
        """
        Test to verify transitions that are triggered by Abort
        command and followed by a completion transition
        that start with a transient state.
        assuming that external subsystems work fine.
        Glossary:
        - "subarray_node": fixture for a TMC SubarrayNode under test
        which provides simulated subarray and master devices
        - "source_obs_state": a TMC SubarrayNode initial allowed obsState,
           required to invoke Abort command
        """

        event_tracer.subscribe_event(subarray_node.subarray_node, "obsState")
        event_tracer.subscribe_event(
            subarray_node.csp_subarray_leaf_node, "cspSubarrayObsState"
        )
        event_tracer.subscribe_event(
            subarray_node.sdp_subarray_leaf_node, "sdpSubarrayObsState"
        )
        for dishln in subarray_node.dish_leaf_node_list:
            event_tracer.subscribe_event(dishln, "pointingState")

        subarray_node.move_to_on()
        assign_input = json.loads(
            command_input_factory.create_assign_resources_configuration(
                "assign_resources_mid"
            )
        )
        assign_input["dish"]["receptor_ids"] = [
            "SKA001",
            "SKA036",
            "SKA077",
            "SKA100",
        ]
        logging.info("assign_input: %s", assign_input)
        subarray_node.force_change_of_obs_state(
            dest_state_name=source_obs_state,
            assign_input_json=json.dumps(assign_input),
        )

        assert_that(event_tracer).described_as(
            "FAILED ASSUMPTION: "
            "Subarray Node device"
            f"({subarray_node.subarray_node.dev_name()}) "
            f"is expected to be in {source_obs_state}",
        ).within_timeout(TIMEOUT).has_change_event_occurred(
            subarray_node.subarray_node,
            "obsState",
            ObsState[source_obs_state],
        )

        assert_that(event_tracer).described_as(
            "FAILED ASSUMPTION: "
            "CSP Subarray Leaf Node device"
            f"({subarray_node.csp_subarray_leaf_node.dev_name()}) "
            f"is expected to be in {source_obs_state}",
        ).within_timeout(TIMEOUT).has_change_event_occurred(
            subarray_node.csp_subarray_leaf_node,
            "cspSubarrayObsState",
            ObsState[source_obs_state],
        )
        assert_that(event_tracer).described_as(
            "FAILED ASSUMPTION: "
            "SDP Subarray Leaf Node device"
            f"({subarray_node.sdp_subarray_leaf_node.dev_name()}) "
            f"is expected to be in {source_obs_state}",
        ).within_timeout(TIMEOUT).has_change_event_occurred(
            subarray_node.sdp_subarray_leaf_node,
            "sdpSubarrayObsState",
            ObsState[source_obs_state],
        )
        if source_obs_state == "CONFIGURING":
            for dishln in subarray_node.dish_leaf_node_list:
                assert_that(event_tracer).described_as(
                    "FAILED ASSUMPTION: "
                    "Dish Leaf Node device"
                    f"({dishln}) "
                    "is expected to be in PointingState.SLEW",
                ).within_timeout(TIMEOUT).has_change_event_occurred(
                    dishln,
                    "pointingState",
                    PointingState.SLEW,
                )

        event_tracer.clear_events()

        event_tracer.subscribe_event(subarray_node.subarray_node, "obsState")
        event_tracer.subscribe_event(
            subarray_node.subarray_node, "longRunningCommandResult"
        )
        event_tracer.subscribe_event(subarray_node.subarray_node, "lrcQueue")
        event_tracer.subscribe_event(
            subarray_node.subarray_node, "longRunningCommandInProgress"
        )

        event_tracer.subscribe_event(
            subarray_node.csp_subarray_leaf_node, "cspSubarrayObsState"
        )
        event_tracer.subscribe_event(
            subarray_node.sdp_subarray_leaf_node, "sdpSubarrayObsState"
        )

        _, unique_id = subarray_node.execute_transition("Abort", argin=None)

        assert_that(event_tracer).described_as(
            "FAILED ASSUMPTION: "
            "Subarray Node device"
            f"({subarray_node.subarray_node.dev_name()}) "
            "is expected to be in ObsState.ABORTING",
        ).within_timeout(TIMEOUT).has_change_event_occurred(
            subarray_node.subarray_node,
            "obsState",
            ObsState.ABORTING,
        )

        assert_that(event_tracer).described_as(
            "FAILED ASSUMPTION: "
            "SDP Subarray Leaf Node device"
            f"({subarray_node.sdp_subarray_leaf_node.dev_name()}) "
            "is expected to be in ObsState.ABORTED",
        ).within_timeout(TIMEOUT).has_change_event_occurred(
            subarray_node.sdp_subarray_leaf_node,
            "sdpSubarrayObsState",
            ObsState.ABORTED,
        )
        assert_that(event_tracer).described_as(
            "FAILED ASSUMPTION: "
            "CSP Subarray Leaf Node device"
            f"({subarray_node.csp_subarray_leaf_node.dev_name()}) "
            "is expected to be in ObsState.ABORTED",
        ).within_timeout(TIMEOUT).has_change_event_occurred(
            subarray_node.csp_subarray_leaf_node,
            "cspSubarrayObsState",
            ObsState.ABORTED,
        )
        assert_that(event_tracer).described_as(
            "FAILED ASSUMPTION AFTER ABORT COMMAND: "
            "Subarray Node device"
            f"({subarray_node.subarray_node.dev_name()}) "
            "is expected have longRunningCommand as"
            '(unique_id,(ResultCode.OK,"Abort command completed"))',
        ).within_timeout(TIMEOUT).has_change_event_occurred(
            subarray_node.subarray_node,
            "longRunningCommandResult",
            (unique_id[0], ABORT_COMPLETED),
        )

        # After abort command, the longRunningCommandInProgress and
        # lrcQueue attributes are expected to be empty
        assert_that(
            subarray_node.subarray_node.longRunningCommandInProgress
        ).described_as(
            'FAILED ASSUMPTION IN "THEN STEP: '
            '"the Subarray transitions to ABORTED obsState" '
            "longRunningCommandInProgress is expected to be empty"
        ).is_empty()

        assert_that(subarray_node.subarray_node.lrcQueue).described_as(
            'FAILED ASSUMPTION IN "THEN STEP: '
            '"the Subarray transitions to ABORTED obsState" '
            "lrcQueue is expected to be empty"
        ).is_empty()

        assert_that(event_tracer).described_as(
            "FAILED ASSUMPTION AFTER ABORT COMMAND: "
            "Subarray Node device"
            f"({subarray_node.subarray_node.dev_name()}) "
            "is expected to be in ObsState.ABORTED",
        ).within_timeout(TIMEOUT).has_change_event_occurred(
            subarray_node.subarray_node,
            "obsState",
            ObsState.ABORTED,
        )
        event_tracer.clear_events()
