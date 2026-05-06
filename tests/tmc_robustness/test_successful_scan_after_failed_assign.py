import json

import pytest
from assertpy import assert_that
from pytest_bdd import given, parsers, scenario, then, when
from ska_tango_base.control_model import ObsState
from ska_tango_testing.integration import TangoEventTracer, log_events
from tango import DevState

from tests.conftest import LOGGER
from tests.resources.test_harness.central_node_mid import CentralNodeWrapperMid
from tests.resources.test_harness.helpers import (
    check_for_device_command_event_tracer,
    prepare_json_args_for_centralnode_commands,
    prepare_json_args_for_commands,
)
from tests.resources.test_harness.subarray_node import SubarrayNodeWrapper
from tests.resources.test_harness.utils.common_utils import JsonFactory
from tests.resources.test_support.common_utils.result_code import ResultCode
from tests.resources.test_support.constant import COMMAND_COMPLETED
from tests.resources.test_support.enum import DishMode


@pytest.mark.batch2
@pytest.mark.SKA_mid
@scenario(
    "../features/successful_scan_after_failed_assigned.feature",
    "Successfully execute a scan after a failed attempt to assign resources",
)
def test_assign_resource_with_invalid_json():
    """
    Test AssignResources command with input as invalid json.

    """


@given(
    parsers.parse(
        "a subarray {subarray_id} with resources {resources_list} in obsState EMPTY"  # noqa: E501
    )
)
def given_tmc(
    event_tracer: TangoEventTracer,
    central_node_mid: CentralNodeWrapperMid,
    subarray_node: SubarrayNodeWrapper,
):
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
    for dishln in subarray_node.dish_leaf_node_list:
        event_tracer.subscribe_event(dishln, "dishMode")
        event_tracer.subscribe_event(dishln, "longRunningCommandResult")
        log_events({dishln: ["dishMode", "longRunningCommandResult"]})

    central_node_mid.move_to_on()
    log_events(
        {
            central_node_mid.central_node: [
                "telescopeState",
                "longRunningCommandResult",
            ],
            central_node_mid.subarray_node: ["obsState"],
        }
    )
    for dishln in subarray_node.dish_leaf_node_list:
        assert_that(event_tracer).described_as(
            'FAILED ASSUMPTION IN "GIVEN" STEP: '
            "'the TMC is On'"
            "TMC Subarray device"
            f"({dishln.dev_name()}) "
            "is expected to be in STANDBY_LP dishMode",
        ).within_timeout(100).has_change_event_occurred(
            dishln,
            "dishMode",
            DishMode.STANDBY_FP,
        )

    assert_that(event_tracer).described_as(
        'FAILED ASSUMPTION IN "GIVEN" STEP: '
        "'the TMC is On'"
        "TMC Central Node device"
        f"({central_node_mid.central_node.dev_name()}) "
        "is expected to be in ON telescope state",
    ).within_timeout(150).has_change_event_occurred(
        central_node_mid.central_node,
        "telescopeState",
        DevState.ON,
    )

    assert_that(event_tracer).described_as(
        'FAILED ASSUMPTION IN "GIVEN" STEP: '
        "'the TMC is On'"
        "TMC Subarray device"
        f"({central_node_mid.subarray_node.dev_name()}) "
        "is expected to be in EMPTY obstate",
    ).within_timeout(100).has_change_event_occurred(
        central_node_mid.subarray_node,
        "obsState",
        ObsState.EMPTY,
    )

    event_tracer.clear_events()


@when(
    parsers.parse(
        "I issue the command AssignResources passing an invalid JSON script to the subarray {subarray_id}"  # noqa: E501
    )
)
def invoke_assign_resources_one(
    command_input_factory: JsonFactory,
    event_tracer: TangoEventTracer,
    central_node_mid: CentralNodeWrapperMid,
):
    assign_input_json = prepare_json_args_for_centralnode_commands(
        "assign_resources_mid", command_input_factory
    )
    assign_json = json.loads(assign_input_json)
    assign_json["sdp"]["processing_blocks"][0].pop("pb_id", None)
    # doesn't raise error
    # Invoke AssignResources() Command on TMC
    LOGGER.info("Invoking AssignResources command on TMC CentralNode")
    pytest.command_result = central_node_mid.perform_action(
        "AssignResources", json.dumps(assign_json)
    )


