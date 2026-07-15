"""Test configuration file for ska_tmc_integration"""
import json
import logging
import os
import time
from datetime import datetime, timezone
from os.path import dirname, join
from time import sleep
from typing import Generator

import katpoint
import pytest
import tango
from pytest_bdd import given, parsers, then, when
from ska_control_model import AdminMode
from ska_ser_logging import configure_logging
from ska_tango_base.control_model import ObsState
from ska_tango_testing.integration import TangoEventTracer
from ska_tango_testing.mock.tango.event_callback import (
    MockTangoEventCallbackGroup,
)
from tango import DevState

from tests.resources.test_harness.central_node_mid import CentralNodeWrapperMid
from tests.resources.test_harness.event_recorder import EventRecorder
from tests.resources.test_harness.helpers import (
    CSP_SIMULATION_ENABLED,
    get_device_simulators,
    prepare_json_args_for_centralnode_commands,
    wait_and_validate_device_attribute_value,
)
from tests.resources.test_harness.simulator_factory import SimulatorFactory
from tests.resources.test_harness.subarray_node import SubarrayNodeWrapper
from tests.resources.test_harness.tmc_mid import TMCMid
from tests.resources.test_harness.utils.common_utils import (
    JsonFactory,
    SharedContext,
)
from tests.resources.test_harness.utils.enums import ResultCode
from tests.resources.test_support.constant import (
    COMMAND_COMPLETED,
    TMC_MID_VCC_CONFIG_INPUT,
    centralnode,
    csp_master,
    tmc_csp_master_leaf_node,
)

configure_logging(logging.DEBUG)
LOGGER = logging.getLogger(__name__)
MID_DELAYMODEL_VERSION = "https://schema.skao.int/ska-mid-csp-delaymodel/3.0"
WEATHER_STATION = "ska-mid/weather-monitoring/s1"


def pytest_sessionstart(session):
    """
    Pytest hook; prints info about tango version.
    :param session: a pytest Session object
    :type session: :py:class:`pytest.Session`
    """
    print(tango.utils.info())


def pytest_addoption(parser):
    """
    Pytest hook; implemented to add the `--true-context` option, used to
    indicate that a true Tango subsystem is available, so there is no
    need for a :py:class:`tango.test_context.MultiDeviceTestContext`.
    :param parser: the command line options parser
    :type parser: :py:class:`argparse.ArgumentParser`
    """
    parser.addoption(
        "--true-context",
        action="store_true",
        default=False,
        help=(
            "Tell pytest that you have a true Tango context and don't "
            "need to spin up a Tango test context"
        ),
    )


def get_input_str(path):
    """
    Returns input json string
    :rtype: String
    """
    with open(path, "r", encoding="UTF-8") as file:
        input_arg = file.read()
    return input_arg


@pytest.fixture
def event_tracer():
    """Returns a TangoEventTracer instance."""
    return TangoEventTracer()


@pytest.fixture()
def json_factory():
    """
    Json factory for getting json files
    """

    def _get_json(slug):
        return get_input_str(join(dirname(__file__), "data", f"{slug}.json"))

    return _get_json


TELESCOPE_ENV = os.getenv("TELESCOPE")

TIMEOUT = 600


def update_configure_json(
    configure_json: str,
    scan_duration: float,
    transaction_id: str,
    scan_type: str,
    config_id: str,
) -> str:
    """
    Returns a json with updated values for the given keys
    """
    config_dict = json.loads(configure_json)

    config_dict["tmc"]["scan_duration"] = scan_duration
    config_dict["transaction_id"] = transaction_id
    config_dict["sdp"]["scan_type"] = scan_type
    config_dict["csp"]["common"]["config_id"] = config_id
    return json.dumps(config_dict)


def update_scan_json(scan_json: str, scan_id: int, transaction_id: str) -> str:
    """
    Returns a json with updated values for the given keys
    """
    scan_dict = json.loads(scan_json)

    scan_dict["scan_id"] = scan_id
    scan_dict["transaction_id"] = transaction_id
    return json.dumps(scan_dict)


