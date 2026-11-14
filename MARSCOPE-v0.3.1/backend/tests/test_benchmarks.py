from app.benchmarks import scalar_baseline
from app.planner import MissionConstraints
from app.terrain import generate_terrain


def test_astar_matches_dijkstra_weighted_cost_on_small_fixture():
    terrain = generate_terrain(width=28, height=28, seed=91)
    constraints = MissionConstraints(max_slope_deg=35, max_temperature_c=0, eva_limit_minutes=300)
    astar = scalar_baseline(terrain, (2, 2), (25, 25), constraints, "standard_astar")
    dijkstra = scalar_baseline(terrain, (2, 2), (25, 25), constraints, "dijkstra")
    assert abs(astar["objective_cost"] - dijkstra["objective_cost"]) < 1e-8
    assert astar["return_feasible"] and dijkstra["return_feasible"]


def test_distance_only_baseline_returns_path():
    terrain = generate_terrain(width=28, height=28, seed=92)
    constraints = MissionConstraints(max_slope_deg=35, max_temperature_c=0, eva_limit_minutes=300)
    result = scalar_baseline(terrain, (2, 2), (25, 25), constraints, "distance_only")
    assert result["path"][0] == {"x": 2, "y": 2}
    assert result["path"][-1] == {"x": 25, "y": 25}