@then(parsers.parse("the subarray {subarray_id} returns an error message"))
def invalid_command_rejection():
    assert "JSON validation error" in pytest.command_result[1][0]
    assert pytest.command_result[0][0] == ResultCode.REJECTED


@then(parsers.parse("the subarray {subarray_id} remains in obsState EMPTY"))
def tmc_status(central_node_mid: CentralNodeWrapperMid):
    assert central_node_mid.subarray_node.obsState == ObsState.EMPTY


@when("I issue the command AssignResources passing a correct JSON script")
def tmc_accepts_command_with_valid_json(
    command_input_factory: JsonFactory, central_node_mid: CentralNodeWrapperMid
):
    assign_input_json = prepare_json_args_for_centralnode_commands(
        "assign_resources_mid", command_input_factory
    )
    _, pytest.unique_id = central_node_mid.store_resources(assign_input_json)


@then("the subarray transitions to obsState IDLE")
def tmc_status_idle(
    event_tracer: TangoEventTracer, central_node_mid: CentralNodeWrapperMid
):
    assert_that(event_tracer).described_as(
        'FAILED ASSUMPTION IN "GIVEN" STEP: '
        "'the subarray must be in the IDLE obsState'"
        "TMC Subarray device"
        f"({central_node_mid.subarray_node.dev_name()}) "
        "is expected to be in IDLE obstate",
    ).within_timeout(60).has_change_event_occurred(
        central_node_mid.subarray_node,
        "obsState",
        ObsState.IDLE,
    )

    assert_that(event_tracer).described_as(
        'FAILED ASSUMPTION IN "GIVEN" STEP: '
        "'the subarray is in IDLE obsState'"
        "TMC Central Node device"
        f"({central_node_mid.central_node.dev_name()}) "
        "is expected have longRunningCommand as"
        '(unique_id,(ResultCode.OK,"Command Completed"))',
    ).within_timeout(60).has_change_event_occurred(
        central_node_mid.central_node,
        "longRunningCommandResult",
        (pytest.unique_id[0], COMMAND_COMPLETED),
    )


@when("I issue the command Configure passing a correct JSON script")
def tmc_accepts_configure_command_with_valid_json(
    command_input_factory: JsonFactory,
    event_tracer: TangoEventTracer,
    subarray_node: SubarrayNodeWrapper,
):
    configure_input_json = prepare_json_args_for_commands(
        "configure_mid", command_input_factory
    )
    configure_input_json = json.loads(configure_input_json)
    configure_input_json["tmc"]["scan_duration"] = 5.0

    _, unique_id = subarray_node.execute_transition(
        "Configure", json.dumps(configure_input_json)
    )
    assert_that(event_tracer).described_as(
        'FAILED ASSUMPTION IN "WHEN" STEP: '
        "TMC Subarray Node device"
        f"({subarray_node.subarray_node.dev_name()}) "
        "is expected have longRunningCommand as"
        '(unique_id,(ResultCode.OK,"Command Completed"))',
    ).within_timeout(100).has_change_event_occurred(
        subarray_node.subarray_node,
        "longRunningCommandResult",
        (unique_id[0], COMMAND_COMPLETED),
    )


@then("the subarray transitions to obsState READY")
def tmc_status_ready(
    event_tracer: TangoEventTracer,
    subarray_node: SubarrayNodeWrapper,
):
    assert_that(event_tracer).described_as(
        'FAILED ASSUMPTION IN "GIVEN" STEP: '
        "'the subarray must be in the READY obsState'"
        "TMC Subarray device"
        f"({subarray_node.subarray_node.dev_name()}) "
        "is expected to be in READY obstate",
    ).within_timeout(60).has_change_event_occurred(
        subarray_node.subarray_node,
        "obsState",
        ObsState.READY,
    )
    event_tracer.clear_events()


