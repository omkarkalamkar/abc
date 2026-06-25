# Project makefile for a ska-tmc-integration project. You should normally only need to modify
# CAR_OCI_REGISTRY_USER and PROJECT below.
ALARM_HANDLER_FQDN= "alarm/handler/01"
CAR_OCI_REGISTRY_HOST:=artefact.skao.int
PROJECT = ska-tmc-integration
TANGO_HOST ?= tango-databaseds:10000 ## TANGO_HOST connection to the Tango DSI
TANGO_HOST_NAME ?= tango-databaseds
TELESCOPE ?= SKA-mid
DISH_NAMESPACE_1 ?= dish-lmc-1
DISH_NAMESPACE_2 ?= dish-lmc-2
DISH_NAMESPACE_3 ?= dish-lmc-3
DISH_NAMESPACE_4 ?= dish-lmc-4
KUBE_NAMESPACE ?= ska-tmc-integration
KUBE_NAMESPACE_SDP ?= ska-tmc-integration-sdp
K8S_TIMEOUT ?= 800s
PYTHON_LINT_TARGET ?= tests/
DEPLOYMENT_TYPE = $(shell echo $(TELESCOPE) | cut -d '-' -f2)
MARK ?= $(shell echo $(TELESCOPE) | sed "s/-/_/g") ## What -m opt to pass to pytest

# run one test with FILE=acceptance/test_subarray_node.py::test_check_internal_model_according_to_the_tango_ecosystem_deployed
FILE ?= tests## A specific test file to pass to pytest
ADD_ARGS ?= ## Additional args to pass to pytest
FILE_NAME?= alarm_rules.txt

DEPLOY_ALL_DISHES ?= false ## Flag to deploy all dishes or no

CUSTOM_VALUES3 ?=
ifeq ($(strip $(DEPLOY_ALL_DISHES)),true)
CUSTOM_VALUES3 = -f charts/ska-tmc-testing-mid/dish_scaled.yaml
endif
# ----------------------------------------------------------------------------
# Exit at failure flag
#
# The following flag is used to determine whether the test run should exit at
# the first failure or continue running tests after a failure. By default, the
# test run will exit at the first failure. To continue running tests after a
# failure, set the flag to 'false'.

EXIT_AT_FAIL ?= false ## Flag for determining exit at failure.
# Set 'true' to exit at first failure. Set 'false' to continue running
# tests after failure. It defaults to 'true' if not set.
# Actually, any value other than 'false' will be treated as 'true'.

ifneq ($(EXIT_AT_FAIL), false)
ADD_ARGS += -x
endif

# ----------------------------------------------------------------------------

# KUBE_NAMESPACE defines the Kubernetes Namespace that will be deployed to
# using Helm.  If this does not already exist it will be created
ifneq ($(CI_JOB_ID),)
KUBE_NAMESPACE ?= ci-$(CI_PROJECT_NAME)-$(CI_COMMIT_SHORT_SHA)
endif
# HELM_RELEASE is the release that all Kubernetes resources will be labelled
# with
HELM_RELEASE ?= test

# UMBRELLA_CHART_PATH Path of the umbrella chart to work with
HELM_CHART=ska-tmc-testing-$(DEPLOYMENT_TYPE)
UMBRELLA_CHART_PATH ?= charts/$(HELM_CHART)/
K8S_CHARTS ?= ska-tmc-$(DEPLOYMENT_TYPE) ska-tmc-testing-$(DEPLOYMENT_TYPE)## list of charts
K8S_CHART ?= $(HELM_CHART)

