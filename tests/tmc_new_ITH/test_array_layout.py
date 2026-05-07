"""Verifies arraylayout functionality
"""

import json
import time

import pytest
import tango
from assertpy import assert_that
from pytest_bdd import given, scenario, then, when
from ska_control_model import ObsState, ResultCode
from ska_integration_test_harness.facades.csp_facade import CSPFacade
from ska_integration_test_harness.facades.sdp_facade import SDPFacade
from ska_integration_test_harness.facades.tmc_facade import TMCFacade
from ska_integration_test_harness.inputs.test_harness_inputs import (
    TestHarnessInputs,
)
from ska_tango_testing.integration import TangoEventTracer, log_events
from ska_tango_testing.mock.placeholders import Anything

from tests.conftest import LOGGER
from tests.resources.test_harness.central_node_mid import CentralNodeWrapperMid
from tests.resources.test_harness.helpers import (
    calculate_epoch_difference,
    generate_ska_epoch_tai_value,
    wait_and_validate_device_attribute_value,
    wait_till_delay_values_are_populated,
)
from tests.resources.test_harness.subarray_node import SubarrayNodeWrapper
from tests.tmc_csp_new_ITH.conftest import (  # SubarrayTestContextData,
    ASSERTIONS_TIMEOUT,
    TIMEOUT,
    SubarrayTestContextData,
)
from tests.tmc_csp_new_ITH.utils.my_file_json_input import MyFileJSONInput


def _setup_event_subscriptions(
    tmc: TMCFacade,
    csp: CSPFacade,
    sdp: SDPFacade,
    event_tracer: TangoEventTracer,
):
    """Subscribe TMC, CSP and SDP devices to track and log obsState events.

    :param tmc: the TMC facade.
    :param csp: the CSP facade.
    :param sdp: the SDP facade.
    :param event_tracer: the event tracer.
    """
    event_tracer.subscribe_event(tmc.subarray_node, "obsState")
    event_tracer.subscribe_event(csp.csp_subarray, "obsState")
    event_tracer.subscribe_event(sdp.sdp_subarray, "obsState")
    event_tracer.subscribe_event(sdp.sdp_subarray, "receiveAddresses")
    event_tracer.subscribe_event(sdp.sdp_subarray, "commandCallInfo")
    event_tracer.subscribe_event(tmc.central_node, "longRunningCommandResult")
    event_tracer.subscribe_event(tmc.central_node, "telescopeState")
    event_tracer.subscribe_event(tmc.central_node, "IsDishVccConfigSet")
    event_tracer.subscribe_event(tmc.subarray_node, "longRunningCommandResult")
    event_tracer.subscribe_event(tmc.subarray_node, "arraylayouturl")
    log_events(
        {
            tmc.subarray_node: [
                "obsState",
                "longRunningCommandResult",
                "arraylayouturl",
            ],
            csp.csp_subarray: ["obsState"],
            sdp.sdp_subarray: [
                "obsState",
                "commandCallInfo",
                "receiveAddresses",
            ],
            tmc.central_node: [
                "longRunningCommandResult",
                "telescopeState",
                "IsDishVccConfigSet",
            ],
        },
        event_enum_mapping={"obsState": ObsState},
    )


@pytest.mark.SKA_tmc_mid_device_restart
@pytest.mark.SKA_mid
@scenario(
    "../tmc_new_ITH/features/array_layout.feature",
    "Verify array layout functionality in TMC mid",
)
def test_verify_array_layout_functionality():
    """Test array layout functionality."""


@given("the telescope is in ON state")
def given_telescope_is_on():
    """
    Telescope is in ON state.
    """
    # TODO: TelescopeOn command invocation is not required for this command.
    # However we need to look at the below issue from earlier test:
    # The availability of the CSP Master restarted from last test does
    # not get updated on CentralNode sometimes. So the TelescopeState ON
    # transition fails in this test. TD item is added to check on why the
    # availability event is not pushed by the CSP
    # Master Leaf Node after restart.


