"""Configurations needed for the tests using the new harness."""

import json
import os
import time
from dataclasses import dataclass
from typing import Any

import pytest
import tango
from assertpy import assert_that
from ska_control_model import ObsState
from ska_integration_test_harness.facades.csp_facade import CSPFacade
from ska_integration_test_harness.facades.dishes_facade import DishesFacade
from ska_integration_test_harness.facades.sdp_facade import SDPFacade
from ska_integration_test_harness.facades.tmc_facade import TMCFacade
from ska_integration_test_harness.init.test_harness_builder import (
    TestHarnessBuilder,
)
from ska_integration_test_harness.inputs.json_input import DictJSONInput
from ska_integration_test_harness.inputs.test_harness_inputs import (
    TestHarnessInputs,
)
from ska_integration_test_harness.structure.telescope_wrapper import (
    TelescopeWrapper,
)
from ska_tango_testing.integration import TangoEventTracer

from tests.conftest import LOGGER
from tests.resources.test_support.constant import TIMEOUT
from tests.tmc_csp_new_ITH.utils.my_file_json_input import MyFileJSONInput
from tests.tmc_new_ITH.utils.dpd_facade import DishPointingDevicesFacade

ASSERTIONS_TIMEOUT = 60

# ------------------------------------------------------------
# Test Harness fixtures

DEFAULT_VCC_CONFIG_INPUT = DictJSONInput(
    {
        "interface": "https://schema.skao.int/ska-mid-cbf-initsysparam/1.0",
        "tm_data_sources": [
            "car://gitlab.com/ska-telescope/ska-telmodel-data?"
            + "ska-sdp-tmlite-repository-1.0.0#tmdata"
        ],
        "tm_data_filepath": (
            "instrument/ska1_mid_psi/ska-mid-cbf-system-parameters.json"
        ),
    }
)


@pytest.fixture
def default_commands_inputs() -> TestHarnessInputs:
    """Default JSON inputs for TMC commands."""
    return TestHarnessInputs(
        assign_input=MyFileJSONInput("centralnode", "assign_resources_mid"),
        configure_input=MyFileJSONInput("subarray", "configure_mid"),
        scan_input=MyFileJSONInput("subarray", "scan_mid"),
        release_input=MyFileJSONInput("centralnode", "release_resources_mid"),
        default_vcc_config_input=DEFAULT_VCC_CONFIG_INPUT,
    )


def _tear_down(tmc: TMCFacade, event_tracer: TangoEventTracer):
    """Function to handle TMC tear down in observation
    state FAULT.

    :param tmc: TMCFacade object to invoke TMC commands
    :type tmc: TMCFacade
    :param event_tracer: TangoEventTracer object for event handling
    :type event_tracer: TangoEventTracer
    """
    if tmc.subarray_node.obsState == ObsState.FAULT:
        tmc.restart(wait_termination=True)
        assert_that(event_tracer).described_as(
            f"TMC Subarray Node device ({tmc.subarray_node})"
            "ObsState attribute value should move "
            f"from {ObsState.FAULT} to EMPTY."
        ).within_timeout(TIMEOUT).has_change_event_occurred(
            tmc.subarray_node, "obsState", ObsState.EMPTY
        )


@pytest.fixture
def telescope_wrapper(
    default_commands_inputs: TestHarnessInputs,
    event_tracer: TangoEventTracer,
) -> TelescopeWrapper:
    """Create an unique test harness with proxies to all devices."""
    test_harness_builder = TestHarnessBuilder()

    # import from a configuration file device names and emulation directives
    # for TMC, CSP, SDP and the Dishes
    test_harness_builder.read_config_file(
        "tests/tmc_new_ITH/test_harness_config.yaml"
    )
    test_harness_builder.validate_configurations()

    # set the default inputs for the TMC commands,
    # which will be used for teardown procedures
    test_harness_builder.set_default_inputs(default_commands_inputs)
    test_harness_builder.validate_default_inputs()
    test_harness_builder.set_kubernetes_namespace(os.getenv("KUBE_NAMESPACE"))

    # build the wrapper of the telescope and it's sub-systems
    telescope = test_harness_builder.build()
    telescope.actions_default_timeout = 120
    yield telescope
    # after a test is completed, reset the telescope to its initial state
    # (obsState=READY, telescopeState=OFF, no resources assigned)
    _tear_down(TMCFacade(telescope), event_tracer)
    telescope.tear_down()


@pytest.fixture
def tmc(telescope_wrapper: TelescopeWrapper) -> TMCFacade:
    """Create a facade to TMC devices."""
    return TMCFacade(telescope_wrapper)