DISH_TANGO_HOST ?= tango-databaseds
COUNT ?= 1 ## Number of times the tests should run
CLUSTER_DOMAIN ?= cluster.local
PORT ?= 10000
SUBARRAY_COUNT ?= 1
DISH_NAME_1 ?= tango://$(DISH_TANGO_HOST).$(DISH_NAMESPACE_1).svc.$(CLUSTER_DOMAIN):$(PORT)/mid-dish/dish-manager/SKA001
DISH_NAME_36 ?= tango://$(DISH_TANGO_HOST).$(DISH_NAMESPACE_2).svc.$(CLUSTER_DOMAIN):$(PORT)/mid-dish/dish-manager/SKA036
DISH_NAME_63 ?= tango://$(DISH_TANGO_HOST).$(DISH_NAMESPACE_3).svc.$(CLUSTER_DOMAIN):$(PORT)/mid-dish/dish-manager/SKA063
DISH_NAME_100 ?= tango://$(DISH_TANGO_HOST).$(DISH_NAMESPACE_4).svc.$(CLUSTER_DOMAIN):$(PORT)/mid-dish/dish-manager/SKA100
CSP_MASTER ?= tango://$(TANGO_HOST_NAME).$(KUBE_NAMESPACE).svc.$(CLUSTER_DOMAIN):$(PORT)/mid-csp/control/0
CSP_SUBARRAY_PREFIX ?= tango://$(TANGO_HOST_NAME).$(KUBE_NAMESPACE).svc.$(CLUSTER_DOMAIN):$(PORT)/mid-csp/subarray
SDP_MASTER ?= tango://$(TANGO_HOST_NAME).$(KUBE_NAMESPACE).svc.$(CLUSTER_DOMAIN):$(PORT)/mid-sdp/control/0
SDP_SUBARRAY_PREFIX ?= tango://$(TANGO_HOST_NAME).$(KUBE_NAMESPACE).svc.$(CLUSTER_DOMAIN):$(PORT)/mid-sdp/subarray

CI_REGISTRY ?= gitlab.com

# K8S_TEST_IMAGE_TO_TEST ?= artefact.skao.int/ska-tango-images-tango-itango:9.3.12## docker image that will be run for testing purpose
K8S_TEST_IMAGE_TO_TEST ?= $(CAR_OCI_REGISTRY_HOST)/ska-build-python:0.3.2

TARANTA_ENABLED ?= false

CI_PROJECT_DIR ?= .

XAUTHORITY ?= $(HOME)/.Xauthority
THIS_HOST := $(shell ip a 2> /dev/null | sed -En 's/127.0.0.1//;s/.*inet (addr:)?(([0-9]*\.){3}[0-9]*).*/\2/p' | head -n1)
DISPLAY ?= $(THIS_HOST):0
JIVE ?= false# Enable jive
TARANTA ?= false
MINIKUBE ?= false ## Minikube or not
FAKE_DEVICES ?= false ## Install fake devices or not

ITANGO_DOCKER_IMAGE = $(CAR_OCI_REGISTRY_HOST)/ska-cicd-k8s-tools-build-deploy:0.13.4

# Test runner - run to completion job in K8s
# name of the pod running the k8s_tests
K8S_TEST_RUNNER = test-runner-$(HELM_RELEASE)

CI_PROJECT_PATH_SLUG ?= ska-tmc-integration
CI_ENVIRONMENT_SLUG ?= ska-tmc-integration
CSP_SIMULATION_ENABLED ?= true
SDP_SIMULATION_ENABLED ?= true
DISH_SIMULATION_ENABLED ?= true
SDP_PROCCONTROL_REPLICAS ?= 1

# Set Default Time Out for Leaf nodes
ifeq ($(CI_JOB_ID),)
    # Local builds: Use full production-like timeouts
    SUBARRAY_COMMAND_TIMEOUT ?= 110
    ABORT_COMMAND_TIMEOUT ?= 130
    CSP_SUBARRAY_LEAF_NODE_COMMAND_TIMEOUT ?= 50
    SDP_SUBARRAY_LEAF_NODE_COMMAND_TIMEOUT ?= 50
    DISH_LEAF_NODE_COMMAND_TIMEOUT ?= 90
else
    # CI builds: Use shorter timeouts for faster test execution
    # Tests still verify timeout behavior, just with faster timeouts
    SUBARRAY_COMMAND_TIMEOUT ?= 50
    ABORT_COMMAND_TIMEOUT ?= 70
    CSP_SUBARRAY_LEAF_NODE_COMMAND_TIMEOUT ?= 30
    SDP_SUBARRAY_LEAF_NODE_COMMAND_TIMEOUT ?= 30
    DISH_LEAF_NODE_COMMAND_TIMEOUT ?= 40
