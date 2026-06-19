import pytest
from pytest_bdd import given, parsers, scenario, then, when
from ska_tango_base.control_model import HealthState

from tests.resources.test_harness.helpers import (
    get_device_simulator_with_given_name,
    get_master_device_simulators,
    set_desired_health_state,
)


@pytest.mark.test
@pytest.mark.SKA_mid
@scenario(
    "../features/test_harness/telescope_health_state_aggregation.feature",
    "Verify CentralNode TelescopeHealthState",
)
def test_telescope_health_state():
    """
    Test case to verify aggregation for CentralNode telescopeHealthState
    """


@given("csp master, sdp master and dish masters health state is OK")
def simulator_devices_health_state_is_ok(simulator_factory, event_recorder):
    """A method to check simulator devices are in HealthState.OK

    Args:
        simulator_factory: fixture for SimulatorFactory class,
        which provides simulated subarray and master devices
        event_recorder: fixture for EventRecorder class
    """
    (
        csp_master_sim,
        sdp_master_sim,
        dish_master_sim_1,
        dish_master_sim_2,
        dish_master_sim_3,
        dish_master_sim_4,
        dish_master_sim_5,
        dish_master_sim_6,
    ) = get_master_device_simulators(simulator_factory)

    set_desired_health_state(
        sim_devices_list=[
            csp_master_sim,
            sdp_master_sim,
            dish_master_sim_1,
            dish_master_sim_2,
            dish_master_sim_3,
            dish_master_sim_4,
            dish_master_sim_5,
            dish_master_sim_6,
        ],
        health_state_value=HealthState.OK,
    )

    event_recorder.subscribe_event(csp_master_sim, "healthState")
    event_recorder.subscribe_event(sdp_master_sim, "healthState")
    event_recorder.subscribe_event(dish_master_sim_1, "healthState")
    event_recorder.subscribe_event(dish_master_sim_2, "healthState")
    event_recorder.subscribe_event(dish_master_sim_3, "healthState")
    event_recorder.subscribe_event(dish_master_sim_4, "healthState")
    event_recorder.subscribe_event(dish_master_sim_5, "healthState")
    event_recorder.subscribe_event(dish_master_sim_6, "healthState")
    assert event_recorder.has_change_event_occurred(
        csp_master_sim, "healthState", HealthState.OK
    ), "Expected HealthState to be OK"
    assert event_recorder.has_change_event_occurred(
        sdp_master_sim, "healthState", HealthState.OK
    ), "Expected HealthState to be OK"
    assert event_recorder.has_change_event_occurred(
        dish_master_sim_1, "healthState", HealthState.OK
    ), "Expected HealthState to be OK"
    assert event_recorder.has_change_event_occurred(
        dish_master_sim_2, "healthState", HealthState.OK
    ), "Expected HealthState to be OK"
    assert event_recorder.has_change_event_occurred(
        dish_master_sim_3, "healthState", HealthState.OK
    ), "Expected HealthState to be OK"
    assert event_recorder.has_change_event_occurred(
        dish_master_sim_4, "healthState", HealthState.OK
    ), "Expected HealthState to be OK"
    assert event_recorder.has_change_event_occurred(
        dish_master_sim_5, "healthState", HealthState.OK
    ), "Expected HealthState to be OK"
    assert event_recorder.has_change_event_occurred(
        dish_master_sim_6, "healthState", HealthState.OK
    ), "Expected HealthState to be OK"


@when(parsers.parse("The {devices} health state changes to {health_state}"))
def set_simulator_devices_health_states(
    simulator_factory, devices, health_state
):
    """A method to set HealthState value for the simulator devices

    Args:
        simulator_factory: fixture for SimulatorFactory class,
        which provides simulated subarray and master devices
        devices (str): simulator devices
        health_state (str): healthstate value
    """
    devices_list = devices.split(",")
    health_state_list = health_state.split(",")

    sim_devices_list = get_device_simulator_with_given_name(
        simulator_factory, devices_list
    )
    for sim_device, sim_health_state_val in list(
        zip(sim_devices_list, health_state_list)
    ):
        sim_device.SetDirectHealthState(HealthState[sim_health_state_val])


@then(parsers.parse("the telescope health state is {telescope_health_state}"))
def check_telescope_health_state(
    central_node_mid, event_recorder, telescope_health_state
):
    """A method to check CentralNode.telescopehealthState attribute
    change after aggregation

    Args:
        central_node_mid : A fixture for CentralNode tango device class
        event_recorder: A fixture for EventRecorder class_
        telescope_health_state (str): telescopehealthState value
    """
    event_recorder.subscribe_event(
        central_node_mid.central_node, "telescopeHealthState"
    )

    assert event_recorder.has_change_event_occurred(
        central_node_mid.central_node,
        "telescopeHealthState",
        HealthState[telescope_health_state],
    ), f"Expected telescopeHealthState to be \
        {HealthState[telescope_health_state]}"
