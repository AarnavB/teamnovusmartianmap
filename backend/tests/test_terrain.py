from app.terrain import generate_terrain


def test_fixture_is_repeatable_and_explicitly_synthetic():
    a = generate_terrain(seed=77)
    b = generate_terrain(seed=77)
    assert a.elevation_m == b.elevation_m
    assert len(a.elevation_m) == 64
    payload = a.to_dict()
    assert payload["status"] == "SIMULATED_NOT_GEOREFERENCED"
    assert payload["id"] == "mars-demo-synthetic-01"
    assert payload["name"] == "Synthetic Martian teaching tile"
    assert "any selected Mars mission site" in payload["warning"]
    assert len(a.targets) == 3