endif

ifeq ($(MAKECMDGOALS),k8s-test)
ADD_ARGS +=  --true-context
MARK ?= $(shell echo $(TELESCOPE) | sed "s/-/_/g")

endif

PYTHON_VARS_AFTER_PYTEST ?= -m '$(MARK) $(ADDMARK)' $(ADD_ARGS) $(FILE) --count=$(COUNT) --durations=10
CUSTOM_VALUES1 ?=
CUSTOM_VALUES2 ?=
ifeq ($(CSP_SIMULATION_ENABLED),false)
CUSTOM_VALUES1 =	--set tmc-mid.deviceServers.mocks.csp=$(CSP_SIMULATION_ENABLED)\
	--set ska-csp-lmc-mid.enabled=true
endif

ifeq ($(SDP_SIMULATION_ENABLED),false)
CUSTOM_VALUES2=	--set tmc-mid.deviceServers.mocks.sdp=$(SDP_SIMULATION_ENABLED)\
	--set global.sdp_master="$(SDP_MASTER)"\
	--set global.sdp_subarray_prefix="$(SDP_SUBARRAY_PREFIX)"\
	--set ska-sdp.proccontrol.replicas=$(SDP_PROCCONTROL_REPLICAS)\
	--set global.sdp.processingNamespace=$(KUBE_NAMESPACE_SDP)\
	--set ska-sdp.kafka.clusterDomain=$(CLUSTER_DOMAIN) \
	--set ska-sdp.kafka.zookeeper.clusterDomain=$(CLUSTER_DOMAIN) \
	--set ska-sdp.enabled=true\
	--set ska-sdp.lmc.loadBalancer=true\
	--set tmc-mid.subarray_count=1\
	--set ska-sdp.lmc.nsubarray=1
endif

K8S_CHART_PARAMS = --set global.minikube=$(MINIKUBE) \
	--set global.tango_host=$(TANGO_HOST) \
	--set ska-tango-base.display=$(DISPLAY) \
	--set ska-tango-base.xauthority=$(XAUTHORITY) \
	--set ska-tango-base.jive.enabled=$(JIVE) \
	--set global.exposeAllDS=false \
	--set global.cluster_domain=$(CLUSTER_DOMAIN) \
	--set global.operator=true \
	--set ska-taranta.enabled=$(TARANTA_ENABLED)\
	--set global.namespace_dish.dish_names[0]="$(DISH_NAME_1)"\
	--set global.namespace_dish.dish_names[1]="$(DISH_NAME_36)"\
	--set global.namespace_dish.dish_names[2]="$(DISH_NAME_63)"\
	--set global.namespace_dish.dish_names[3]="$(DISH_NAME_100)"\
	--set tmc-mid.deviceServers.mocks.dish=$(DISH_SIMULATION_ENABLED)\
	--set tmc-mid.subarray_count=$(SUBARRAY_COUNT)\
	--set tmc-mid.deviceServers.subarraynode.CommandTimeOutDefault=$(SUBARRAY_COMMAND_TIMEOUT)\
	--set tmc-mid.deviceServers.subarraynode.AbortCommandTimeOut=$(ABORT_COMMAND_TIMEOUT)\
	--set tmc-mid.deviceServers.sdpsubarrayleafnode.CommandTimeOutDefault=$(SDP_SUBARRAY_LEAF_NODE_COMMAND_TIMEOUT)\
	--set tmc-mid.deviceServers.cspsubarrayleafnode.CommandTimeOutDefault=$(CSP_SUBARRAY_LEAF_NODE_COMMAND_TIMEOUT)\
	--set tmc-mid.deviceServers.dishleafnode.CommandTimeOutDefault=$(DISH_LEAF_NODE_COMMAND_TIMEOUT)\
	$(CUSTOM_VALUES1)\
	$(CUSTOM_VALUES2)\
	$(CUSTOM_VALUES3)

