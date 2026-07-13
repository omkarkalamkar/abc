@XTP-113914 @XTP-28347
Feature: Delay model generation for ADR-63 reference frames in TMC Mid

    Scenario Outline: Generate valid delay model for <reference_frame> target via TMC Mid
        Given a TMC in ON state
        And subarray is in IDLE ObsState
        When I configure the TMC subarray with a pointing group using "<reference_frame>" reference frame
        Then CSP Subarray Leaf Node generates a valid delayModel for the target
        Then I end the observation
        Then CSP Subarray Leaf Node resets the delayModel to default

        Examples:
            | reference_frame |
            | icrs            |
            | tle             |
            | altaz           |
            | galactic        |
            | special         |
