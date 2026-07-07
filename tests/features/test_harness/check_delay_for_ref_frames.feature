@HM-972 @SKA_mid @Team_HIMALAYA
Feature: Delay generation for TLE, Alt-Az and Galactic targets in TMC Mid

    Scenario Outline: Generate delay values for different reference frames in TMC Mid
        Given a TMC in ON state with subarray in IDLE ObsState
        When I configure the TMC subarray with a <reference_frame> pointing target
        Then CSP Subarray Leaf Node generates delay values for the target
        When I end the observation
        Then CSP Subarray Leaf Node stops generating delay values

        Examples:
            | reference_frame |
            | tle             |
            | altaz           |
            | galactic        |
