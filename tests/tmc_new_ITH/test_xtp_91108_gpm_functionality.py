"""Test module to test the GPM functionality"""

import ast
import json
import logging
import re

import pytest
from assertpy import assert_that
from pytest_bdd import given, parsers, scenario, then, when
from ska_control_model import ObsState
from ska_integration_test_harness.actions.utils.generate_eb_pb_ids import (
    generate_eb_pb_ids,
)
from ska_integration_test_harness.facades import DishesFacade
from ska_integration_test_harness.facades.tmc_facade import TMCFacade
from ska_integration_test_harness.inputs.json_input import DictJSONInput
from ska_integration_test_harness.inputs.test_harness_inputs import (
    TestHarnessInputs,
)
from ska_tango_testing.integration import TangoEventTracer, log_events
from ska_tango_testing.mock.placeholders import Anything

from tests.resources.test_harness.utils.enums import ResultCode
from tests.resources.test_support.constant import (
    ERROR_PROPAGATION_DEFECT,
    RESET_DEFECT,
)
from tests.tmc_csp_new_ITH.conftest import ASSERTIONS_TIMEOUT
from tests.tmc_csp_new_ITH.utils.my_file_json_input import MyFileJSONInput

logger = logging.getLogger(__name__)


def get_gpm_report(table):
    """Generates GPM report from table data for test validation."""

    gpm_report = {}
    lines = [
        line.strip() for line in table.strip().split("\n") if line.strip()
    ]
    headers = [h.strip() for h in lines[0].split("|") if h.strip()]
    for row in lines[1:]:
        values = [v.strip() for v in row.split("|") if v.strip()]
        entry = dict(zip(headers, values))
        dish_id = entry["Dish_ID"].lower()
        status = entry["Status"]
        reason = entry["Reason"]
        gpm_report[dish_id] = {"status": status, "reason": reason}

    return gpm_report


def extract_gpm_failure_details(events_tracer):
    """Extracts parsed failure details from first failed GPM command."""

    event_data = None
    for event in events_tracer.events:
        if isinstance(event.attribute_value, tuple):
            if "SetGlobalPointingModel" in event.attribute_value[0]:
                event_data = json.loads(event.attribute_value[1])
                if event_data[0] == int(ResultCode.FAILED):
                    break

    return ast.literal_eval(event_data[1].split("SetGPM failed on: ", 1)[1])


@pytest.mark.batch1
@pytest.mark.SKA_mid
@scenario(
    "../tmc_new_ITH/features/xtp_91108_gpm_functionality.feature",
    "TMC processes GPM JSON and reports status per dish",
)
def test_verify_gpm_functionality():
    """Test TMC can apply and report GPM for specified bands
    for given dishes"""


@given("a TMC Mid telescope is operational")
def given_a_tmc(
    tmc: TMCFacade,
    dishes: DishesFacade,
    event_tracer: TangoEventTracer,
):
    """Given a TMC"""
    event_tracer.clear_events()
    event_tracer.subscribe_event(tmc.subarray_node, "obsState")
    event_tracer.subscribe_event(tmc.central_node, "longRunningCommandResult")
    event_tracer.subscribe_event(tmc.central_node, "GlobalPointingModelStatus")
    log_events(
        {
            tmc.central_node: [
                "longRunningCommandResult",
                "GlobalPointingModelStatus",
            ],
            tmc.subarray_node: ["obsState"],
        }
    )
    tmc.move_to_on(wait_termination=True, is_long_running_command=True)
    # Setup TMC for testing negative scenarios
    # before invoking SetGlobalPointingModel command on TMC
    assign_input = MyFileJSONInput("centralnode", "assign_resources_mid")
    assign_input = generate_eb_pb_ids(assign_input)
    assign_input = json.loads(assign_input.as_str())
    assign_input["dish"]["receptor_ids"] = ["SKA036"]
    assign_input["sdp"]["resources"]["receptors"] = ["SKA036"]
    tmc.force_change_of_obs_state(
        ObsState.IDLE,
        TestHarnessInputs(assign_input=DictJSONInput(assign_input)),
        wait_termination=True,
    )
    dish_63 = dishes.dish_master_dict["dish_063"]
    dish_63.SetDefective(ERROR_PROPAGATION_DEFECT)