@pytest.fixture()
def change_event_callbacks() -> MockTangoEventCallbackGroup:
    """subarray_node
    Return a dictionary of Tango device change event callbacks with
    asynchrony support.

    :return: a collections.defaultdict that returns change event
        callbacks by name.
    """
    return MockTangoEventCallbackGroup(
        "longRunningCommandResult",
        timeout=50.0,
    )


@pytest.fixture()
def central_node_mid() -> Generator[CentralNodeWrapperMid, None, None]:
    """Return CentralNode for Mid Telescope and calls tear down"""
    central_node = CentralNodeWrapperMid()
    yield central_node
    # this will call after test complete
    central_node.tear_down()


@pytest.fixture()
def tmc_mid() -> Generator[TMCMid, None, None]:
    """Return TMC Mid object"""
    tmc_mid = TMCMid()
    yield tmc_mid
    tmc_mid.tear_down()


@pytest.fixture()
def subarray_node() -> Generator[SubarrayNodeWrapper, None, None]:
    """Return SubarrayNode and calls tear down"""
    subarray = SubarrayNodeWrapper()
    yield subarray
    # this will call after test complete
    subarray.tear_down()


@pytest.fixture()
def command_input_factory() -> JsonFactory:
    """Return Json Factory"""
    return JsonFactory()


@pytest.fixture()
def simulator_factory() -> SimulatorFactory:
    """Return Simulator Factory for Mid Telescope"""
    return SimulatorFactory()


@pytest.fixture()
def event_recorder() -> Generator[EventRecorder, None, None]:
    """Return EventRecorder and clear events"""
    event_rec = EventRecorder()
    yield event_rec
    event_rec.clear_events()


def verify_dish_vcc_command_status_completed(central_node, csp_master_device):
    """Method to verify DishVcc is initialized and completed."""

    # Using constants for readability
    STATUS_COMPLETED = 3
    STATUS_FAILED = 4
    is_dish_vcc_in_desired_state = True

    if (
        int(central_node.DishVccCommandStatus) == 0
        or csp_master_device.adminmode != AdminMode.ONLINE
    ):
        csp_master_device.adminmode = AdminMode.ONLINE
        sleep(10)

    # 1. Initial poll loop
    timeout = 200
    while timeout > 0:
        current_status = int(central_node.DishVccCommandStatus)
        if current_status in (STATUS_COMPLETED, STATUS_FAILED):
            LOGGER.info("LoadDishCfg Completed")
            is_dish_vcc_in_desired_state = False
            break
        timeout -= 1
        sleep(1)

    err_msg = "LoadDishCfg command status not completed, can't run tests"
    # 2. Recovery Logic if the initial attempt failed
    if current_status == STATUS_FAILED or is_dish_vcc_in_desired_state:
        # Attempt recovery re-configuration
        cn = central_node
        cn.loaddishcfg(json.dumps(TMC_MID_VCC_CONFIG_INPUT))
        command_status_ok = False
        retry_timeout = 20
        msg = "ALL DISH OK"
        while retry_timeout > 0:
            # Check validation status
            validation_str = cn.DishVccValidationStatus
            status_dict = json.loads(validation_str)
            all_dish_ok = any(
                msg in str(value) for value in status_dict.values()
            )
            # Check command status
            if int(cn.DishVccCommandStatus) == STATUS_COMPLETED:
                command_status_ok = True

            # If both conditions are met, recovery succeeded
            # (but we still raise the exception per original logic)
            if all_dish_ok and command_status_ok:
                LOGGER.info("LoadDishCfg Completed")
                break
            retry_timeout -= 1
            sleep(1)
        if not command_status_ok:
            raise Exception(
                f"{err_msg}. Recovery attempt also failed or timed out."
            )


