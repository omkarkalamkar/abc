"""Implement negative scenario test cases for subarray
"""
import json

import pytest
from ska_tango_testing.mock.placeholders import Anything

from tests.resources.test_harness.helpers import prepare_json_args_for_commands
from tests.resources.test_harness.utils.enums import SimulatorDeviceType
from tests.resources.test_support.constant import (
    INTERMEDIATE_STATE_DEFECT,
    RESET_DEFECT,
    tmc_csp_subarray_leaf_node,
)


class TestSubarrayNodeNegative(object):
    @pytest.mark.batch2
    @pytest.mark.SKA_mid
    def test_subarray_assign_csp_unresponsive(
        self,
        subarray_node,
        command_input_factory,
        simulator_factory,
        event_recorder,
    ):
        input_json = prepare_json_args_for_commands(
            "assign_resources_mid", command_input_factory
        )
        csp_sim = simulator_factory.get_or_create_simulator_device(
            SimulatorDeviceType.MID_CSP_DEVICE
        )
        # Subscribe for long-running command result attribute
        # so that error message from subarray can be validated
        event_recorder.subscribe_event(
            subarray_node.subarray_node, "longRunningCommandResult"
        )

        subarray_node.move_to_on()

        subarray_node.force_change_of_obs_state("EMPTY")

        # Set csp defective and execute configure command
        csp_sim.SetDefective(json.dumps(INTERMEDIATE_STATE_DEFECT))

        pytest.command_result = subarray_node.execute_transition(
            "AssignResources", argin=input_json
        )

        assertion_data = event_recorder.has_change_event_occurred(
            subarray_node.subarray_node,
            "longRunningCommandResult",
            (pytest.command_result[1][0], Anything),
            lookahead=15,
        )
        exception_message = (
            "Exception occurred on the following devices: "
            f"{tmc_csp_subarray_leaf_node}: "
        )
        assert (
            exception_message
            in json.loads(assertion_data["attribute_value"][1])[1]
        )

        csp_sim.SetDefective(RESET_DEFECT)
