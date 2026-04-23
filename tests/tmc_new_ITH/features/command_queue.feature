Feature: Default

	Scenario: Test command queuing
		Given the subarray is in the EMPTY state
		When I queue AssignResources,Configure and Scan command
        Then the command results of AssignResources,Configure and Scan transitions to OK
		Then the subarray transitions to the READY state
