from app.lpa import LPAStar
from app.planner import MissionConstraints, route_metrics
from app.terrain import generate_terrain


def test_lpa_repairs_after_a_new_obstacle():
    terrain = generate_terrain(seed=33)
    constraints = MissionConstraints(max_slope_deg=35, max_temperature_c=0)
    planner = LPAStar(terrain, (2, 2), (61, 61), constraints)
    before = planner.extract_path()
    assert before[0] == (2, 2) and before[-1] == (61, 61)
    candidate = before[len(before) // 2]
    if candidate in ((2, 2), (61, 61)):
        candidate = before[len(before) // 2 + 1]
    terrain.obstacle[candidate[1]][candidate[0]] = True
    planner.update_cells([candidate])
    after = planner.extract_path()
    assert candidate not in after
    assert after[0] == (2, 2) and after[-1] == (61, 61)
    assert route_metrics(terrain, after, constraints)["distance_m"] >= route_metrics(terrain, before, constraints)["distance_m"]
