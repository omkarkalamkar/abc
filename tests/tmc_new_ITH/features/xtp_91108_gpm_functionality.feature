Feature: Apply GPM configuration to dishes via TMC Mid Telescope

  Background:
    Given a TMC Mid telescope is operational
  
  @XTP-91108 @XTP-91105
  Scenario Outline: TMC processes GPM JSON and reports status per dish
    Given the following GPM configurations are provided for version hm-912:
      | Dish_ID | Bands           |
      | SKA001  | Band_1, Band_5a |
      | SKA036  | Band_2          |
      | SKA093  | Band_5b         |
      | SKA077  | Band_1, Band_2  |
    When the GPM configuration is applied via TMC
    Then TMC reports the status as below for the respective dish id:
      | Dish_ID | Status       | Reason                                 |
      | SKA001  | GPM Applied  | not found on gitlab,Exception occurred |
      | SKA036  | GPM Failed   | Dish is assigned to subarray           |
      | SKA093  | GPM Failed   | Dish is unreachable                    |
      | SKA077  | GPM Applied  | Completed                              |