@given("AssignResources is invoked on the SubarrayNode with an arrayLayoutUrl")
def given_assign_resources_executed_successfully(
    tmc: TMCFacade,
    sdp: SDPFacade,
    csp: CSPFacade,
    event_tracer: TangoEventTracer,
):
    """
    Execute the first AssignResources command which should succeed.
    """
    _setup_event_subscriptions(tmc, csp, sdp, event_tracer)
    json_input = MyFileJSONInput(
        "centralnode", "assign_resources_array_layout"
    )
    json_input_str = json.loads(json_input.as_str())
    telmodel = json_input_str["telmodel"]
    pytest.source_uris = telmodel["source_uris"]
    pytest.array_layout_path = telmodel["array_layout_path"]
    _, pytest.unique_id = tmc.assign_resources(json_input)

    assert_that(event_tracer).described_as(
        "TMC subarray obsState should move to IDLE"
    ).within_timeout(ASSERTIONS_TIMEOUT).has_change_event_occurred(
        tmc.subarray_node, "obsState", ObsState.IDLE
    )

    assert_that(event_tracer).described_as(
        "AssignResources command should complete successfully"
    ).within_timeout(ASSERTIONS_TIMEOUT).has_change_event_occurred(
        tmc.central_node,
        "longRunningCommandResult",
        (
            pytest.unique_id[0],
            json.dumps(((ResultCode.OK), "Command Completed")),
        ),
    )


@given("TMC subarray node arrayLayout attribute is updated with layout data")
def verify_subarray_array_layout(
    event_tracer: TangoEventTracer,
    tmc: TMCFacade,
):
    """Verifies the arrayLayout attribute of TMC Subarray Node
    after command AssignResources.
    """

    assert_that(event_tracer).described_as(
        f"TMC Subarray Node device ({tmc.subarray_node})"
        "arrayLayout attribute holds downloaded layout data."
    ).within_timeout(TIMEOUT).has_change_event_occurred(
        tmc.subarray_node,
        "arraylayouturl",
        Anything,
    )
    source_uris = json.loads(tmc.central_node.defaultarraylayouturl)[
        "source_uris"
    ]

    layout_path = json.loads(tmc.central_node.defaultarraylayouturl)[
        "array_layout_path"
    ]

    # Verify array layout links
    assert pytest.source_uris == source_uris
    assert pytest.array_layout_path == layout_path


@when("I invoke the Configure command on the SubarrayNode")
def verify_configure_command(
    tmc: TMCFacade,
    context_fixt: SubarrayTestContextData,
    event_tracer: TangoEventTracer,
    csp,
    sdp,
):
    """Invoke Configure command on SubarrayNode."""

    json_input = MyFileJSONInput("subarray", "command_Configure")
    context_fixt.when_action_result = tmc.configure(
        json_input,
        wait_termination=False,
    )
    context_fixt.starting_state = ObsState.CONFIGURING
    assert_that(event_tracer).described_as(
        f"Both TMC Subarray Node device ({tmc.subarray_node})"
        f", CSP Subarray device ({csp.csp_subarray}) "
        f"and SDP Subarray device ({sdp.sdp_subarray}) "
        "ObsState attribute values should move "
        f"from {str(context_fixt.starting_state)} to READY."
    ).within_timeout(ASSERTIONS_TIMEOUT).has_change_event_occurred(
        tmc.subarray_node,
        "obsState",
        ObsState.READY,
        previous_value=context_fixt.starting_state,
    ).has_change_event_occurred(
        csp.csp_subarray,
        "obsState",
        ObsState.READY,
        previous_value=context_fixt.starting_state,
    ).has_change_event_occurred(
        sdp.sdp_subarray,
        "obsState",
        ObsState.READY,
        previous_value=context_fixt.starting_state,
    )
    context_fixt.starting_state = ObsState.READY
    pytest.SOURCE_VISIBILITY = True


