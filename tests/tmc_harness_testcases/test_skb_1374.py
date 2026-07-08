"""
This module defines a BDD (Behavior-Driven Development) test scenario
using pytest-bdd to verify the behavior of the Subarray in case track table
generation fails on dish leaf node as mentioned in SKB-1374.
"""
import json
import logging
import time

import pytest
from assertpy import assert_that
from pytest_bdd import given, scenario, then, when
from ska_control_model import ObsState
from ska_ser_logging import configure_logging
from ska_tango_base.commands import ResultCode
from ska_tango_testing.integration import TangoEventTracer, log_events
from ska_tango_testing.mock.placeholders import Anything
from tango import DevState

from tests.resources.test_harness.central_node_mid import CentralNodeWrapperMid
from tests.resources.test_harness.helpers import (
    prepare_json_args_for_centralnode_commands,
    prepare_json_args_for_commands,
)
from tests.resources.test_harness.subarray_node import SubarrayNodeWrapper
from tests.resources.test_harness.utils.common_utils import JsonFactory
from tests.resources.test_support.constant import TIMEOUT

configure_logging(logging.DEBUG)
LOGGER = logging.getLogger(__name__)


@pytest.mark.batch1
@pytest.mark.SKA_mid
@scenario(
    "../features/skb_1374.feature",
    "TMC Subarray moves to FAULT when track table generation fails "
    + "on the dish leaf nodes.",
)
def test_verify_skb_1374():
    """the Subarray in case track table generation fails on the dish
    leaf nodes as mentioned in SKB-1374
    """


