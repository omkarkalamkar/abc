@XTP-113487 @XTP-113486
Scenario: TMC loaddishcfg fails on failure on all dishes
        Given a TMC
        And CSP Controller is in OFF state
        And All the dishes set to throw exception
        When I issue the command LoadDishCfg on TMC with Dish and VCC configuration file
        Then TMC fails to set the Dish-VCC map

@XTP-113488 @XTP-113486
Scenario: TMC allows partial success for LoadDishCfg and blocks further commands on device state and kValue issues
    Given a TMC with CSP Controller in OFF state and one functional dish out of allocated dishes
    When I issue LoadDishCfg with Dish and VCC configuration file
    Then LoadDishCfg completes with partial success
    And TMC does not allow LoadDishCfg in any ObsState as CSP Controller is ON
    And TMC does not allow AssignResources as kValue issue on dish

