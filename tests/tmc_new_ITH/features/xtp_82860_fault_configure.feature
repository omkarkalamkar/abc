#This test covers scenarios of Restart command flow when Configure command fails and TMC Subarray transitions to FAULT observation state.
@XTP-82860 @XTP-82747 @TEAM_HIMALAYA
Scenario Outline: Test Restart Command during failure of Configure Command - Part 1
    Given CSP, SDP and DISH in <csp_obsstate>,<sdp_obsstate>,<dish_pointingstates> and <dish_dishmodes> after <command>
    And TMC Subarray in observation state FAULT
    When I invoke Restart Command on the TMC Subarray
    Then CSP and SDP transitions to observation state EMPTY
    And Dish transitions to dishMode StandbyFP and PointingState READY
    And TMC subarray transitions to observation state EMPTY
    Examples:
          | command   | csp_obsstate | sdp_obsstate | dish_pointingstates     | dish_dishmodes                              |
          | Configure | READY        | READY        | READY,READY,READY,READY | CONFIG,CONFIG,CONFIG,CONFIG                 |
          | Configure | READY        | READY        | TRACK,READY,TRACK,READY | OPERATE,CONFIG,OPERATE,CONFIG               |
          | Configure | READY        | READY        | READY,TRACK,READY,READY | CONFIG,OPERATE,CONFIG,CONFIG                |
          | Configure | READY        | READY        | TRACK,TRACK,TRACK,READY | OPERATE,OPERATE,OPERATE,CONFIG              |
          | Configure | FAULT        | READY        | TRACK,TRACK,READY,READY | OPERATE,OPERATE,STANDBY_FP,STANDBY_FP       |
          | Configure | FAULT        | READY        | READY,READY,TRACK,TRACK | STANDBY_FP,STANDBY_FP,OPERATE,OPERATE       |
          | Configure | FAULT        | READY        | SLEW,TRACK,TRACK,SLEW   | STANDBY_FP,OPERATE,OPERATE,STANDBY_FP       |
          | Configure | FAULT        | READY        | TRACK,READY,READY,TRACK | OPERATE,STANDBY_FP,STANDBY_FP,OPERATE       |
          | Configure | FAULT        | READY        | READY,TRACK,TRACK,TRACK | STANDBY_FP,OPERATE,OPERATE,OPERATE          |
          | Configure | FAULT        | CONFIGURING  | TRACK,READY,TRACK,TRACK | OPERATE,STANDBY_FP,OPERATE,OPERATE          |
          | Configure | FAULT        | CONFIGURING  | TRACK,TRACK,TRACK,TRACK | OPERATE,OPERATE,OPERATE,OPERATE             |
          | Configure | FAULT        | CONFIGURING  | TRACK,SLEW,SLEW,TRACK   | OPERATE,STANDBY_FP,STANDBY_FP,OPERATE       |
          | Configure | FAULT        | CONFIGURING  | TRACK,TRACK,TRACK,TRACK | OPERATE,OPERATE,OPERATE,OPERATE             |
          | Configure | FAULT        | CONFIGURING  | TRACK,TRACK,TRACK,TRACK | OPERATE,OPERATE,OPERATE,OPERATE             |
          | Configure | READY        | FAULT        | TRACK,TRACK,TRACK,TRACK | OPERATE,OPERATE,OPERATE,OPERATE             |
          | Configure | READY        | FAULT        | TRACK,TRACK,TRACK,TRACK | OPERATE,OPERATE,OPERATE,OPERATE             |
          | Configure | READY        | FAULT        | SLEW,TRACK,TRACK,TRACK  | STANDBY_FP,OPERATE,OPERATE,OPERATE          |
          | Configure | READY        | FAULT        | TRACK,TRACK,TRACK,TRACK | OPERATE,OPERATE,OPERATE,OPERATE             |
          | Configure | READY        | FAULT        | TRACK,READY,TRACK,TRACK | OPERATE,STANDBY_FP,OPERATE,OPERATE          |
          | Configure | CONFIGURING  | FAULT        | TRACK,TRACK,TRACK,TRACK | OPERATE,OPERATE,OPERATE,OPERATE             |
          | Configure | CONFIGURING  | FAULT        | TRACK,TRACK,TRACK,TRACK | OPERATE,OPERATE,OPERATE,OPERATE             |
          | Configure | CONFIGURING  | FAULT        | TRACK,TRACK,TRACK,TRACK | OPERATE,OPERATE,OPERATE,OPERATE             |
          | Configure | CONFIGURING  | FAULT        | TRACK,TRACK,TRACK,TRACK | OPERATE,OPERATE,OPERATE,OPERATE             |
          | Configure | CONFIGURING  | FAULT        | TRACK,TRACK,TRACK,READY | OPERATE,OPERATE,OPERATE,STANDBY_FP          |

