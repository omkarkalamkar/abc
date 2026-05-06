@XTP-81618 @XTP-28347
Scenario Outline: TMC Behaviour when partial configuration is provided
  Given a TMC
  And TMC SubarrayNode is in Ready ObsState
  When I execute partial configure command with <configuration_data>
  Then the TMC SubarrayNode transitions to obsState READY
  And provided configuration data applied on dish leaf node
  Examples:
   | configuration_data                                   |
   | configuration_with_only_trajectory                   |
   | configuration_with_only_band                         |
   | configuration_with_only_collimation_offsets          |
   | configuration_with_traj_coll_offsets                 |
   | configuration_with_only_wrap_sector                  |