def invoke_load_dish_cfg_cmd() -> bool:
    """Method to invoke load dish cfg"""

    cn_wrapper = CentralNodeWrapperMid()
    central_node = cn_wrapper.central_node
    event_recorder = EventRecorder()
    cspmln_validation_string = "TMC and CSP Master Dish Vcc Version is Same"
    event_recorder.subscribe_event(central_node, "longRunningCommandResult")
    central_node_dish_vcc_validation_status = {
        "dish": "ALL DISH OK",
        tmc_csp_master_leaf_node: cspmln_validation_string,
    }
    _, unique_id = central_node.loaddishcfg(
        json.dumps(TMC_MID_VCC_CONFIG_INPUT)
    )
    event_recorder.has_change_event_occurred(
        central_node,
        "longRunningCommandResult",
        (unique_id[0], COMMAND_COMPLETED),
        lookahead=10,
    )
    event_recorder.clear_events()
    timeout = 10
    while timeout > 0:
        if (
            json.loads(central_node.DishVccValidationStatus)
            == central_node_dish_vcc_validation_status
        ):
            return False
        timeout -= 1
        sleep(1)
    return True


def assert_dish_vcc_validation_status_is_ok():
    """Method to check dish vcc validation status is ok"""

    timeout = 10
    dish_vcc_validation_status_not_matching = True
    cn_wrapper = CentralNodeWrapperMid()
    central_node = cn_wrapper.central_node
    cspmln_validation_string = "TMC and CSP Master Dish Vcc Version is Same"
    central_node_dish_vcc_validation_status = {
        "dish": "ALL DISH OK",
        tmc_csp_master_leaf_node: cspmln_validation_string,
    }
    while timeout > 0:
        if (
            json.loads(central_node.DishVccValidationStatus)
            == central_node_dish_vcc_validation_status
        ):
            dish_vcc_validation_status_not_matching = False
            break
        timeout -= 1
        sleep(1)
    if dish_vcc_validation_status_not_matching:
        LOGGER.info(
            "Invoking LoadDishCfg. Dish VCC Status: %s",
            central_node.DishVccValidationStatus,
        )
        dish_vcc_validation_status_not_matching = invoke_load_dish_cfg_cmd()
    assert not dish_vcc_validation_status_not_matching


@pytest.fixture(scope="session", autouse=True)
def dish_vcc_command_status_completed_at_startup():
    """Run dish VCC command status verification at the
    beginning of pytest execution."""
    central_node = CentralNodeWrapperMid()
    verify_dish_vcc_command_status_completed(
        central_node.central_node, central_node.csp_master
    )


def wait_for_dish_mode_change(
    target_mode: int, dishfqdn: str, timeout_seconds: int
):
    """Returns True if the dishMode is changed to a expected value"""
    LOGGER.info("target_mode: %s", target_mode)
    start_time = time.time()

    while time.time() - start_time < timeout_seconds:
        if dishfqdn.dishMode == target_mode:
            return True
        time.sleep(1)

    return False


def wait_for_telescope_state_change(
    target_state: int, centralnode_fqdn: str, timeout_seconds: int
):
    """
    Waits for the telescopeState of a central node
    to change to the specified target_state.

    Parameters:
    - target_state (int): The expected telescopeState
                          to wait for.
    - centralnode_fqdn (str): Fully Qualified Domain
                              Name (FQDN) of the central node.
    - timeout_seconds (int): Maximum time (in seconds) to
                            wait for the state change.

    Returns:
    - bool: True if the telescopeState changes
      to the target_state within the specified timeout, False otherwise.
    """

    start_time = time.time()
    while time.time() - start_time < timeout_seconds:
        if centralnode_fqdn.telescopeState == target_state:
            return True
        time.sleep(1)

    return False


def wait_for_pointing_state_change(
    target_mode: int, dishfqdn: str, timeout_seconds: int
):
    """Returns True if the pointingState is changed to a expected value"""
    start_time = time.time()

    while time.time() - start_time < timeout_seconds:
        if dishfqdn.pointingState.value == target_mode:
            return True
        time.sleep(1)

    return False


