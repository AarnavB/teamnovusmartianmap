from app.terrain import generate_terrain


def test_fixture_is_repeatable_and_explicitly_synthetic():
    a = generate_terrain(seed=77)
    b = generate_terrain(seed=77)
    assert a.elevation_m == b.elevation_m
    assert len(a.elevation_m) == 64
    assert a.to_dict()["status"] == "SIMULATED_NOT_GEOREFERENCED"
    assert len(a.targets) == 3
