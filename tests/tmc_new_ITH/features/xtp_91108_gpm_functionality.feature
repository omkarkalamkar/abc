Feature: Apply GPM configuration to dishes via TMC Mid Telescope

  Background:
    Given a TMC Mid telescope is operational
  
  @XTP-91108 @XTP-91105
  Scenario Outline: TMC processes GPM JSON and reports status per dish
    Given the following GPM configurations are provided for version 1.1.3:
      | Dish_ID | Bands           |
      | SKA001  | Band_1, Band_5a |
      | SKA036  | Band_2          |
      | SKA093  | Band_5b         |
      | SKA063  | Band_4, Band_3  |
    When the GPM configuration is applied via TMC
    Then TMC reports the status as below for the respective dish id:
      | Dish_ID | Status       | Reason                                 |
      | SKA001  | GPM Applied  | Completed                              |
      | SKA036  | GPM Failed   | Dish is assigned to subarray           |
      | SKA093  | GPM Failed   | Dish is unreachable                    |
      | SKA063  | GPM Failed   | not found on gitlab,Exception occurred |