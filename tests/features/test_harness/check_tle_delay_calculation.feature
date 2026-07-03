@HM-972 @SKA_mid
Feature: Delay generation for TLE targets in TMC Mid
	
	Scenario: CSP Subarray Leaf Node generates delay values for a TLE target
		Given the telescope is in ON state
		And TMC subarray 1 in ObsState IDLE
		When I configure the TMC subarray with a TLE target
		Then CSP Subarray Leaf Node generates delay values for the TLE target
		When I end the observation
		Then CSP Subarray Leaf Node stops generating delay values