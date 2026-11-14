from app.planner import MissionConstraints, MultiObjectiveAStar, build_route_set, route_metrics
from app.terrain import generate_terrain


def test_route_stays_inside_grid_and_avoids_hard_blocked_cells():
    terrain = generate_terrain(seed=11)
    constraints = MissionConstraints(max_slope_deg=35, max_temperature_c=0)
    result = MultiObjectiveAStar(terrain, constraints, "balanced").search((3, 3), (58, 58))
    assert result["path"][0] == (3, 3)
    assert result["path"][-1] == (58, 58)
    for x, y in result["path"]:
        assert not terrain.is_blocked(x, y, constraints.max_slope_deg, constraints.max_temperature_c)


def test_three_policy_routes_are_returned_with_comparable_metrics():
    terrain = generate_terrain(seed=12)
    routes = build_route_set(terrain, (3, 3), (58, 58), MissionConstraints(max_slope_deg=35, max_temperature_c=0))
    assert {r["profile"] for r in routes} == {"conservative", "balanced", "science_first"}
    for route in routes:
        assert route["metrics"]["distance_m"] > 0
        assert 0 <= route["metrics"]["uncertainty_pct"] <= 100
        assert "return_feasible" in route["metrics"]


def test_resource_limited_mission_can_be_rejected():
    terrain = generate_terrain(seed=12)
    c = MissionConstraints(eva_limit_minutes=10, energy_budget_wh=10, max_slope_deg=35, max_temperature_c=0)
    try:
        MultiObjectiveAStar(terrain, c, "balanced").search((3, 3), (58, 58))
    except ValueError as exc:
        assert "No route" in str(exc)
    else:
        raise AssertionError("Expected a route rejection under restrictive resources")
