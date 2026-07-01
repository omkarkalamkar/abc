Scenario Outline: TMC allows partial success for load Dish and VCC configuration file  
        Given a TMC
        And CSP Controller is in OFF state
        And All the dishes set to throw exception
        When I issue the command LoadDishCfg on TMC with Dish and VCC configuration file   
        Then TMC fails to set the Dish-VCC map 