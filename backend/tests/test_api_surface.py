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
