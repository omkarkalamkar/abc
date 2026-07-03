@HM-972 @SKA_mid
Feature: Delay generation for TLE targets in TMC Mid
	
	Scenario: Generate delay values for a <reference_frame> target
        When I configure the TMC subarray with a <reference_frame> target
        Then CSP Subarray Leaf Node generates delay values for the target
        When I end the observation
        Then CSP Subarray Leaf Node stops generating delay values

        Examples:
            | reference_frame |
            | tle              |
            | altaz            |
            | galactic         |