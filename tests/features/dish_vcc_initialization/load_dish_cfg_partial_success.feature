Scenario Outline: TMC loaddishcfg fails on failure on all dishes
        Given a TMC
        And CSP Controller is in OFF state
        And All the dishes set to throw exception
        When I issue the command LoadDishCfg on TMC with Dish and VCC configuration file
        Then TMC fails to set the Dish-VCC map

Scenario Outline: TMC allows partial success for load Dish and VCC configuration file
        Given a TMC
        And CSP Controller is in OFF state
        And one dish is working as expected out of allocated dishes
        When I issue the command LoadDishCfg on TMC with Dish and VCC configuration file
        Then TMC loaddishcfg gets succeed partially
        When I try to invoke loaddishcfg in obsstate empty
        Then TMC not allow loaddishcfg as CSP controller is in ON state
        When TMC detects kValue issue on any of the dish
        Then TMC rejects the assign resources command.

