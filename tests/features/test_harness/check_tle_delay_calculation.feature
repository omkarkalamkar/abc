@HM-972 @SKA_mid
Feature: Delay generation for TLE, Alt-az and Galactic targets in TMC Mid

	Scenario Outline: Generate delay values for different reference frames in TMC Mid
		Given the telescope is in ON state
		And TMC subarray 1 in ObsState IDLE
		When I configure the TMC subarray with a <reference_frame> target
		Then CSP Subarray Leaf Node generates delay values for the target
		When I end the observation
		Then CSP Subarray Leaf Node stops generating delay values

		Examples:
			| reference_frame |
			| tle             |
			| altaz           |
			| galactic        |