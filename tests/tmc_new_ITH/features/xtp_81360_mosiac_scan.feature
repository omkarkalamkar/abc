@XTP-81360 @XTP-28347
Scenario Outline: TMC Mid execute mosiac scan
	Given TMC Subarray is in observation state IDLE
	And A subarray is configured for a mosaic scan, with <group1> assigned to track a fixed target and <group2> responsible for tracking varying offsets
	And the subarray is in READY obsState
	When I perform partial configurations with <x_offsets> <y_offsets> offsets
	Then the subarray executes the commands successfully and is in READY obsState
	Examples:
		| group1          | group2         | x_offsets        | y_offsets        |
		| SKA001,SKA077   | SKA036,SKA100  | -5.0,5.0         | 5.0,1.0          |