@then(
    "the DLN targetData attribute is updated using the array layout "
    "from Telmodel"
)
def then_dln_target_data_updated():

    """Verify that the DLN targetData attribute is updated."""
    dpd = tango.DeviceProxy("mid-tmc/dish-pointing/ska001")
    target_data = json.loads(dpd.targetData)
    LOGGER.info(f"DPD targetData attribute: {target_data}")
    assert "array_layout" in target_data

    array_layout = target_data["array_layout"]

    assert (
        array_layout.get("interface")
        == "https://schema.skao.int/ska-telmodel-layout-receptor/1.1"
    ), "Unexpected array_layout interface version"

    assert array_layout.get("station_label") == "SKA001"
    assert array_layout.get("station_id") == 65
    # 4. Verify geocentric coordinates exist and are numeric
    geoc = array_layout["location"]["geocentric"]
    assert geoc["coordinate_frame"] == "ITRF"
    assert isinstance(geoc["x"], (float, int))
    assert isinstance(geoc["y"], (float, int))
    assert isinstance(geoc["z"], (float, int))

    # 5. Verify geodetic coordinates are valid Earth coordinates
    geod = array_layout["location"]["geodetic"]
    assert geod["coordinate_frame"] == "WGS84"
    assert -90 <= geod["lat"] <= 90
    assert -180 <= geod["lon"] <= 180


@then(
    "CSP Subarray Leaf Node starts generating delay values with proper epoch"
)
def check_if_delay_values_are_generating(
    subarray_node: SubarrayNodeWrapper,
) -> None:
    """Check if delay values are generating."""
    ska_epoch_tai = generate_ska_epoch_tai_value()
    LOGGER.info(f"ska_epoch_tai : {ska_epoch_tai}")
    delay_json, delay_generated_time = wait_till_delay_values_are_populated(
        subarray_node.csp_subarray_leaf_node
    )
    LOGGER.info(f"delay_json: {delay_json}")
    LOGGER.info(f"delay_generated_time: {delay_generated_time}")
    epoch_difference = calculate_epoch_difference(
        delay_generated_time, ska_epoch_tai, delay_json
    )
    LOGGER.info(f"epoch_difference: {epoch_difference}")
    assert epoch_difference < 30


@then("Program Track Table is populated correctly")
def dish_that_is_tracking(
    central_node_mid: CentralNodeWrapperMid,
):
    """A configured subarray"""
    if pytest.SOURCE_VISIBILITY:
        programTrackTable = central_node_mid.get_track_table_for_dish_id(
            "SKA001"
        )
        LOGGER.info("Value for programTrackTable is: %s", programTrackTable)
        assert len(programTrackTable) == 15
    else:
        LOGGER.info("No source is visible within Elevation limits right now")


@then("TMC is able to memorize the array layout link on restart")
def tmc_able_to_memorize_the_array_layout(
    tmc: TMCFacade,
    default_commands_inputs: TestHarnessInputs,
):
    """
    Verifies that TMC is able to memorize the array layout
    link on restart.
    """

    tmc.force_change_of_obs_state(
        ObsState.EMPTY, default_commands_inputs, wait_termination=True
    )

    # Restart TMC central node device server
    cn_device_server = tango.DeviceProxy(
        f"dserver/{tmc.central_node.info().server_id}"
    )
    cn_device_server.RestartServer()
    time.sleep(8)
    assert wait_and_validate_device_attribute_value(
        tmc.central_node,
        "IsDishVccConfigSet",
        True,
    )

    assert (
        pytest.source_uris
        == json.loads(tmc.central_node.defaultarraylayouturl)["source_uris"]
    )
    assert (
        pytest.array_layout_path
        == json.loads(tmc.central_node.defaultarraylayouturl)[
            "array_layout_path"
        ]
    )
