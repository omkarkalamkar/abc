import json
import logging

import pytest
from ska_tango_base.control_model import HealthState, ObsState
from ska_tango_testing.mock.placeholders import Anything

from tests.resources.test_harness.helpers import (
    get_device_simulators,
    prepare_json_args_for_centralnode_commands,
)
from tests.resources.test_harness.utils.enums import CapabilityStates
from tests.resources.test_support.constant import COMMAND_COMPLETED

logging.basicConfig(level=logging.INFO)
LOGGER = logging.getLogger(__name__)


class TestSubarrayHealthState(object):
    """This class implement test cases to verify HealthState
    of Subarray Node.
    This tests implement rows of following excel sheet
    https://docs.google.com/spreadsheets/d/1XbNb8We7fK-EhmOcw3S-h0V_Pu-WAfPTkEd13MSmIns/edit#gid=747888622
    """

    @pytest.mark.batch2
    @pytest.mark.SKA_mid
    def test_health_state_ok(
        self, subarray_node, simulator_factory, event_recorder
    ):
        # Row 1
        (
            csp_sa_sim,
            sdp_sa_sim,
            dish_master_sim_1,
            dish_master_sim_2,
            dish_master_sim_3,
            dish_master_sim_4,
        ) = get_device_simulators(simulator_factory)

        csp_sa_sim.SetDirectHealthState(HealthState.OK)
        sdp_sa_sim.SetDirectHealthState(HealthState.OK)
        dish_master_sim_1.SetDirectHealthState(HealthState.OK)
        dish_master_sim_2.SetDirectHealthState(HealthState.OK)
        dish_master_sim_3.SetDirectHealthState(HealthState.OK)
        dish_master_sim_4.SetDirectHealthState(HealthState.OK)
        event_recorder.subscribe_event(csp_sa_sim, "healthState")
        event_recorder.subscribe_event(sdp_sa_sim, "healthState")
        event_recorder.subscribe_event(dish_master_sim_1, "healthState")
        event_recorder.subscribe_event(dish_master_sim_2, "healthState")
        event_recorder.subscribe_event(dish_master_sim_3, "healthState")
        event_recorder.subscribe_event(dish_master_sim_4, "healthState")

        event_recorder.subscribe_event(
            subarray_node.subarray_node, "healthState"
        )
        assert event_recorder.has_change_event_occurred(
            csp_sa_sim, "healthState", HealthState.OK
        )

        assert event_recorder.has_change_event_occurred(
            sdp_sa_sim, "healthState", HealthState.OK
        )

        assert event_recorder.has_change_event_occurred(
            dish_master_sim_1, "healthState", HealthState.OK
        )

        assert event_recorder.has_change_event_occurred(
            dish_master_sim_2, "healthState", HealthState.OK
        )
        assert event_recorder.has_change_event_occurred(
            dish_master_sim_3, "healthState", HealthState.OK
        )
        assert event_recorder.has_change_event_occurred(
            dish_master_sim_4, "healthState", HealthState.OK
        )

        # Subarray node react automatically
        assert event_recorder.has_change_event_occurred(
            subarray_node.subarray_node,
            "healthState",
            HealthState.OK,
        ), "Expected Subarray Node HealthState to be OK"

    @pytest.mark.parametrize(
        "csp_subarray_health_state, sdp_subarray_health_state, \
        dish_master1_health_state, dish_master2_health_state, \
        dish_master3_health_state, dish_master4_health_state",
        [
            (
                HealthState.FAILED,
                HealthState.FAILED,
                HealthState.OK,
                HealthState.OK,
                HealthState.OK,
                HealthState.OK,
            ),
            (
                HealthState.FAILED,
                HealthState.OK,
                HealthState.OK,
                HealthState.OK,
                HealthState.OK,
                HealthState.OK,
            ),
            (
                HealthState.OK,
                HealthState.FAILED,
                HealthState.OK,
                HealthState.OK,
                HealthState.OK,
                HealthState.OK,
            ),
        ],
    )
    @pytest.mark.batch2
    @pytest.mark.SKA_mid
    def test_health_state_failed_when_csp_or_sdp_failed(
        self,
        subarray_node,
        simulator_factory,
        event_recorder,
        csp_subarray_health_state,
        sdp_subarray_health_state,
        dish_master1_health_state,
        dish_master2_health_state,
        dish_master3_health_state,
        dish_master4_health_state,
    ):
        # Row 2 to 4
        (
            csp_sa_sim,
            sdp_sa_sim,
            dish_master_sim_1,
            dish_master_sim_2,
            dish_master_sim_3,
            dish_master_sim_4,
        ) = get_device_simulators(simulator_factory)

        csp_sa_sim.SetDirectHealthState(csp_subarray_health_state)
        sdp_sa_sim.SetDirectHealthState(sdp_subarray_health_state)
        dish_master_sim_1.SetDirectHealthState(dish_master1_health_state)
        dish_master_sim_2.SetDirectHealthState(dish_master2_health_state)
        dish_master_sim_3.SetDirectHealthState(dish_master3_health_state)
        dish_master_sim_4.SetDirectHealthState(dish_master4_health_state)
        event_recorder.subscribe_event(csp_sa_sim, "healthState")
        event_recorder.subscribe_event(csp_sa_sim, "healthinfo")
        event_recorder.subscribe_event(sdp_sa_sim, "healthState")
        event_recorder.subscribe_event(sdp_sa_sim, "healthinfo")
        event_recorder.subscribe_event(dish_master_sim_1, "healthState")
        event_recorder.subscribe_event(dish_master_sim_2, "healthState")
        event_recorder.subscribe_event(dish_master_sim_3, "healthState")
        event_recorder.subscribe_event(dish_master_sim_4, "healthState")
        event_recorder.subscribe_event(
            subarray_node.subarray_node, "healthState"
        )
        event_recorder.subscribe_event(
            subarray_node.subarray_node,
            "healthinfo",
        )
        assert event_recorder.has_change_event_occurred(
            csp_sa_sim,
            "healthState",
            csp_subarray_health_state,
        )

        assert event_recorder.has_change_event_occurred(
            sdp_sa_sim,
            "healthState",
            sdp_subarray_health_state,
        )

        assert event_recorder.has_change_event_occurred(
            dish_master_sim_1,
            "healthState",
            dish_master1_health_state,
        )

        assert event_recorder.has_change_event_occurred(
            dish_master_sim_2,
            "healthState",
            dish_master2_health_state,
        )

        assert event_recorder.has_change_event_occurred(
            dish_master_sim_3,
            "healthState",
            dish_master3_health_state,
        )
        assert event_recorder.has_change_event_occurred(
            dish_master_sim_4,
            "healthState",
            dish_master4_health_state,
        )

        assert event_recorder.has_change_event_occurred(
            subarray_node.subarray_node,
            "healthState",
            HealthState.FAILED,
        ), "Expected Subarray Node HealthState to be FAILED"
        assert event_recorder.has_change_event_occurred(
            subarray_node.subarray_node,
            "healthinfo",
            Anything,
        ), "Expected Subarray Node HealthState to be FAILED"
        raw_health_info = subarray_node.subarray_node.healthInfo
        LOGGER.info("Raw healthInfo: %s", raw_health_info)
        assert raw_health_info is not None, "healthInfo should not be None"
        parsed = json.loads(raw_health_info)
        LOGGER.info(
            "Formatted healthInfo:\n%s",
            json.dumps(parsed, indent=4),
        )
        if (
            csp_subarray_health_state != HealthState.FAILED
            and sdp_subarray_health_state != HealthState.FAILED
        ):
            assert parsed == [], f"Expected empty healthInfo but got: {parsed}"
        else:
            assert isinstance(
                parsed, dict
            ), f"Expected dict healthInfo when FAILED but got: {parsed}"
            messages = [
                msg
                for value in parsed.values()
                if isinstance(value, list)
                for msg in value
            ]
            assert (
                messages
            ), f"Expected failure messages in healthInfo but got: {parsed}"
            expected_failures = []
            if csp_subarray_health_state == HealthState.FAILED:
                expected_failures.append("CSP Subarray Health State: FAILED")
            if sdp_subarray_health_state == HealthState.FAILED:
                expected_failures.append("SDP Subarray Health State: FAILED")
            for expected_msg in expected_failures:
                assert any(expected_msg in msg for msg in messages), (
                    f"Expected '{expected_msg}' in healthInfo "
                    f"but got: {messages}"
                )

    @pytest.mark.parametrize(
        "csp_subarray_health_state, sdp_subarray_health_state, \
        dish_master1_health_state, dish_master2_health_state, \
        dish_master3_health_state, dish_master4_health_state",
        [
            (
                HealthState.UNKNOWN,
                HealthState.UNKNOWN,
                HealthState.OK,
                HealthState.OK,
                HealthState.OK,
                HealthState.OK,
            ),
            (
                HealthState.UNKNOWN,
                HealthState.OK,
                HealthState.OK,
                HealthState.OK,
                HealthState.OK,
                HealthState.OK,
            ),
            (
                HealthState.OK,
                HealthState.UNKNOWN,
                HealthState.OK,
                HealthState.OK,
                HealthState.OK,
                HealthState.OK,
            ),
        ],
    )
    @pytest.mark.batch2
    @pytest.mark.SKA_mid
    def test_health_state_failed_when_csp_or_sdp_unknown(
        self,
        subarray_node,
        simulator_factory,
        event_recorder,
        csp_subarray_health_state,
        sdp_subarray_health_state,
        dish_master1_health_state,
        dish_master2_health_state,
        dish_master3_health_state,
        dish_master4_health_state,
    ):
        # Row 7 to 9
        (
            csp_sa_sim,
            sdp_sa_sim,
            dish_master_sim_1,
            dish_master_sim_2,
            dish_master_sim_3,
            dish_master_sim_4,
        ) = get_device_simulators(simulator_factory)
        csp_sa_sim.SetDirectHealthState(csp_subarray_health_state)
        sdp_sa_sim.SetDirectHealthState(sdp_subarray_health_state)
        dish_master_sim_1.SetDirectHealthState(dish_master1_health_state)
        dish_master_sim_2.SetDirectHealthState(dish_master2_health_state)
        dish_master_sim_3.SetDirectHealthState(dish_master3_health_state)
        dish_master_sim_4.SetDirectHealthState(dish_master4_health_state)
        event_recorder.subscribe_event(csp_sa_sim, "healthState")
        event_recorder.subscribe_event(sdp_sa_sim, "healthState")
        event_recorder.subscribe_event(dish_master_sim_1, "healthState")
        event_recorder.subscribe_event(dish_master_sim_2, "healthState")
        event_recorder.subscribe_event(dish_master_sim_3, "healthState")
        event_recorder.subscribe_event(dish_master_sim_4, "healthState")
        event_recorder.subscribe_event(
            subarray_node.subarray_node, "healthState"
        )
        assert event_recorder.has_change_event_occurred(
            csp_sa_sim,
            "healthState",
            csp_subarray_health_state,
        )

        assert event_recorder.has_change_event_occurred(
            sdp_sa_sim,
            "healthState",
            sdp_subarray_health_state,
        )

        assert event_recorder.has_change_event_occurred(
            dish_master_sim_1,
            "healthState",
            dish_master1_health_state,
        )

        assert event_recorder.has_change_event_occurred(
            dish_master_sim_2,
            "healthState",
            dish_master2_health_state,
        )
        assert event_recorder.has_change_event_occurred(
            dish_master_sim_3,
            "healthState",
            dish_master3_health_state,
        )
        assert event_recorder.has_change_event_occurred(
            dish_master_sim_4,
            "healthState",
            dish_master4_health_state,
        )

        assert event_recorder.has_change_event_occurred(
            subarray_node.subarray_node,
            "healthState",
            HealthState.UNKNOWN,
        ), "Expected Subarray Node HealthState to be UNKNOWN"

    @pytest.mark.parametrize(
        "csp_subarray_health_state, sdp_subarray_health_state, \
        dish_master1_health_state, dish_master2_health_state, \
        dish_master3_health_state, dish_master4_health_state",
        [
            (
                HealthState.DEGRADED,
                HealthState.DEGRADED,
                HealthState.OK,
                HealthState.OK,
                HealthState.OK,
                HealthState.OK,
            ),
            (
                HealthState.DEGRADED,
                HealthState.OK,
                HealthState.OK,
                HealthState.OK,
                HealthState.OK,
                HealthState.OK,
            ),
            (
                HealthState.OK,
                HealthState.DEGRADED,
                HealthState.OK,
                HealthState.OK,
                HealthState.OK,
                HealthState.OK,
            ),
        ],
    )
    @pytest.mark.batch2
    @pytest.mark.SKA_mid
    def test_health_state_degraded_when_csp_or_sdp_degraded(
        self,
        subarray_node,
        simulator_factory,
        event_recorder,
        csp_subarray_health_state,
        sdp_subarray_health_state,
        dish_master1_health_state,
        dish_master2_health_state,
        dish_master3_health_state,
        dish_master4_health_state,
    ):
        # Row 12 to 14
        (
            csp_sa_sim,
            sdp_sa_sim,
            dish_master_sim_1,
            dish_master_sim_2,
            dish_master_sim_3,
            dish_master_sim_4,
        ) = get_device_simulators(simulator_factory)
        csp_sa_sim.SetDirectHealthState(csp_subarray_health_state)
        sdp_sa_sim.SetDirectHealthState(sdp_subarray_health_state)
        dish_master_sim_1.SetDirectHealthState(dish_master1_health_state)
        dish_master_sim_2.SetDirectHealthState(dish_master2_health_state)
        dish_master_sim_3.SetDirectHealthState(dish_master3_health_state)
        dish_master_sim_4.SetDirectHealthState(dish_master4_health_state)
        event_recorder.subscribe_event(csp_sa_sim, "healthState")
        event_recorder.subscribe_event(sdp_sa_sim, "healthState")
        event_recorder.subscribe_event(dish_master_sim_1, "healthState")
        event_recorder.subscribe_event(dish_master_sim_2, "healthState")
        event_recorder.subscribe_event(dish_master_sim_3, "healthState")
        event_recorder.subscribe_event(dish_master_sim_4, "healthState")
        event_recorder.subscribe_event(
            subarray_node.subarray_node, "healthState"
        )
        assert event_recorder.has_change_event_occurred(
            csp_sa_sim,
            "healthState",
            csp_subarray_health_state,
        )

        assert event_recorder.has_change_event_occurred(
            sdp_sa_sim,
            "healthState",
            sdp_subarray_health_state,
        )

        assert event_recorder.has_change_event_occurred(
            dish_master_sim_1,
            "healthState",
            dish_master1_health_state,
        )

        assert event_recorder.has_change_event_occurred(
            dish_master_sim_2,
            "healthState",
            dish_master2_health_state,
        )
        assert event_recorder.has_change_event_occurred(
            dish_master_sim_3,
            "healthState",
            dish_master3_health_state,
        )
        assert event_recorder.has_change_event_occurred(
            dish_master_sim_4,
            "healthState",
            dish_master4_health_state,
        )
        assert event_recorder.has_change_event_occurred(
            subarray_node.subarray_node,
            "healthState",
            HealthState.DEGRADED,
        ), "Expected Subarray Node HealthState to be DEGRADED"

    @pytest.mark.parametrize(
        "csp_subarray_health_state, sdp_subarray_health_state, \
        dish_master1_health_state, dish_master2_health_state, \
        dish_master3_health_state, dish_master4_health_state",
        [
            (
                HealthState.FAILED,
                HealthState.OK,
                HealthState.OK,
                HealthState.OK,
                HealthState.OK,
                HealthState.OK,
            ),
            (
                HealthState.FAILED,
                HealthState.FAILED,
                HealthState.FAILED,
                HealthState.FAILED,
                HealthState.FAILED,
                HealthState.FAILED,
            ),
        ],
    )
    @pytest.mark.batch2
    @pytest.mark.SKA_mid
    def test_health_state_failed_when_all_dish_failed(
        self,
        subarray_node,
        central_node_mid,
        simulator_factory,
        event_recorder,
        command_input_factory,
        csp_subarray_health_state,
        sdp_subarray_health_state,
        dish_master1_health_state,
        dish_master2_health_state,
        dish_master3_health_state,
        dish_master4_health_state,
    ):
        # Row 5 and 6
        (
            csp_sa_sim,
            sdp_sa_sim,
            dish_master_sim_1,
            dish_master_sim_2,
            dish_master_sim_3,
            dish_master_sim_4,
        ) = get_device_simulators(simulator_factory)

        self._assign_dishes_to_subarray(
            subarray_node,
            central_node_mid,
            command_input_factory,
            event_recorder,
        )
        csp_sa_sim.SetDirectHealthState(csp_subarray_health_state)
        sdp_sa_sim.SetDirectHealthState(sdp_subarray_health_state)
        dish_master_sim_1.SetDirectHealthState(dish_master1_health_state)
        dish_master_sim_2.SetDirectHealthState(dish_master2_health_state)
        dish_master_sim_3.SetDirectHealthState(dish_master3_health_state)
        dish_master_sim_4.SetDirectHealthState(dish_master4_health_state)
        event_recorder.subscribe_event(csp_sa_sim, "healthState")
        event_recorder.subscribe_event(sdp_sa_sim, "healthState")
        event_recorder.subscribe_event(dish_master_sim_1, "healthState")
        event_recorder.subscribe_event(dish_master_sim_2, "healthState")
        event_recorder.subscribe_event(dish_master_sim_3, "healthState")
        event_recorder.subscribe_event(dish_master_sim_4, "healthState")
        event_recorder.subscribe_event(
            subarray_node.subarray_node, "healthState"
        )
        assert event_recorder.has_change_event_occurred(
            csp_sa_sim,
            "healthState",
            csp_subarray_health_state,
        )

        assert event_recorder.has_change_event_occurred(
            sdp_sa_sim,
            "healthState",
            sdp_subarray_health_state,
        )

        assert event_recorder.has_change_event_occurred(
            dish_master_sim_1,
            "healthState",
            dish_master1_health_state,
        )

        assert event_recorder.has_change_event_occurred(
            dish_master_sim_2,
            "healthState",
            dish_master2_health_state,
        )

        assert event_recorder.has_change_event_occurred(
            dish_master_sim_3,
            "healthState",
            dish_master3_health_state,
        )
        assert event_recorder.has_change_event_occurred(
            dish_master_sim_4,
            "healthState",
            dish_master4_health_state,
        )
        assert event_recorder.has_change_event_occurred(
            subarray_node.subarray_node,
            "healthState",
            HealthState.FAILED,
        ), "Expected Subarray Node HealthState to be FAILED"

    @pytest.mark.parametrize(
        "csp_subarray_health_state, sdp_subarray_health_state, \
        dish_master1_health_state, dish_master2_health_state, \
        dish_master3_health_state, dish_master4_health_state",
        [
            (
                HealthState.OK,
                HealthState.OK,
                HealthState.UNKNOWN,
                HealthState.OK,
                HealthState.OK,
                HealthState.OK,
            ),
            (
                HealthState.OK,
                HealthState.OK,
                HealthState.OK,
                HealthState.UNKNOWN,
                HealthState.OK,
                HealthState.OK,
            ),
            (
                HealthState.OK,
                HealthState.OK,
                HealthState.UNKNOWN,
                HealthState.UNKNOWN,
                HealthState.OK,
                HealthState.OK,
            ),
            (
                HealthState.UNKNOWN,
                HealthState.UNKNOWN,
                HealthState.UNKNOWN,
                HealthState.UNKNOWN,
                HealthState.UNKNOWN,
                HealthState.UNKNOWN,
            ),
        ],
    )
    @pytest.mark.batch2
    @pytest.mark.SKA_mid
    def test_health_state_failed_when_dish_unknown(
        self,
        subarray_node,
        central_node_mid,
        simulator_factory,
        event_recorder,
        command_input_factory,
        csp_subarray_health_state,
        sdp_subarray_health_state,
        dish_master1_health_state,
        dish_master2_health_state,
        dish_master3_health_state,
        dish_master4_health_state,
    ):
        # Row 10 and 11
        (
            csp_sa_sim,
            sdp_sa_sim,
            dish_master_sim_1,
            dish_master_sim_2,
            dish_master_sim_3,
            dish_master_sim_4,
        ) = get_device_simulators(simulator_factory)

        self._assign_dishes_to_subarray(
            subarray_node,
            central_node_mid,
            command_input_factory,
            event_recorder,
        )
        pytest.capability_dict = json.dumps(
            {
                "B1": CapabilityStates.STANDBY,
                "B2": CapabilityStates.STANDBY,
                "B3": CapabilityStates.STANDBY,
                "B4": CapabilityStates.STANDBY,
                "B5a": CapabilityStates.STANDBY,
                "B5b": CapabilityStates.STANDBY,
            }
        )
        dish_master_sim_1.SetDirectCapabilityState(pytest.capability_dict)
        dish_master_sim_2.SetDirectCapabilityState(pytest.capability_dict)
        dish_master_sim_3.SetDirectCapabilityState(pytest.capability_dict)
        dish_master_sim_4.SetDirectCapabilityState(pytest.capability_dict)
        csp_sa_sim.SetDirectHealthState(csp_subarray_health_state)
        sdp_sa_sim.SetDirectHealthState(sdp_subarray_health_state)
        dish_master_sim_1.SetDirectHealthState(dish_master1_health_state)
        dish_master_sim_2.SetDirectHealthState(dish_master2_health_state)
        dish_master_sim_3.SetDirectHealthState(dish_master3_health_state)
        dish_master_sim_4.SetDirectHealthState(dish_master4_health_state)
        event_recorder.subscribe_event(csp_sa_sim, "healthState")
        event_recorder.subscribe_event(sdp_sa_sim, "healthState")
        event_recorder.subscribe_event(dish_master_sim_1, "healthState")
        event_recorder.subscribe_event(dish_master_sim_2, "healthState")
        event_recorder.subscribe_event(dish_master_sim_3, "healthState")
        event_recorder.subscribe_event(dish_master_sim_4, "healthState")
        event_recorder.subscribe_event(
            subarray_node.subarray_node, "healthState"
        )
        assert event_recorder.has_change_event_occurred(
            csp_sa_sim,
            "healthState",
            csp_subarray_health_state,
            lookahead=2,
        )

        assert event_recorder.has_change_event_occurred(
            sdp_sa_sim,
            "healthState",
            sdp_subarray_health_state,
            lookahead=2,
        )

        assert event_recorder.has_change_event_occurred(
            dish_master_sim_1,
            "healthState",
            dish_master1_health_state,
            lookahead=2,
        )

        assert event_recorder.has_change_event_occurred(
            dish_master_sim_2,
            "healthState",
            dish_master2_health_state,
            lookahead=2,
        )
        assert event_recorder.has_change_event_occurred(
            dish_master_sim_3,
            "healthState",
            dish_master3_health_state,
            lookahead=2,
        )
        assert event_recorder.has_change_event_occurred(
            dish_master_sim_4,
            "healthState",
            dish_master4_health_state,
            lookahead=2,
        )
        dish_states = [
            dish_master1_health_state,
            dish_master2_health_state,
            dish_master3_health_state,
            dish_master4_health_state,
        ]

        # ---- Expected SA health state logic (OK + UNKNOWN handling) ----
        if (
            csp_subarray_health_state == HealthState.UNKNOWN
            and sdp_subarray_health_state == HealthState.UNKNOWN
            and all(state == HealthState.UNKNOWN for state in dish_states)
        ):
            expected_state = HealthState.UNKNOWN

        elif HealthState.UNKNOWN in dish_states:
            expected_state = HealthState.DEGRADED

        else:
            expected_state = HealthState.OK
        assert event_recorder.has_change_event_occurred(
            subarray_node.subarray_node,
            "healthState",
            expected_state,
            lookahead=10,
        ), "Expected Subarray Node HealthState to be UNKNOWN"

    @pytest.mark.parametrize(
        "csp_subarray_health_state, sdp_subarray_health_state, \
        dish_master1_health_state, dish_master2_health_state, \
        dish_master3_health_state, dish_master4_health_state",
        [
            (
                HealthState.OK,
                HealthState.OK,
                HealthState.FAILED,
                HealthState.OK,
                HealthState.OK,
                HealthState.OK,
            ),
            (
                HealthState.OK,
                HealthState.OK,
                HealthState.OK,
                HealthState.FAILED,
                HealthState.OK,
                HealthState.OK,
            ),
            (
                HealthState.OK,
                HealthState.OK,
                HealthState.DEGRADED,
                HealthState.OK,
                HealthState.OK,
                HealthState.OK,
            ),
            (
                HealthState.OK,
                HealthState.OK,
                HealthState.OK,
                HealthState.DEGRADED,
                HealthState.OK,
                HealthState.OK,
            ),
            (
                HealthState.OK,
                HealthState.OK,
                HealthState.DEGRADED,
                HealthState.DEGRADED,
                HealthState.OK,
                HealthState.OK,
            ),
            (
                HealthState.DEGRADED,
                HealthState.DEGRADED,
                HealthState.DEGRADED,
                HealthState.DEGRADED,
                HealthState.DEGRADED,
                HealthState.DEGRADED,
            ),
        ],
    )
    @pytest.mark.batch2
    @pytest.mark.SKA_mid
    def test_health_state_degraded_when_one_or_more_dish_degraded_or_failed(
        self,
        subarray_node,
        central_node_mid,
        simulator_factory,
        event_recorder,
        command_input_factory,
        csp_subarray_health_state,
        sdp_subarray_health_state,
        dish_master1_health_state,
        dish_master2_health_state,
        dish_master3_health_state,
        dish_master4_health_state,
    ):
        # Row 15 to 17
        (
            csp_sa_sim,
            sdp_sa_sim,
            dish_master_sim_1,
            dish_master_sim_2,
            dish_master_sim_3,
            dish_master_sim_4,
        ) = get_device_simulators(simulator_factory)

        self._assign_dishes_to_subarray(
            subarray_node,
            central_node_mid,
            command_input_factory,
            event_recorder,
        )
        csp_sa_sim.SetDirectHealthState(csp_subarray_health_state)
        sdp_sa_sim.SetDirectHealthState(sdp_subarray_health_state)
        dish_master_sim_1.SetDirectHealthState(dish_master1_health_state)
        dish_master_sim_2.SetDirectHealthState(dish_master2_health_state)
        dish_master_sim_3.SetDirectHealthState(dish_master3_health_state)
        dish_master_sim_4.SetDirectHealthState(dish_master4_health_state)
        event_recorder.subscribe_event(csp_sa_sim, "healthState")
        event_recorder.subscribe_event(sdp_sa_sim, "healthState")
        event_recorder.subscribe_event(dish_master_sim_1, "healthState")
        event_recorder.subscribe_event(dish_master_sim_2, "healthState")
        event_recorder.subscribe_event(dish_master_sim_3, "healthState")
        event_recorder.subscribe_event(dish_master_sim_4, "healthState")
        event_recorder.subscribe_event(
            subarray_node.subarray_node, "healthState"
        )
        assert event_recorder.has_change_event_occurred(
            csp_sa_sim,
            "healthState",
            csp_subarray_health_state,
            lookahead=2,
        )

        assert event_recorder.has_change_event_occurred(
            sdp_sa_sim,
            "healthState",
            sdp_subarray_health_state,
            lookahead=2,
        )

        assert event_recorder.has_change_event_occurred(
            dish_master_sim_1,
            "healthState",
            dish_master1_health_state,
            lookahead=2,
        )

        assert event_recorder.has_change_event_occurred(
            dish_master_sim_2,
            "healthState",
            dish_master2_health_state,
            lookahead=2,
        )
        assert event_recorder.has_change_event_occurred(
            dish_master_sim_3,
            "healthState",
            dish_master3_health_state,
            lookahead=2,
        )
        assert event_recorder.has_change_event_occurred(
            dish_master_sim_4,
            "healthState",
            dish_master4_health_state,
            lookahead=2,
        )

        if (
            dish_master1_health_state == HealthState.DEGRADED
            and dish_master2_health_state == HealthState.DEGRADED
            and dish_master3_health_state == HealthState.DEGRADED
            and dish_master4_health_state == HealthState.DEGRADED
        ):
            assert event_recorder.has_change_event_occurred(
                subarray_node.subarray_node,
                "healthState",
                HealthState.FAILED,
                lookahead=10,
            ), "Expected Subarray Node HealthState to be DEGRADED"
        else:
            assert event_recorder.has_change_event_occurred(
                subarray_node.subarray_node,
                "healthState",
                HealthState.DEGRADED,
                lookahead=10,
            ), "Expected Subarray Node HealthState to be DEGRADED"

    def _assign_dishes_to_subarray(
        self,
        subarray_node,
        central_node_mid,
        command_input_factory,
        event_recorder,
    ):
        event_recorder.subscribe_event(
            central_node_mid.central_node, "longRunningCommandResult"
        )
        event_recorder.subscribe_event(subarray_node.subarray_node, "obsState")
        central_node_mid.move_to_on()
        subarray_id = 1

        assign_input_json = prepare_json_args_for_centralnode_commands(
            "assign_resources_mid", command_input_factory
        )
        assign_input = json.loads(assign_input_json)
        assign_input["subarray_id"] = int(subarray_id)
        command_result = central_node_mid.perform_action(
            "AssignResources", json.dumps(assign_input)
        )
        assert event_recorder.has_change_event_occurred(
            subarray_node.subarray_node, "obsState", ObsState.IDLE
        ), "Waiting for subarray node to complete"
        assert event_recorder.has_change_event_occurred(
            central_node_mid.central_node,
            "longRunningCommandResult",
            (command_result[1][0], COMMAND_COMPLETED),
        )