def wait_for_obsstate_state_change(
    target_mode: int, device: str, timeout_seconds: int
):
    """Returns True if the pointingState is changed to a expected value"""
    start_time = time.time()

    while time.time() - start_time < timeout_seconds:
        if device.obsState.value == target_mode:
            return True
        time.sleep(1)

    return False


def wait_for_DeviceInfo_change(device: str, timeout_seconds: int):
    """Returns True if the obsState is changed to ObsState.EMPTY"""
    start_time = time.time()

    while time.time() - start_time < timeout_seconds:

        attribute_value = json.loads(device.lastDeviceInfoChanged)

        if attribute_value["obsState"] == "ObsState.EMPTY":

            return True
        time.sleep(1)

    return False


@pytest.fixture
def shared_context():
    """
    This is used for sharing data between BDD tests
    """
    return SharedContext()


@pytest.fixture(scope="module")
def stored_unique_id():
    """
    A placeholder fixture to access
    the uniques_ids in multiple function as a parameter
    :returns: empty list
    """
    return []


@pytest.fixture(scope="session", autouse=True)
def is_dish_vcc_set():
    """
    Validate dish vcc config set to true
    """
    try:
        weather_Station_dev_proxy = tango.DeviceProxy(WEATHER_STATION)
        weather_Station_dev_proxy.adminMode = 0
    except Exception as e:
        # Any other unexpected error should surface as a test failure
        LOGGER.exception(
            "Unexpected error in set_weather_station fixture %s", e
        )

    csp_master_device = tango.DeviceProxy(csp_master)
    csp_subarray_01 = tango.DeviceProxy("mid-csp/subarray/01")
    csp_subarray_02 = tango.DeviceProxy("mid-csp/subarray/02")
    if csp_subarray_01.adminMode != AdminMode.ONLINE:
        csp_subarray_01.adminMode = AdminMode.ONLINE
    if csp_subarray_02.adminMode != AdminMode.ONLINE:
        csp_subarray_02.adminMode = AdminMode.ONLINE
    if csp_master_device.adminMode != AdminMode.ONLINE:
        csp_master_device.adminMode = AdminMode.ONLINE
    csp_state = csp_master_device.state()
    if CSP_SIMULATION_ENABLED.lower() == "true" and csp_state in (
        tango.DevState.UNKNOWN,
        tango.DevState.DISABLE,
    ):
        csp_master_device.setdirectstate(tango.DevState.OFF)
    central_node = tango.DeviceProxy(centralnode)
    assert wait_and_validate_device_attribute_value(
        central_node,
        "isDishVccConfigSet",
        True,
    ), "Timeout while waiting for isDishVccConfigSet to true"


@given("the telescope is in ON state")
def check_telescope_is_in_on_state(
    central_node_mid: CentralNodeWrapperMid, event_recorder: EventRecorder
) -> None:
    """Ensure telescope is in ON state."""
    central_node_mid.move_to_on()
    event_recorder.subscribe_event(
        central_node_mid.central_node, "telescopeState"
    )
    assert event_recorder.has_change_event_occurred(
        central_node_mid.central_node,
        "telescopeState",
        DevState.ON,
    )


@given("TMC subarray is in ObsState IDLE")
def move_subarray_node_to_idle_obsstate(
    central_node_mid: CentralNodeWrapperMid,
    event_recorder: EventRecorder,
    command_input_factory: JsonFactory,
    subarray_node,
) -> None:
    """
    Move TMC Subarray to IDLE obsstate.
    :param central_node_mid: fixture for a TMC CentralNode Mid under test
    which provides simulated master devices
    :param event_recorder: fixture for a MockTangoEventCallbackGroup
    for validating the subscribing and receiving events.
    :param command_input_factory: fixture for creating input required
    for command
    :param subarray_node: fixture for a TMC SubarrayNode under test
    """
    assign_input_json = prepare_json_args_for_centralnode_commands(
        "assign_resources_mid", command_input_factory
    )
    event_recorder.subscribe_event(
        central_node_mid.central_node, "longRunningCommandResult"
    )
    # Create json for AssignResources commands with requested subarray_id
    assign_input = json.loads(assign_input_json)
    _, unique_id = central_node_mid.store_resources(json.dumps(assign_input))

    event_recorder.subscribe_event(central_node_mid.subarray_node, "obsState")
    assert event_recorder.has_change_event_occurred(
        central_node_mid.subarray_node,
        "obsState",
        ObsState.IDLE,
        lookahead=10,
    )
    assert event_recorder.has_change_event_occurred(
        central_node_mid.central_node,
        "longRunningCommandResult",
        (unique_id[0], json.dumps([ResultCode.OK, "Command Completed"])),
        lookahead=5,
    )


