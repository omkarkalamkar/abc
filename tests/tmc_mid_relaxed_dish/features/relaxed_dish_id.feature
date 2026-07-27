Feature: Deploy and test TMC mid with relaxed dish ids

	@relaxed_dish_id
	Scenario: TMC mid deploys dishes with ids beyond 197
		Given a TMC mid deployment configured with relaxed dish ids
		When I query the TMC central node and the dish leaf nodes
		Then the dish leaf nodes for dish ids beyond 197 are deployed and reachable
		And the central node reports the relaxed dish ids in its DishIDs property