PYTHON_VARS_BEFORE_PYTEST ?= PYTHONPATH=.:./src \
							 TANGO_HOST=$(TANGO_HOST) \
							 TELESCOPE=$(TELESCOPE) \
							 CLUSTER_DOMAIN=$(CLUSTER_DOMAIN) \
							 CSP_SIMULATION_ENABLED=$(CSP_SIMULATION_ENABLED) \
							 SDP_SIMULATION_ENABLED=$(SDP_SIMULATION_ENABLED) \
							 DISH_SIMULATION_ENABLED=$(DISH_SIMULATION_ENABLED) \
							 DISH_NAMESPACE_1=$(DISH_NAMESPACE_1) \
							 DISH_NAMESPACE_2=$(DISH_NAMESPACE_2) \
							 DISH_NAMESPACE_3=$(DISH_NAMESPACE_3) \
							 DISH_NAMESPACE_4=$(DISH_NAMESPACE_4) \
							 DISH_NAME_1=$(DISH_NAME_1) \
							 DISH_NAME_36=$(DISH_NAME_36) \
							 DISH_NAME_63=$(DISH_NAME_63) \
							 DISH_NAME_100=$(DISH_NAME_100) \
							 KUBE_NAMESPACE=$(KUBE_NAMESPACE) \
							 KUBE_NAMESPACE_SDP=$(KUBE_NAMESPACE_SDP)

K8S_TEST_TEST_COMMAND ?= $(PYTHON_VARS_BEFORE_PYTEST) $(PYTHON_RUNNER) \
						pytest \
						$(PYTHON_VARS_AFTER_PYTEST) ./tests \
						| tee pytest.stdout # k8s-test test command to run in container

-include .make/base.mk
-include .make/k8s.mk
-include .make/helm.mk
-include .make/python.mk
-include .make/oci.mk
-include .make/xray.mk
-include PrivateRules.mak
-include resources/alarmhandler.mk

# to create SDP namespace
k8s-pre-install-chart:
ifeq ($(SDP_SIMULATION_ENABLED),false)
	@echo "k8s-pre-install-chart: creating the SDP namespace $(KUBE_NAMESPACE_SDP)"
	@make k8s-namespace KUBE_NAMESPACE=$(KUBE_NAMESPACE_SDP)
endif

# to create SDP namespace
k8s-pre-install-chart-car:
ifeq ($(SDP_SIMULATION_ENABLED),false)
	@echo "k8s-pre-install-chart-car: creating the SDP namespace $(KUBE_NAMESPACE_SDP)"
	@make k8s-namespace KUBE_NAMESPACE=$(KUBE_NAMESPACE_SDP)
endif

# to delete SDP namespace
k8s-post-uninstall-chart:
ifeq ($(SDP_SIMULATION_ENABLED),false)
	@echo "k8s-post-uninstall-chart: deleting the SDP namespace $(KUBE_NAMESPACE_SDP)"
	@make k8s-delete-namespace KUBE_NAMESPACE=$(KUBE_NAMESPACE_SDP)
endif

taranta-link:
	@echo "#            https://k8s.stfc.skao.int/$(KUBE_NAMESPACE)/taranta/dashboard"

alarm-handler-configurator-link:
	@echo "#            https://k8s.stfc.skao.int/$(KUBE_NAMESPACE)/alarm-handler/"


cred:
	make k8s-namespace
	curl -s https://gitlab.com/ska-telescope/templates-repository/-/raw/master/scripts/namespace_auth.sh | bash -s $(SERVICE_ACCOUNT) $(KUBE_NAMESPACE) || true


test-requirements:
	@poetry export --without-hashes --with dev --format requirements.txt --output tests/requirements.txt

k8s-pre-test: test-requirements

# ----------------------------------------------------------------------------
# Trick to select a subset of the tests to run by their python name
# Very useful when debugging a single test
#
# Example:
# make k8s-test MARK=tmc PYTHON_TEST_NAME="abort"
# # Expected result: among all the tests with "tmc" as a marker,
# #  			  only the ones with "abort" in their name will be run.

PYTHON_TEST_NAME ?= ## -k parameter for pytest

ifneq ($(PYTHON_TEST_NAME),)
PYTHON_VARS_AFTER_PYTEST += -k '$(PYTHON_TEST_NAME)'
endif