@given("CSP subarray transitioned to obsState IDLE")
def csp_subarray_is_in_idle(
    event_recorder: EventRecorder, simulator_factory: SimulatorFactory
):
    "Method to check CSP subarray is in IDLE."
    csp_sim, _, _, _, _, _ = get_device_simulators(simulator_factory)
    event_recorder.subscribe_event(csp_sim, "obsState")
    assert event_recorder.has_change_event_occurred(
        csp_sim,
        "obsState",
        ObsState.IDLE,
    )


@given(parsers.parse("TMC subarray {subarray_id} stuck in obsState FAULT"))
def tmc_subarray_stuck_in_resourcing(
    subarray_node: SubarrayNodeWrapper,
    event_recorder: EventRecorder,
    subarray_id: str,
):
    "Method to check TMC subarray stuck in Resourcing."
    event_recorder.subscribe_event(subarray_node.subarray_node, "obsState")
    subarray_node.set_subarray_id(subarray_id)
    assert event_recorder.has_change_event_occurred(
        subarray_node.subarray_node,
        "obsState",
        ObsState.FAULT,
    )


@when(parsers.parse("I invoked Abort on TMC subarray {subarray_id}"))
def invoke_abort(subarray_node: SubarrayNodeWrapper, subarray_id: str):
    """
    This method invokes abort command on tmc subarray.
    """
    subarray_node.set_subarray_id(subarray_id)
    subarray_node.execute_transition("Abort")


@then("the CSP subarray transitions to ObsState ABORTED")
def sdp_csp_subarray_is_in_aborted_obsstate(
    event_recorder: EventRecorder, simulator_factory: SimulatorFactory
):
    """
    Method to check SDP subarray and CSP subarray is in ABORTED obsstate
    """
    csp_sim, sdp_sim, _, _, _, _ = get_device_simulators(simulator_factory)
    event_recorder.subscribe_event(sdp_sim, "obsState")
    event_recorder.subscribe_event(csp_sim, "obsState")

    assert event_recorder.has_change_event_occurred(
        csp_sim,
        "obsState",
        ObsState.ABORTED,
    )


@then(
    parsers.parse(
        "the TMC subarray {subarray_id} transitions to ObsState ABORTED"
    )
)
def tmc_subarray_is_in_aborted_obsstate(
    subarray_node: SubarrayNodeWrapper,
    event_recorder: EventRecorder,
    subarray_id: str,
):
    """
    Method to check if TMC subarray is in ABORTED obsstate
    """
    event_recorder.subscribe_event(subarray_node.subarray_node, "obsState")
    subarray_node.set_subarray_id(subarray_id)
    assert event_recorder.has_change_event_occurred(
        subarray_node.subarray_node,
        "obsState",
        ObsState.ABORTED,
    )


MID_DELAY_JSON = {
    "interface": "https://schema.skao.int/ska-mid-csp-delaymodel/3.0",
    "start_validity_sec": 0.1,
    "cadence_sec": 0.1,
    "validity_period_sec": 0.1,
    "config_id": "",
    "subarray": 1,
    "receptor_delays": [
        {"receptor": "", "xypol_coeffs_ns": [], "ypol_offset_ns": 0.0},
        {"receptor": "", "xypol_coeffs_ns": [], "ypol_offset_ns": 0.0},
    ],
}

