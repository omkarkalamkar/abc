@SKA_mid @XTP-108859 @XTP-28347
Scenario Outline: telescopeState should be ON if atleast one dish is available
    Given A TMC
    When I invoke the ON command on the Central Node
    And dishes SKA001, SKA036, SKA063, SKA100 are in dish mode <DishModeSKA001>, <DishModeSKA036>, <DishModeSKA063>, <DishModeSKA100> respectively
    Then telescopeState is in DevState.ON

    Examples:
      | DishModeSKA001 | DishModeSKA036 | DishModeSKA063 | DishModeSKA100 |
      | STANDBY_FP     | STANDBY_FP     | STANDBY_FP     | STANDBY_FP     |
      | STANDBY_FP     | STANDBY_LP     | SHUTDOWN       | SHUTDOWN       |
      | STANDBY_FP     | OPERATE        | CONFIG         | STANDBY_FP     |
      | STANDBY_LP     | OPERATE        | SHUTDOWN       | STANDBY_FP     |
      | STANDBY_LP     | SHUTDOWN       | CONFIG         | STANDBY_FP     |