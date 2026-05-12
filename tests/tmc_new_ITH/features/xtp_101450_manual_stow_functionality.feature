Feature: Apply STOW mode to dishes via TMC Mid Telescope

  Background:
    Given a TMC Mid telescope is operational

  @XTP-101450
  Scenario: TMC processes SetStowMode command and reports status per dish
    Given the following dish ids are provided as input to the SetStowMode command:
      | Dish_ID |
      | ska001  |
      | ska036  |
      | ska077  |
      | ska100  |
      | ska064  |
    When the SetStowMode command is invoked via TMC
    Then TMC reports the status as below for the respective dish id:
      | Dish_ID | Status                       | Reason                            |
      | ska001  | DishMode set to Stow         | SetStowMode successfully executed |
      | ska100  | DishMode set to Stow         | SetStowMode successfully executed |
      | ska036  | DishMode set to Stow         | Dish is already in stow mode      |
      | ska064  | Dish is unreachable          | Dish is not allocated to TMC      |
      | ska077  | Timeout has occurred         | Issue in the respective dish      |
    When the SetStowMode command is invoked with "ALL" as an input
    Then TMC invokes SetStowMode on all the dishes

