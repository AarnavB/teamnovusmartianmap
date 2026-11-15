import pytest

from app.lpa import LPAStar
from app.planner import MissionConstraints, MultiObjectiveAStar, build_route_set
from app.terrain import generate_terrain


JEV_WEIGHTS = {
    "distance": 0.01,
    "time": 0.02,
    "energy": 0.03,
    "terrain_risk": 0.75,
    "environment_risk": 0.02,
    "radiation": 0.05,
    "uncertainty": 0.05,
    "science_opportunity_cost": 0.04,
    "oxygen": 0.03,
}


def test_jev_objective_vector_is_validated_and_used_by_balanced_a_star():
    terrain = generate_terrain(width=24, height=24, seed=23)
    constraints = MissionConstraints.from_dict({"objective_weights": JEV_WEIGHTS})

    adaptive = MultiObjectiveAStar(terrain, constraints, "balanced")
    static_balanced = MultiObjectiveAStar(terrain, MissionConstraints(), "balanced")

    assert sum(adaptive.weights.values()) == pytest.approx(1.0)
    assert adaptive.weights["terrain_risk"] > 0.70
    assert adaptive.weights != static_balanced.weights


def test_jev_vector_does_not_change_static_route_a_or_c():
    terrain = generate_terrain(width=24, height=24, seed=24)
    constraints = MissionConstraints.from_dict({"objective_weights": JEV_WEIGHTS})
    defaults = MissionConstraints()

    for profile in ("conservative", "science_first"):
        adaptive_context = MultiObjectiveAStar(terrain, constraints, profile)
        static_context = MultiObjectiveAStar(terrain, defaults, profile)
        assert adaptive_context.weights == static_context.weights


def test_lpa_repair_reuses_the_same_jev_vector_as_route_b():
    terrain = generate_terrain(width=24, height=24, seed=25)
    constraints = MissionConstraints.from_dict({"objective_weights": JEV_WEIGHTS})

    route_b = MultiObjectiveAStar(terrain, constraints, "balanced")
    incremental = LPAStar(terrain, (3, 3), (20, 20), constraints)

    assert incremental.weights == route_b.weights
    assert incremental.constraints.objective_weights == constraints.objective_weights


def test_route_set_labels_only_route_b_as_jev_adaptive():
    terrain = generate_terrain(width=64, height=64, seed=26)
    constraints = MissionConstraints.from_dict({"objective_weights": JEV_WEIGHTS})

    routes = build_route_set(terrain, (3, 3), (58, 58), constraints)
    by_profile = {route["profile"]: route for route in routes}

    assert by_profile["conservative"]["weight_source"] == "static_profile"
    assert by_profile["science_first"]["weight_source"] == "static_profile"
    assert by_profile["balanced"]["weight_source"] == "jev"
    assert by_profile["balanced"]["name"] == "JEV-ADAPTIVE"


@pytest.mark.parametrize(
    "weights",
    [
        {"not_a_planner_objective": 1.0},
        {"distance": -0.1},
        {"distance": 1.1},
        {"distance": float("nan")},
        {"distance": 0.0, "time": 0.0},
    ],
)
def test_invalid_jev_objective_vectors_are_rejected(weights):
    with pytest.raises(ValueError):
        MissionConstraints.from_dict({"objective_weights": weights})