@given("a TMC is in IDLE obsState")
def given_a_tmc_in_idle_obs_state(
    central_node_mid: CentralNodeWrapperMid,
    subarray_node: SubarrayNodeWrapper,
    command_input_factory: JsonFactory,
    event_tracer: TangoEventTracer,
):
    """
    This method brings TMC to IDLE ObsState
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
    # Event Subscriptions
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
        }
    )

    # Invoking commands on TMC
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

    assign_input_json = prepare_json_args_for_centralnode_commands(
        "assign_resources_mid", command_input_factory
    )
    _, unique_id = central_node_mid.store_resources(assign_input_json)
    assert_that(event_tracer).described_as(
        'FAILED ASSUMPTION IN "GIVEN" STEP: '
        "'a TMC in EMPTY obsState'"
        "Subarray Node device"
        f"({central_node_mid.subarray_node.dev_name()}) "
        "is expected to be in IDLE obstate",
    ).within_timeout(TIMEOUT).has_change_event_occurred(
        central_node_mid.subarray_node,
        "obsState",
        ObsState.IDLE,
    )
    assert_that(event_tracer).described_as(
        'FAILED ASSUMPTION IN "GIVEN" STEP: '
        "'a TMC in EMPTY obsState'"
        "Subarray Node device"
        f"({central_node_mid.central_node.dev_name()}) "
        "is expected have longRunningCommand as"
        '(unique_id,(ResultCode.OK,"Command Completed"))',
    ).within_timeout(TIMEOUT).has_change_event_occurred(
        central_node_mid.central_node,
        "longRunningCommandResult",
        (unique_id[0], json.dumps((int(ResultCode.OK), "Command Completed"))),
    )


@when("I invoke Configure command on Subarray")
def invoke_configure(
    subarray_node: SubarrayNodeWrapper,
    command_input_factory: JsonFactory,
):
    """Method to call Configure command on Subarray

    Args:
        subarray_node (SubarrayNodeWrapper): Object of subarray
        node wrapper
        command_input_factory (JsonFactory): Factory for creating JSON
        arguments for commands
    """
    pytest.initial_program_track_table_error_val = (
        subarray_node.dish_pointing_device[0].programTrackTableError
    )
    configure_input_json = prepare_json_args_for_commands(
        "configure_mid", command_input_factory
    )
    configure_json = json.loads(configure_input_json)
    configure_json["pointing"]["groups"][0]["field"]["target_name"] = "Spica"
    configure_json["pointing"]["groups"][0]["field"]["attrs"]["c1"] = 201.299
    configure_json["pointing"]["groups"][0]["field"]["attrs"]["c2"] = -11.162
    configure_input_json = json.dumps(configure_json)
    _, pytest.unique_id = subarray_node.subarray_node.Configure(
        json.dumps(configure_json)
    )
    LOGGER.info("Invoked Configure on SubarrayNode")


@then(
    "Subarray moves to obsState FAULT if track table generation fails else "
    + "moves to obsState READY"
)
def check_obs_state_of_subarray(
    event_tracer: TangoEventTracer,
    central_node_mid: CentralNodeWrapperMid,
    subarray_node: SubarrayNodeWrapper,
):
    """Method to check observation state of SubarrayNode after Configure
    command is invoked

    Args:
        event_tracer(TangoEventTracer): object of TangoEventTracer
        used for managing the device events
        subarray_node (SubarrayNodeWrapper): Object of subarray
        node wrapper
    """
    timeout = 10
    count = 0

    # Wait for programTrackTableError
    while count <= timeout:
        current_program_track_table_error_val = (
            subarray_node.dish_pointing_device[0].programTrackTableError
        )
        if (
            current_program_track_table_error_val
            != pytest.initial_program_track_table_error_val
        ):
            break
        time.sleep(1)
        count += 1
    program_track_table_error_val = subarray_node.dish_pointing_device[
        0
    ].programTrackTableError

    if program_track_table_error_val:
        LOGGER.info("Verify Configure command failure")
        # assert tracktable error and SubarrayNode FAULT obsState
        assert_that(event_tracer).described_as(
            'FAILED ASSUMPTION IN "GIVEN" STEP: '
            "'a TMC in CONFIGURING obsState'"
            "Subarray Node device"
            f"({central_node_mid.subarray_node.dev_name()}) "
            "is expected to be in FAULT obstate",
        ).within_timeout(TIMEOUT).has_change_event_occurred(
            central_node_mid.subarray_node,
            "obsState",
            ObsState.FAULT,
        )
        assert_that(event_tracer).described_as(
            'FAILED ASSUMPTION IN "GIVEN" STEP: '
            "'a TMC in CONFIGURING obsState'"
            "Subarray Node device"
            f"({central_node_mid.subarray_node.dev_name()}) "
            "is expected have longRunningCommand as"
            '(unique_id,(ResultCode.OK,"Command Completed"))',
        ).within_timeout(TIMEOUT).has_change_event_occurred(
            central_node_mid.subarray_node,
            "longRunningCommandResult",
            (
                pytest.unique_id[0],
                Anything,
            ),
        )
        assert (
            "not within mechanical limits set to dish"
            in program_track_table_error_val
        )
    else:
        LOGGER.info("Verify Configure command success")
        # assert the successful completion of Configure command
        assert_that(event_tracer).described_as(
            'FAILED ASSUMPTION IN "GIVEN" STEP: '
            "'a TMC in CONGIGURING obsState'"
            "Subarray Node device"
            f"({central_node_mid.subarray_node.dev_name()}) "
            "is expected to be in READY obstate",
        ).within_timeout(TIMEOUT).has_change_event_occurred(
            central_node_mid.subarray_node,
            "obsState",
            ObsState.READY,
        )
        assert_that(event_tracer).described_as(
            'FAILED ASSUMPTION IN "GIVEN" STEP: '
            "'a TMC in CONFIGURING obsState'"
            "Subarray Node device"
            f"({central_node_mid.subarray_node.dev_name()}) "
            "is expected have longRunningCommand as"
            '(unique_id,(ResultCode.OK,"Command Completed"))',
        ).within_timeout(TIMEOUT).has_change_event_occurred(
            central_node_mid.subarray_node,
            "longRunningCommandResult",
            (
                pytest.unique_id[0],
                json.dumps((int(ResultCode.OK), "Command Completed")),
            ),
        )
