
@Team_SAHYADRI @XTP-64365 @XTP-28347 @SKA_mid
Scenario: TMC mid executes Abort command on DISH with pointingState SLEW
    Given TMC subarray <subarray_id> with <dish_ids> is in obsState CONFIGURING
    And DishMaster <dish_ids> is in dishMode OPERATE with pointingState SLEW
    When I issue the Abort command to the TMC subarray <subarray_id>
    Then the Dish <dish_ids> transitions to dishMode STANDBY_FP and pointingState READY
    And TMC SubarrayNode transitions to obsState ABORTED
    Examples:

        | subarray_id | dish_ids                       |
        | 1           | SKA001,SKA036,SKA077,SKA100    |