# ----------------------------------------------------------------------------
# test results files
# (The following variables are used to generate the various test results files
# i.e., cucumber.json, report.json, and report.html)
#
# report.html is used to generate the BDD test report by the pytest-bdd-report
# plugin. The plugin generates a BDD test report in HTML format, that will
# then be published in the artifacts and that will be linked in the
# Jira ticket of the test execution.

# target file names for the cucumber-related test results json files
CUCUMBER_JSON_RESULT_FILE ?= build/cucumber.json
REPORT_JSON_RESULT_FILE ?= build/report.json
XRAY_TEST_RESULT_FILE ?= build/cucumber.json

# configuration file for ska-ser-xray to publish the test results to Jira
XRAY_EXECUTION_CONFIG_FILE ?= tests/xray-config.json

# target file name for the BDD test report in HTML format
# Leave or set to empty to disable the HTML BDD test report generation
HTML_REPORT_TARGET_FILE ?= build/report.html


# ----------------------------------------------------------------------------
# Add all the flags needed to generate the test results files

# Add BDD report output
PYTHON_VARS_AFTER_PYTEST += \
	--cucumberjson="$(CUCUMBER_JSON_RESULT_FILE)" \
	--json-report \
	--json-report-file="$(REPORT_JSON_RESULT_FILE)"

# Add BDD HTML test report (if enabled)
ifneq ($(strip $(HTML_REPORT_TARGET_FILE)),)
PYTHON_VARS_AFTER_PYTEST += --bdd-report="$(HTML_REPORT_TARGET_FILE)"
endif


# ----------------------------------------------------------------------------
# Publish the BDD HTML test report to the just published
# Jira test execution issue

## General flag to enable/disable the publishing of the BDD HTML test report
# to the Jira test execution issue.
# Set to any value other than "true" to disable it
ENRICH_TEST_EXECUTIONS ?= true
ENRICH_TEST_EXECUTIONS_PARAMS ?=

## Jira configurations for publishing the BDD HTML test report to Jira
JIRA_URL ?= https://jira.skatelescope.org
JIRA_PROJECT_KEY ?= XTP

ENRICH_TEST_EXECUTIONS_PARAMS += --jira-url="$(strip $(JIRA_URL))" \
	--project-key="$(strip $(JIRA_PROJECT_KEY))" \
	--ci-job-id="$(CI_JOB_ID)" --commit-sha="$(CI_COMMIT_SHA)" \
	--html-report="$(strip $(HTML_REPORT_TARGET_FILE))"

# NOTE: we assume CI_JOB_ID and CI_COMMIT_SHA are available in the environment

## Flag to set to "true" if you want to add also a link to the
# BDD test documentation in the Jira test execution issue
# (Set to false to disable the link to the BDD test documentation
# in the Jira test execution issue)
ADD_DOCS_LINK_TO_JIRA ?= false
## The folder where the documentation will be generated
STEP_DOCUMENTATION_OUTPUT_FOLDER ?= tests/tmc_csp_new_ITH/bdd-steps-doc

ifeq ($(ADD_DOCS_LINK_TO_JIRA), true)
ENRICH_TEST_EXECUTIONS_PARAMS += --test-docs="$(strip $(STEP_DOCUMENTATION_OUTPUT_FOLDER))"
endif


## After the test run and the Test Execution Jira ticket is created,
# if the HTML report is enabled and
# the script to publish the HTML report to Jira is available,
# then publish a link to the HTML report to Jira
# xray-post-publish:
# 	if [ -f "$(HTML_REPORT_TARGET_FILE)" ] && [ "$(strip $(ENRICH_TEST_EXECUTIONS))" == "true" ]; then \
# 		echo "Publishing the BDD HTML test report to the Jira test execution issue"; \
# 		xray-enrich-test-execution $(ENRICH_TEST_EXECUTIONS_PARAMS); \
# 	fi;

# ----------------------------------------------------------------------------
# Further customisations of the test command args

# Verbose error tracebacks (for now, only for new ITH tests)
# and also link to test documentation
ifeq ($(strip $(MARK)),tmc_csp_new_ITH)
PYTHON_VARS_AFTER_PYTEST += -v --tb=long --log-cli-level=INFO
endif
