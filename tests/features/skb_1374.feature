@XTP-113246 @XTP-28347
Scenario: TMC Subarray moves to FAULT when track table generation fails on the dish leaf nodes.
    Given a TMC is in IDLE obsState
    When I invoke Configure command on Subarray
    Then Subarray moves to obsState FAULT if track table generation fails else moves to obsState READY