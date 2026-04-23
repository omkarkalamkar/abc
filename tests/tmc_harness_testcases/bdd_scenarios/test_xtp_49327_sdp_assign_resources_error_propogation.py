"""Test module to verify timeout error propogation from SDP Subarray"""
import json

import pytest
from pytest_bdd import given, scenario, then, when
from ska_tango_testing.mock.placeholders import Anything

from tests.resources.test_harness.central_node_mid import CentralNodeWrapperMid
from tests.resources.test_harness.event_recorder import EventRecorder
from tests.resources.test_harness.helpers import (
    prepare_json_args_for_centralnode_commands,
)
from tests.resources.test_harness.simulator_factory import SimulatorFactory
from tests.resources.test_harness.utils.common_utils import JsonFactory
from tests.resources.test_harness.utils.enums import SimulatorDeviceType
from tests.resources.test_support.constant import (
    COMMAND_NOT_ALLOWED_DEFECT_BEFORE_QUEUING,
    RESET_DEFECT,
    tmc_sdp_subarray_leaf_node,
)


@pytest.mark.batch1
@pytest.mark.SKA_mid
@scenario(
    "../features/test_harness/xtp_49327_sdp_subarray_"
    + "error_propogation.feature",
    "Verify CommandNotAllowed error propogation with defective SDP Subarray",
)
def test_sdp_subarray_assign_resources_error_propagation():
    """
    Test case to verify CommandNotAllowed error propogation
    """


# from conftest.py
# @given("the telescope is in ON state")


@given("SDP subarray is set with command not allowed defect")
def set_sdp_subarray_defective(simulator_factory: SimulatorFactory):
    """A method to set command not allowed defect
    for SDP Subarray

    Args:
        simulator_factory: fixture for SimulatorFactory class,
        which provides simulated subarray and master devices
    """
    pytest.sdp_sim = simulator_factory.get_or_create_simulator_device(
        SimulatorDeviceType.MID_SDP_DEVICE
    )
    # Set SDP subarray defective
    pytest.sdp_sim.SetDefective(
        json.dumps(COMMAND_NOT_ALLOWED_DEFECT_BEFORE_QUEUING)
    )


@when("I issue the AssignResources command from TMC CentralNode")
def invoke_assign_resources(
    central_node_mid: CentralNodeWrapperMid,
    command_input_factory: JsonFactory,
) -> None:
    """
    Invokes AssignResources command
    """
    assign_input_json = prepare_json_args_for_centralnode_commands(
        "assign_resources_mid", command_input_factory
    )
    pytest.command_result = central_node_mid.perform_action(
        "AssignResources", assign_input_json
    )


@then(
    "CommandNotAllowed exception is propagated to TMC CentralNode "
    + "on longRunningCommandResult"
)
def check_timeout_error(
    central_node_mid: CentralNodeWrapperMid, event_recorder: EventRecorder
):
    """A method to check CentralMode.longRunningCommandResult attribute
    change for exception

    Args:
        central_node_mid : A fixture for CentralNodeMid tango device class
        event_recorder: A fixture for EventRecorder class
    """
    event_recorder.subscribe_event(
        central_node_mid.central_node, "longRunningCommandResult"
    )
    assertion_data = event_recorder.has_change_event_occurred(
        central_node_mid.central_node,
        "longRunningCommandResult",
        (pytest.command_result[1][0], Anything),
        lookahead=15,
    )
    exception_message = (
        "Exception occurred on the following devices:"
        + f" {pytest.sdp_sim.dev_name()}:"
        " ska_tmc_simulators.dependencies.exceptions.CommandNotAllowed:"
        " Command is not allowed\n"
    )
    assert (
        exception_message
        in json.loads(assertion_data["attribute_value"][1])[1]
    )

    # Reset SDP subarray defect
    pytest.sdp_sim.SetDefective(RESET_DEFECT)