@pytest.fixture
def csp(telescope_wrapper: TelescopeWrapper):
    """Create a facade to CSP devices."""
    return CSPFacade(telescope_wrapper)


@pytest.fixture
def sdp(telescope_wrapper: TelescopeWrapper):
    """Create a facade to SDP devices."""
    return SDPFacade(telescope_wrapper)


@pytest.fixture
def dishes(telescope_wrapper: TelescopeWrapper):
    """Create a facade to dishes devices."""
    return DishesFacade(telescope_wrapper)


@pytest.fixture
def dish_pointng_devices():
    """Create a facade to dish pointing devices."""
    return DishPointingDevicesFacade()


# ----------------------------------------------------------
# Tango event tracer


@pytest.fixture
def event_tracer() -> TangoEventTracer:
    """Create an event tracer."""
    return TangoEventTracer(
        event_enum_mapping={"obsState": ObsState},
    )


# ------------------------------------------------------------
# Other fixtures and common steps


@dataclass
class TestContextData:
    """A class to store shared variables between steps."""

    starting_state: ObsState | None = None
    """The state of the system before the WHEN step."""

    expected_next_state: ObsState | None = None
    """The expected state to be reached if no WHEN step is executed.

    It is meaningful when the starting state is transient and so it will
    automatically change to another state (different both from the starting
    state and the expected next state).

    Leave empty if the starting state is not transient.
    """

    when_action_result: Any | None = None
    """The result of the WHEN step command."""

    when_action_name: str | None = None
    """The name of the Tango command executed in the WHEN step."""

    def is_starting_state_transient(self) -> bool:
        """Check if the starting state is transient."""
        return self.expected_next_state is not None

    csp_obsstate: ObsState | None = None
    sdp_obsstate: ObsState | None = None


@pytest.fixture
def context_data() -> TestContextData:
    """A collection of variables shared between steps.

    The shared variables are the following:

    - previous_state: the previous state of the subarray.
    - expected_next_state: the expected next state of the subarray (specified
        only if the previous st
    - trigger: the trigger that caused the state change.

    :return: the shared variables.
    """
    return TestContextData()


@dataclass
class SubarrayTestContextData:
    """A class to store shared variables between steps."""

    starting_state: ObsState | None = None
    """The state of the system before the WHEN step."""

    expected_next_state: ObsState | None = None
    """The expected state to be reached if no WHEN step is executed.

    It is meaningful when the starting state is transient and so it will
    automatically change to another state (different both from the starting
    state and the expected next state).

    Leave empty if the starting state is not transient.
    """

    when_action_result: Any | None = None
    """The result of the WHEN step command."""

    when_action_name: str | None = None
    """The name of the Tango command executed in the WHEN step."""

    def is_starting_state_transient(self) -> bool:
        """Check if the starting state is transient."""
        return self.expected_next_state is not None


@pytest.fixture
def context_fixt() -> SubarrayTestContextData:
    """A collection of variables shared between steps.

    The shared variables are the following:

    - previous_state: the previous state of the subarray.
    - expected_next_state: the expected next state of the subarray (specified
        only if the previous st
    - trigger: the trigger that caused the state change.

    :return: the shared variables.
    """
    return SubarrayTestContextData()


def get_abort_command_timeout() -> int:
    """
    This method returns value of subarraynode's
    AbortCommandTimeOut property.
    """
    db = tango.Database()
    return int(
        db.get_device_property("mid-tmc/subarray/01", "AbortCommandTimeOut")[
            "AbortCommandTimeOut"
        ][0]
    )


def wait_for_target_data(device, expected_x, expected_y, timeout=5):
    """
    Waits for the targetData attribute to contain the
    specified x and y values under the trajectory key.

    Args:
        device (DeviceProxy): The Tango device proxy object.
        expected_x (float): The expected x value under the trajectory key.
        expected_y (float): The expected y value under the trajectory key.
        timeout (int, optional): The maximum time to wait in seconds.

    Returns:
        bool: True if the expected values are found within the timeout
    """
    start_time = time.time()
    while time.time() - start_time < timeout:
        target_data = device.targetData
        try:
            target_data_dict = json.loads(target_data)
            trajectory = target_data_dict.get("pointing", {}).get(
                "trajectory", {}
            )
            if (
                trajectory.get("attrs", {}).get("x") == expected_x
                and trajectory.get("attrs", {}).get("y") == expected_y
            ):
                return True
        except (json.JSONDecodeError, AttributeError) as e:
            LOGGER.debug("Error reading targetData: %s", e)
        time.sleep(1)

    LOGGER.warning(
        "Timeout after %s  waiting for targetData to contain x=%s, y=%s",
        timeout,
        expected_x,
        expected_y,
    )
    return False
