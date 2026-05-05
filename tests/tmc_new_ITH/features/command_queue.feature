Feature: Default

	#The tests check for command queuing mechanism in TMC MID with help of Mock devices for other subsystems.
	@XTP-108790 @XTP-108789
	Scenario: Test TMC Mid command queuing
		Given the subarray is in the EMPTY state
		When I queue Configure and Scan command
		Then the command results of Configure and Scan transitions to OK
		And the subarray transitions to the READY state