@when("I issue the command Scan")
def tmc_accepts_scan_command(
    command_input_factory: JsonFactory,
    event_tracer: TangoEventTracer,
    subarray_node: SubarrayNodeWrapper,
):
    scan_input_json = prepare_json_args_for_commands(
        "scan_mid", command_input_factory
    )
    subarray_node.store_scan_data(scan_input_json)


@then("the subarray transitions to obsState SCANNING")
def tmc_status_scanning(event_tracer, subarray_node):
    csp_subarray = subarray_node.subarray_devices["csp_subarray"]
    sdp_subarray = subarray_node.subarray_devices["sdp_subarray"]
    event_tracer.subscribe_event(csp_subarray, "obsState")
    event_tracer.subscribe_event(sdp_subarray, "obsState")
    assert_that(event_tracer).described_as(
        'FAILED ASSUMPTION IN "THEN" STEP: '
        "'the subarray transitions to obsState SCANNING'"
        "TMC Subarray device"
        f"({csp_subarray.dev_name()}) "
        "is expected to be in SCANNING obstate",
    ).within_timeout(60).has_change_event_occurred(
        csp_subarray,
        "obsState",
        ObsState.SCANNING,
    )
    assert_that(event_tracer).described_as(
        'FAILED ASSUMPTION IN "THEN" STEP: '
        "'the subarray transitions to obsState SCANNING'"
        "TMC Subarray device"
        f"({sdp_subarray.dev_name()}) "
        "is expected to be in SCANNING obstate",
    ).within_timeout(60).has_change_event_occurred(
        sdp_subarray,
        "obsState",
        ObsState.SCANNING,
    )
    assert_that(event_tracer).described_as(
        'FAILED ASSUMPTION IN "THEN" STEP: '
        "'the subarray transitions to obsState SCANNING'"
        "TMC Subarray device"
        f"({subarray_node.subarray_node.dev_name()}) "
        "is expected to be in SCANNING obstate",
    ).within_timeout(60).has_change_event_occurred(
        subarray_node.subarray_node,
        "obsState",
        ObsState.SCANNING,
    )
    for dishln in subarray_node.dish_leaf_node_list:
        assert check_for_device_command_event_tracer(
            dishln,
            "longRunningCommandResult",
            COMMAND_COMPLETED,
            event_tracer,
            "Scan",
        )

    event_tracer.clear_events()


@when("I issue the command EndScan")
def tmc_accepts_endscan_command(
    subarray_node: SubarrayNodeWrapper,
):
    subarray_node.remove_scan_data()


# @then("the subarray transitions to obsState READY")


@then("implements the teardown")
def teardown_the_tmc(
    central_node_mid: CentralNodeWrapperMid,
    subarray_node: SubarrayNodeWrapper,
):
    """Tears down the system after test run"""
    subarray_node.tear_down()
    central_node_mid.tear_down()


@pytest.mark.batch2
@pytest.mark.SKA_mid
@scenario(
    "../features/successful_scan_after_failed_assigned.feature",
    "Successfully execute a scan after a successive failed attempt to assign resources",  # noqa: E501
)
def test_assign_resource_after_successive_assign_failure():
    """
    Test successful Scan after after invoking AssignResource command with
    different invalid json.

    """


@when(
    parsers.parse(
        "I issue the command AssignResources passing an invalid JSON script2 to the subarray {subarray_id}"  # noqa: E501
    )
)
def send_assignresource_with_invalid_json2(
    command_input_factory: JsonFactory,
    event_tracer: TangoEventTracer,
    central_node_mid: CentralNodeWrapperMid,
):
    assign_input_json = prepare_json_args_for_centralnode_commands(
        "assign_resources_mid", command_input_factory
    )

    assign_json = json.loads(assign_input_json)
    del assign_json["sdp"]["execution_block"]["scan_types"][0]["scan_type_id"]
    # Invoke AssignResources() Command on TMC
    LOGGER.info("Invoking AssignResources command on TMC CentralNode")
    pytest.command_result = central_node_mid.perform_action(
        "AssignResources", json.dumps(assign_json)
    )


