Feature: Test Restart Command during failure of Configure Command

  Scenario Outline: Test Restart Command during failure of Configure Command - Part 1
    Given a TMC
    And the resources are assigned to TMC SubarrayNode
    And the TMC SubarrayNode <subarray_id> Configure is in progress
    And Sdp Subarray <subarray_id> completes Configure
    And Csp Subarray <subarray_id> <csp_obsstate> and goes back to <sdp_obsstate>
    And the TMC SubarrayNode <subarray_id> transitions to FAULT
    When I issue the Restart command on TMC SubarrayNode <subarray_id>
    Then the SDP subarray <subarray_id> transitions to observation state EMPTY
    And the CSP subarray <subarray_id> transitions to observation state EMPTY
    And Dish transitions to dishMode StandbyFP and PointingState READY
    And TMC subarray transitions to observation state EMPTY
    And AssignResources and Configure commands are executed successfully after restart recovery

    Examples:
          | command   | csp_obsstate | sdp_obsstate | dish_pointingstates     | dish_dishmodes                              |
          | Configure | READY        | READY        | READY,READY,READY,READY | CONFIG,CONFIG,CONFIG,CONFIG                 |
          | Configure | CONFIGURING  | READY        | TRACK,TRACK,TRACK,TRACK | OPERATE,OPERATE,OPERATE,OPERATE             |

  Scenario Outline: Test Restart Command during failure of Configure Command - Part 2
    Given a TMC
    And the resources are assigned to TMC SubarrayNode
    And the TMC SubarrayNode <subarray_id> Configure is in progress
    And Csp Subarray <subarray_id> completes Configure
    And Sdp Subarray <subarray_id> raises exception and goes back to obsState IDLE
    And the TMC SubarrayNode <subarray_id> transitions to FAULT
    When I issue the Restart command on TMC SubarrayNode <subarray_id>
    Then the SDP subarray <subarray_id> transitions to observation state EMPTY
    And the CSP subarray <subarray_id> transitions to observation state EMPTY
    And Dish transitions to dishMode StandbyFP and PointingState READY
    And TMC subarray transitions to observation state EMPTY
    And AssignResources and Configure commands are executed successfully after restart recovery

    Examples:
          | command   | csp_obsstate | sdp_obsstate | dish_pointingstates     | dish_dishmodes                              |
          | Configure | READY        | CONFIGURING  | TRACK,TRACK,TRACK,TRACK | OPERATE,OPERATE,OPERATE,OPERATE             |
          | Configure | READY        | IDLE         | TRACK,TRACK,TRACK,TRACK | OPERATE,OPERATE,OPERATE,OPERATE             |