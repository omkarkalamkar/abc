@SKA_mid @XTP-106734 @XTP-106735 @TEAM_HIMALAYA
Scenario Outline: Test Configure command to verify Mattieu Pattern
    Given the TMC is On
    And the subarray is in IDLE obsState
    When the command configure is issued with position velocity <input_json1>
    Then the subarray transitions to obsState READY
    And TMC is able to generate track table entries
    Examples:
    | input_json1                     |
    | pvt_pattern_configure           |