@when(
    parsers.parse(
        "I issue the command AssignResources passing an invalid JSON script3 to the subarray {subarray_id}"  # noqa: E501
    )
)
def send_assignresource_with_invalid_json3(
    command_input_factory: JsonFactory,
    event_tracer: TangoEventTracer,
    central_node_mid: CentralNodeWrapperMid,
):
    assign_input_json = prepare_json_args_for_centralnode_commands(
        "assign_resources_mid", command_input_factory
    )

    assign_json = json.loads(assign_input_json)

    del assign_json["sdp"]["execution_block"]["channels"][0]["channels_id"]
    # Invoke AssignResources() Command on TMC
    LOGGER.info("Invoking AssignResources command on TMC CentralNode")
    pytest.command_result = central_node_mid.perform_action(
        "AssignResources", json.dumps(assign_json)
    )


@pytest.mark.batch2
@pytest.mark.SKA_mid
@scenario(
    "../features/successful_scan_after_assigning_unavailable_resources.feature",  # noqa: E501
    "Successfully execute a scan after invoking assign resources with unavailable resources",  # noqa: E501
)
def test_assign_resource_with_unavailable_resources():
    """
    Test successful Scan after invoking AssignResource command with
    unavailable resources.

    """


@when(
    parsers.parse(
        "I issue the command AssignResources with unavailable resources {resources_list} to the subarray {subarray_id}"  # noqa: E501
    )
)
def invoke_assign_resources_two(
    command_input_factory: JsonFactory,
    event_tracer: TangoEventTracer,
    central_node_mid: CentralNodeWrapperMid,
    resources_list,
):
    assign_input_json = prepare_json_args_for_centralnode_commands(
        "assign_resources_mid", command_input_factory
    )

    assign_json = json.loads(assign_input_json)

    assign_json["dish"]["receptor_ids"][0] = resources_list
    # Invoke AssignResources() Command on TMC
    LOGGER.info("Invoking AssignResources command on TMC CentralNode")
    pytest.command_result = central_node_mid.perform_action(
        "AssignResources", json.dumps(assign_json)
    )


@then(
    parsers.parse(
        "the subarray {subarray_id} returns an error message with {resorces_list}"  # noqa: E501
    )
)  # noqa: E501
def invalid_command_rejection_with_unavailable_resources(resources_list):
    assert (
        "The following Receptor id(s) do not exist:"
    ) and resources_list in pytest.command_result[1][0]
    assert pytest.command_result[0][0] == ResultCode.REJECTED


@pytest.mark.batch2
@pytest.mark.SKA_mid
@scenario(
    "../features/successful_scan_after_assigning_unavailable_resources.feature",  # noqa: E501
    "Successfully execute a scan after invoking successive assign resources with unavailable resources",  # noqa: E501
)
def test_assign_resource_successive_invokation_with_unavailable_resources():
    """
    Test successful execution of Scan after successful invokation of
    AssignResource command with unavailable resources.
    """


@pytest.mark.batch2
@pytest.mark.SKA_mid
@scenario(
    "../features/successful_scan_after_combination_of_failed_assign_resources.feature",  # noqa: E501
    "Successfully execute a scan after combination of failed assign resources",  # noqa: E501
)
def test_assign_resource_with_combination():
    """
    Test successful Scan after invoking AssignResource with combination of
    invalid json and unavailable resources.
    Sequence
    1. Unavailable Resources
    2. Invalid json
    """


@pytest.mark.batch2
@pytest.mark.SKA_mid
@scenario(
    "../features/successful_scan_after_combination_of_failed_assign_resources.feature",  # noqa: E501
    "Successfully execute a scan after second combination of failed assign resources",  # noqa: E501
)
def test_assign_resource_with_second_combination():
    """
    Test successful Scan after invoking AssignResource command with
    combination of invalid json and unavailable resources.
    Sequence:
    1. Invalid json
    2. Unavailable Resources
    """