@XTP-82860 @XTP-82747 @TEAM_HIMALAYA
Scenario Outline: Test Restart Command during failure of Configure Command - Part 2
    Given CSP, SDP and DISH in <csp_obsstate>,<sdp_obsstate>,<dish_pointingstates> and <dish_dishmodes> after <command>
    And TMC Subarray in observation state FAULT
    When I invoke Restart Command on the TMC Subarray
    Then CSP and SDP transitions to observation state EMPTY
    And Dish transitions to dishMode StandbyFP and PointingState READY
    And TMC subarray transitions to observation state EMPTY
    Examples:
          | command   | csp_obsstate | sdp_obsstate | dish_pointingstates     | dish_dishmodes                              |
          | Configure | CONFIGURING  | READY        | TRACK,TRACK,TRACK,TRACK | OPERATE,OPERATE,OPERATE,OPERATE             |
          | Configure | CONFIGURING  | READY        | READY,READY,READY,READY | STANDBY_FP,STANDBY_FP,STANDBY_FP,STANDBY_FP |
          | Configure | CONFIGURING  | READY        | TRACK,TRACK,TRACK,TRACK | OPERATE,OPERATE,OPERATE,OPERATE             |
          | Configure | CONFIGURING  | READY        | SLEW,SLEW,SLEW,SLEW     | STANDBY_FP,STANDBY_FP,STANDBY_FP,STANDBY_FP |
          | Configure | CONFIGURING  | READY        | TRACK,TRACK,TRACK,TRACK | OPERATE,OPERATE,OPERATE,OPERATE             |
          | Configure | CONFIGURING  | CONFIGURING  | TRACK,TRACK,TRACK,TRACK | OPERATE,OPERATE,OPERATE,OPERATE             |
          | Configure | CONFIGURING  | CONFIGURING  | TRACK,TRACK,TRACK,TRACK | OPERATE,OPERATE,OPERATE,OPERATE             |
          | Configure | CONFIGURING  | CONFIGURING  | TRACK,TRACK,TRACK,TRACK | OPERATE,OPERATE,OPERATE,OPERATE             |
          | Configure | CONFIGURING  | CONFIGURING  | TRACK,TRACK,TRACK,TRACK | OPERATE,OPERATE,OPERATE,OPERATE             |
          | Configure | CONFIGURING  | CONFIGURING  | TRACK,TRACK,TRACK,TRACK | OPERATE,OPERATE,OPERATE,OPERATE             |
          | Configure | READY        | CONFIGURING  | TRACK,TRACK,TRACK,TRACK | OPERATE,OPERATE,OPERATE,OPERATE             |
          | Configure | READY        | CONFIGURING  | TRACK,TRACK,TRACK,TRACK | OPERATE,OPERATE,OPERATE,OPERATE             |
          | Configure | READY        | CONFIGURING  | TRACK,TRACK,TRACK,TRACK | OPERATE,OPERATE,OPERATE,OPERATE             |
          | Configure | READY        | CONFIGURING  | TRACK,TRACK,TRACK,TRACK | OPERATE,OPERATE,OPERATE,OPERATE             |
          | Configure | READY        | CONFIGURING  | TRACK,TRACK,TRACK,TRACK | OPERATE,OPERATE,OPERATE,OPERATE             |
          | Configure | READY        | READY        | SLEW,TRACK,TRACK,TRACK  | STANDBY_FP,OPERATE,OPERATE,OPERATE          |
          | End       | FAULT        | IDLE         | READY,READY,READY,READY | OPERATE,OPERATE,OPERATE,OPERATE             |
          | End       | IDLE         | FAULT        | READY,READY,READY,READY | OPERATE,OPERATE,OPERATE,OPERATE             |
          | End       | IDLE         | IDLE         | TRACK,READY,TRACK,TRACK | OPERATE,OPERATE,OPERATE,OPERATE             |
          | End       | IDLE         | IDLE         | TRACK,SLEW,TRACK,TRACK  | OPERATE,OPERATE,OPERATE,OPERATE             |
          | End       | IDLE         | FAULT        | TRACK,TRACK,TRACK,TRACK | OPERATE,OPERATE,OPERATE,OPERATE             |
          | End       | FAULT        | FAULT        | READY,READY,READY,READY | OPERATE,OPERATE,OPERATE,OPERATE             |
          | End       | FAULT        | IDLE         | READY,READY,READY,READY | OPERATE,OPERATE,OPERATE,OPERATE             |