# Parse table rows by splitting on '|' to extract Dish_ID
# (converted to lowercase)
# and Bands (split by commas into list). Headers are derived
# from first row.
@given(
    parsers.re(
        r"the following GPM configurations are provided for version "
        r"(?P<version>[\d\.]+):\n"
        r"(?P<table>(?:\s*\|.*\|\s*\n?)+)",
        re.MULTILINE | re.DOTALL,
    ),
    target_fixture="gpm_config",
)
def given_a_gpm_json(version, table):
    """Build a GPM json from data provided in feature"""

    lines = [
        line.strip() for line in table.strip().split("\n") if line.strip()
    ]
    headers = [h.strip() for h in lines[0].split("|") if h.strip()]
    receptors = {}
    gpm_input_data = {}

    for row in lines[1:]:
        values = [v.strip() for v in row.split("|") if v.strip()]
        entry = dict(zip(headers, values))
        dish_id = entry["Dish_ID"].lower()
        bands = [b.strip() for b in entry["Bands"].split(",")]
        receptors[dish_id] = bands

    gpm_input_data = {"version": version, "receptors": receptors}

    logger.info("Formed GPM input: %s", gpm_input_data)
    return gpm_input_data


@when("the GPM configuration is applied via TMC")
def apply_gpm_to_dishes(tmc: TMCFacade, gpm_config):
    """Invoke SetGlobalPointingModel on dishes"""

    message, pytest.unique_id = tmc.central_node.SetGlobalPointingModel(
        json.dumps(gpm_config)
    )
    logger.info("Command ID: %s Message: %s", message, pytest.unique_id)


@then(
    parsers.re(
        r"TMC reports the status as below for the respective dish id:\n"
        r"(?P<table>.+)",
        re.MULTILINE | re.DOTALL,
    )
)
def tmc_reports_gpm_status_on_dish(
    tmc: TMCFacade,
    event_tracer: TangoEventTracer,
    table,
    gpm_config,
    dishes: DishesFacade,
):
    """Test TMC reports GPM for specified bands on dishes"""

    logger.info("GPM data for validation %s", get_gpm_report(table))
    (
        assert_that(event_tracer)
        .described_as(
            'FAILED ASSUMPTION IN "THEN" STEP: '
            "TMC Central Node device "
            f"({tmc.central_node.dev_name()}) "
            "is expected have longRunningCommandResult as "
            "(unique_id, COMMAND_RESULT)",
        )
        .within_timeout(ASSERTIONS_TIMEOUT)
        .has_change_event_occurred(
            tmc.central_node,
            "longRunningCommandResult",
            (pytest.unique_id[0], Anything),
        )
    )

    event_tracer_lrcr_data = extract_gpm_failure_details(event_tracer)

    for dish_id, validation_data in get_gpm_report(table).items():
        if "Applied" not in validation_data["status"]:
            dish_gpm_lrcr_data = event_tracer_lrcr_data[dish_id]
            if isinstance(dish_gpm_lrcr_data, str):
                assert validation_data["reason"] in dish_gpm_lrcr_data
            elif isinstance(dish_gpm_lrcr_data, dict):
                reasons = validation_data["reason"].split(",")
                lrcr_messages = [
                    value[1].lower() for value in dish_gpm_lrcr_data.values()
                ]
                lrcr_result_codes = [
                    value[0] for value in dish_gpm_lrcr_data.values()
                ]
                logger.info(
                    "Test reasons for validations: %s "
                    "LRCR messages: %s"
                    "Result codes: %s",
                    reasons,
                    lrcr_messages,
                    lrcr_result_codes,
                )
                for value in reasons:
                    assert any(
                        value.lower() in msg.lower() for msg in lrcr_messages
                    )
                for value in lrcr_result_codes:
                    assert int(ResultCode.FAILED) == value
        else:
            global_pointing_model_status = json.loads(
                tmc.central_node.globalpointingmodelstatus
            )
            assert (
                gpm_config["version"]
                == global_pointing_model_status[dish_id]["Band_1"]
            )
            assert (
                gpm_config["version"]
                == global_pointing_model_status[dish_id]["Band_5a"]
            )

    dishes.dish_master_dict["dish_063"].SetDefective(RESET_DEFECT)

    release_input = MyFileJSONInput("centralnode", "release_resources_mid")
    event_tracer.clear_events()

    tmc.release_resources(release_input, wait_termination=False)
    assert_that(event_tracer).described_as(
        f"TMC Subarray Node device ({tmc.subarray_node})"
        "ObsState attribute values should move "
        f"from IDLE to EMPTY."
    ).within_timeout(ASSERTIONS_TIMEOUT).has_change_event_occurred(
        tmc.subarray_node, "obsState", ObsState.EMPTY
    )
