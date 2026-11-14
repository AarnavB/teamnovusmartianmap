from fastapi.testclient import TestClient
from app.main import app


def test_api_health_catalog_and_science_routes():
    with TestClient(app) as client:
        health = client.get("/api/health")
        catalog = client.get("/api/data/catalog")
        evidence = client.get("/api/science/evidence")
    assert health.status_code == 200
    assert health.json()["project"] == "MARSCOPE"
    assert catalog.status_code == 200
    assert {"NASA PDS Search API", "PDS Geosciences Node ODE REST"}.issubset(set(catalog.json()["archives_connected"]))
    assert evidence.status_code == 200
    assert evidence.json()["records"]


def test_offline_status_exposes_review_cache_scope():
    with TestClient(app) as client:
        response = client.get("/api/offline/status")
    assert response.status_code == 200
    payload = response.json()
    assert "package_count" in payload
    assert "tile_count" in payload
    assert "not integrated into the 3D mesh" in payload["availability_scope"]


def test_api_pds_label_inspection_upload():
    content = b"PDS_VERSION_ID = PDS3\nTARGET_NAME = MARS\nINSTRUMENT_ID = CTX\nEND\n"
    with TestClient(app) as client:
        response = client.post("/api/data/pds/inspect-label", files={"file": ("demo.lbl", content, "text/plain")})
    assert response.status_code == 200
    assert response.json()["identified_fields"]["TARGET_NAME"] == "MARS"
    assert response.json()["raw_label_retained"] is True


def test_invalid_plan_constraints_return_validation_error_not_server_error():
    with TestClient(app) as client:
        response = client.post("/api/routes", json={
            "start": {"x": 3, "y": 3},
            "goal": {"x": 58, "y": 58},
            "constraints": {"objective_weight_multipliers": {"not_an_objective": 1.0}},
        })
    assert response.status_code == 422



def test_each_mission_site_has_a_distinct_labeled_terrain_grid():
    with TestClient(app) as client:
        jezero = client.get("/api/terrain/jezero")
        gale = client.get("/api/terrain/gale")
        legacy = client.get("/api/terrain")

    assert jezero.status_code == 200
    assert gale.status_code == 200
    assert jezero.json()["site_id"] == "jezero"
    assert gale.json()["site_id"] == "gale"
    assert jezero.json()["site_name"] == "Jezero Crater"
    assert gale.json()["site_name"] == "Gale Crater"
    assert jezero.json()["id"] != gale.json()["id"]
    assert jezero.json()["elevation_m"] != gale.json()["elevation_m"]
    assert jezero.json()["status"] == "SIMULATED_NOT_GEOREFERENCED"
    assert gale.json()["coordinate_info"]["georeferenced"] is False
    assert legacy.json()["site_id"] == "jezero"


def test_routes_use_requested_mission_site():
    with TestClient(app) as client:
        response = client.post("/api/routes", json={
            "site_id": "gale",
            "start": {"x": 4, "y": 5},
            "goal": {"x": 59, "y": 56},
            "constraints": {},
        })

    assert response.status_code == 200
    assert response.json()["site_id"] == "gale"
    assert response.json()["terrain_id"].startswith("mars-demo-gale-")


def test_vercel_project_preview_origin_is_allowed_by_cors():
    origin = "https://teamnovusmartianmap-git-feature-mission-site-selector-aarnav8.vercel.app"
    with TestClient(app) as client:
        response = client.options(
            "/api/terrain/gale",
            headers={
                "Origin": origin,
                "Access-Control-Request-Method": "GET",
            },
        )

    assert response.status_code == 200
    assert response.headers["access-control-allow-origin"] == origin
