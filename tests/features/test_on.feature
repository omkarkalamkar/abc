@SKA_mid @XTP-
Scenario: Central Node ON command succeeds when at least one dish is available (in STANDBY_FP)
    Given A TMC
    When I invoke the ON command on the Central Node
    And dishes SKA001, SKA036, SKA063, SKA100 are in dish mode <DishModeSKA001>, <DishModeSKA036>, <DishModeSKA063>, <DishModeSKA100> respectively
    Then telescopeState is in DevState.ON

    Examples:
      | DishModeSKA001 | DishModeSKA036 | DishModeSKA063 | DishModeSKA100 |
      | STANDBY_FP     | STANDBY_FP     | STANDBY_FP     | STANDBY_FP     |
      | STANDBY_FP     | STANDBY_LP     | SHUTDOWN       | STANDBY_FP     |
      | STANDBY_FP     | OPERATE        | CONFIG         | STANDBY_FP     |
      | STANDBY_LP     | OPERATE        | SHUTDOWN       | STANDBY_FP     |
      | STANDBY_LP     | SHUTDOWN       | CONFIG         | STANDBY_FP     |