POINTING_CONFIGS = {
    "icrs": {
        "groups": [
            {
                "field": {
                    "target_name": "Polaris Australis",
                    "reference_frame": "icrs",
                    "attrs": {"c1": 317.199, "c2": -88.95636},
                }
            }
        ]
    },
    "tle": {
        "groups": [
            {
                "field": {
                    "target_name": "ANGOSAT 2",
                    "reference_frame": "tle",
                    "attrs": {
                        "line1": "1 54033U 22131A   26187.02363267  "
                        ".00000150  00000+0  00000+0 0  9991",
                        "line2": "2 54033   0.0192 123.5880 0000094 "
                        "274.7177 277.2087  1.00271785 13664",
                    },
                }
            }
        ]
    },
    "altaz": {
        "groups": [
            {
                "field": {
                    "target_name": "South Celestial Pole",
                    "reference_frame": "altaz",
                    "attrs": {"c1": 180.0, "c2": 30.71},
                }
            }
        ]
    },
    "galactic": {
        "groups": [
            {
                "field": {
                    "target_name": "Large Magellanic Cloud",
                    "reference_frame": "galactic",
                    "attrs": {"c1": 280.4652, "c2": -32.8884},
                }
            }
        ]
    },
    "special": {
        "groups": [
            {
                "field": {
                    "target_name": None,
                    "reference_frame": "special",
                }
            }
        ]
    },
}


ASSIGNED_RECEPTORS = ["SKA001", "SKA036", "SKA077", "SKA100"]

# SKA-Mid Dish mechanical limits (sourced from Dish LMC / tmdata)
AZ_MIN_DEG = -270.0
AZ_MAX_DEG = 270.0
EL_MIN_DEG = 17.5
EL_MAX_DEG = 90.0

NON_SIDEREAL_OBJECTS = [
    "Sun",
    "Moon",
    "Mercury",
    "Venus",
    "Mars",
    "Jupiter",
    "Saturn",
    "Uranus",
    "Neptune",
]

_SKA001_ANTENNA = "SKA001, -30:42:39.8, 21:26:38.0, 1086, 15.0"


def pick_visible_solar_system_target(
    receptor_ids: list[str],
    candidate_bodies: list[str] | None = None,
    when_utc: datetime | None = None,
) -> str:
    """Return the first solar-system object visible to ALL given receptors.

    Raises RuntimeError if no candidate is visible.
    """
    if candidate_bodies is None:
        candidate_bodies = NON_SIDEREAL_OBJECTS

    if when_utc is None:
        when_utc = datetime.now(timezone.utc)

    if not receptor_ids:
        raise ValueError("receptor_ids cannot be empty")

    for body_name in candidate_bodies:
        visible_to_all = True
        for receptor_id in receptor_ids:
            try:
                antenna = katpoint.Antenna(_SKA001_ANTENNA)
                target = katpoint.Target(f"{body_name}, special")
                target.antenna = antenna
                result = target.azel(when_utc)

                az = result.az
                el = result.alt

                az_deg = float(az.deg)
                el_deg = float(el.deg)

                if not (
                    AZ_MIN_DEG <= az_deg <= AZ_MAX_DEG
                    and EL_MIN_DEG <= el_deg <= EL_MAX_DEG
                ):
                    LOGGER.debug(
                        "Rejected %s for %s: az=%.2f°, el=%.2f°",
                        body_name,
                        receptor_id,
                        az_deg,
                        el_deg,
                    )
                    visible_to_all = False
                    break
            except Exception as exc:
                LOGGER.debug(
                    "Error checking %s for %s: %s", body_name, receptor_id, exc
                )
                visible_to_all = False
                break

        if visible_to_all:
            LOGGER.info(
                "Selected special target: %s (visible to all receptors: %s)",
                body_name,
                receptor_ids,
            )
            return body_name

    raise RuntimeError(
        f"No solar-system body from {candidate_bodies} is visible "
    )
