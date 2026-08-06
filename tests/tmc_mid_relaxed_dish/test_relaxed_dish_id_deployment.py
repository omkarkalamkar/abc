"""Tests for deploying and validating TMC mid with relaxed dish ids.

These tests exercise the "relaxed" dish id range (dish ids beyond 197, i.e.
up to ``SkaDishIdUpperLimit`` = 999). They are deployment level checks that do
not depend on the integration test harness, since the harness is configured
only for the standard set of dishes.
"""

import pytest
import tango
from assertpy import assert_that
from pytest_bdd import given, scenario, then, when

from tests.conftest import LOGGER
from tests.resources.test_support.constant import (
    centralnode,
    dish_leaf_node_prefix,
)

# Dish ids that lie beyond the previous limit of 197 (relaxed dish ids).
RELAXED_DISH_IDS = ["SKA198", "SKA500", "SKA999"]


@pytest.mark.relaxed_dish_id
@pytest.mark.SKA_mid
@scenario(
    "../tmc_mid_relaxed_dish/features/relaxed_dish_id.feature",
    "TMC mid deploys dishes with ids beyond 197",
)
def test_relaxed_dish_id_deployment():
    """Validate TMC mid deploys and recognises dish ids beyond 197."""


@given("a TMC mid deployment configured with relaxed dish ids")
def given_relaxed_dish_deployment():
    """The deployment is created by the CI job with dish_relaxed.yaml."""
    central_node = tango.DeviceProxy(centralnode)
    assert_that(central_node.ping()).described_as(
        "The TMC central node should be reachable."
    ).is_greater_than(0)


@when("I query the TMC central node and the dish leaf nodes")
def when_query_devices():
    """No explicit action needed; assertions are performed in Then steps."""


@then("the dish leaf nodes for dish ids beyond 197 are deployed and reachable")
def then_relaxed_dish_leaf_nodes_reachable():
    """Every relaxed dish id has a reachable dish leaf node device."""
    for dish_id in RELAXED_DISH_IDS:
        dln_fqdn = f"{dish_leaf_node_prefix}{dish_id.lower()}"
        LOGGER.info("Checking dish leaf node %s", dln_fqdn)
        dish_leaf_node = tango.DeviceProxy(dln_fqdn)
        assert_that(dish_leaf_node.ping()).described_as(
            f"Dish leaf node {dln_fqdn} should be reachable."
        ).is_greater_than(0)
        assert_that(dish_leaf_node.state()).described_as(
            f"Dish leaf node {dln_fqdn} should not be in FAULT state."
        ).is_not_equal_to(tango.DevState.FAULT)


@then("the central node reports the relaxed dish ids in its DishIDs property")
def then_central_node_reports_relaxed_dish_ids():
    """The central node DishIDs property contains the relaxed dish ids."""
    database = tango.Database()
    configured_dish_ids = database.get_device_property(
        centralnode, "DishIDs"
    )["DishIDs"]
    LOGGER.info("Central node DishIDs: %s", list(configured_dish_ids))
    for dish_id in RELAXED_DISH_IDS:
        assert_that(list(configured_dish_ids)).described_as(
            f"Central node DishIDs should contain relaxed dish id {dish_id}."
        ).contains(dish_id)
