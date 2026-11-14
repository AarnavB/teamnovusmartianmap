from __future__ import annotations

import json
import zipfile
from pathlib import Path

import httpx
import numpy as np
import pytest

from app.services.archive_clients import search_pds, search_ode, ArchiveServiceError
from app.services.wmts import parse_capabilities, plan_tile_requests, inspect_cached_packages
from app.domain.pds_labels import inspect_label
from app.domain.observation_ingest import import_observation_csv
from app.domain.science_assistant import answer_question


def mock_client(handler):
    return httpx.Client(transport=httpx.MockTransport(handler))


def test_pds_search_uses_documented_query_and_preserves_raw_response():
    seen = {}

    def handler(request: httpx.Request):
        seen["url"] = str(request.url)
        return httpx.Response(200, json={"data": [{"title": "HiRISE product", "lid": "urn:nasa:pds:example"}]})

    with mock_client(handler) as client:
        result = search_pds("Gale Crater HiRISE", limit=7, client=client)
    assert "pds.nasa.gov/api/search/1/products" in seen["url"]
    assert "keywords=Gale+Crater+HiRISE" in seen["url"]
    assert result["record_count"] == 1
    assert result["records"][0]["lid"] == "urn:nasa:pds:example"
    assert result["raw"]["data"][0]["title"] == "HiRISE product"


def test_ode_search_uses_instrument_code_and_bbox_intersection():
    captured = {}

    def handler(request: httpx.Request):
        captured.update(dict(request.url.params))
        return httpx.Response(200, json={"Product": [{"ProductURL": "https://example.org/product.img", "LabelURL": "https://example.org/product.lbl"}]})

    with mock_client(handler) as client:
        result = search_ode(instrument="HiRISE", min_lat=-5.0, max_lat=-4.0, west_lon=137.0, east_lon=138.0, client=client)
    assert captured["iid"] == "HIRISE"
    assert captured["ihid"] == "MRO"
    assert captured["loc"] == "b"
    assert captured["westernlon"] == "137.0"
    assert result["records"][0]["ProductURL"].startswith("https://")


def test_ode_rejects_invalid_latitude_bbox():
    with pytest.raises(ValueError):
        search_ode(instrument="CTX", min_lat=5, max_lat=-5, west_lon=10, east_lon=20)


def test_wmts_capabilities_parsing_and_tile_planning():
    xml = b'''<?xml version="1.0"?>
    <Capabilities xmlns="http://www.opengis.net/wmts/1.0">
      <Contents>
        <Layer><Title>Curiosity Mosaic</Title><Identifier>curiosity_hirise_mosaic</Identifier>
          <Format>image/jpeg</Format><Style isDefault="true"><Identifier>default</Identifier></Style>
          <TileMatrixSetLink><TileMatrixSet>MarsEQC</TileMatrixSet></TileMatrixSetLink>
          <ResourceURL format="image/jpeg" resourceType="tile" template="https://tiles.example/{Style}/{TileMatrixSet}/{TileMatrix}/{TileRow}/{TileCol}.jpg"/>
        </Layer>
        <TileMatrixSet><Identifier>MarsEQC</Identifier><SupportedCRS>urn:ogc:def:crs:EPSG::104905</SupportedCRS>
          <TileMatrix><Identifier>0</Identifier><ScaleDenominator>100000000</ScaleDenominator><TopLeftCorner>-20000000 20000000</TopLeftCorner><TileWidth>256</TileWidth><TileHeight>256</TileHeight><MatrixWidth>8</MatrixWidth><MatrixHeight>8</MatrixHeight></TileMatrix>
          <TileMatrix><Identifier>1</Identifier><ScaleDenominator>50000000</ScaleDenominator><TopLeftCorner>-20000000 20000000</TopLeftCorner><TileWidth>256</TileWidth><TileHeight>256</TileHeight><MatrixWidth>16</MatrixWidth><MatrixHeight>16</MatrixHeight></TileMatrix>
        </TileMatrixSet>
      </Contents>
    </Capabilities>'''
    parsed = parse_capabilities(xml, layer_id="curiosity_hirise_mosaic", capabilities_url="https://tiles.example/wmts?REQUEST=GetCapabilities")
    plan = plan_tile_requests(parsed, "curiosity_hirise_mosaic", [0.0, -0.01, 0.01, 0.01], max_tiles=16)
    assert plan["tile_count"] > 0
    assert plan["tile_count"] <= 16
    assert all("{" not in tile["url"] and "}" not in tile["url"] for tile in plan["tiles"])
    assert plan["matrix_set"] == "MarsEQC"


def test_offline_tile_package_status_reads_manifest_without_extracting_tiles(tmp_path):
    package = tmp_path / "cache.zip"
    with zipfile.ZipFile(package, "w") as archive:
        archive.writestr("manifest.json", json.dumps({
            "layer": {"layer_id": "curiosity_hirise_mosaic", "title": "Curiosity HiRISE Mosaic"},
            "cache_plan": {"layer_id": "curiosity_hirise_mosaic", "bbox_wsen": [137, -5, 138, -4], "resolution_m_per_pixel": 2.5},
        }))
        archive.writestr("tile_index.json", json.dumps([{"row": 1, "col": 2}, {"row": 1, "col": 3}]))
        archive.writestr("tiles/0/1/2.png", b"not extracted during status check")
    result = inspect_cached_packages(tmp_path)
    assert result["package_count"] == 1
    assert result["tile_count"] == 2
    assert result["packages"][0]["title"] == "Curiosity HiRISE Mosaic"
    assert "offline review only" in result["availability_scope"]


def test_pds3_label_preserves_original_and_extracts_core_metadata():
    raw = b'''PDS_VERSION_ID = PDS3\nRECORD_TYPE = FIXED_LENGTH\nTARGET_NAME = MARS\nINSTRUMENT_ID = CTX\nPRODUCT_ID = B01_012345_1234_XN_56N123W\nMAP_PROJECTION_TYPE = EQUIRECTANGULAR\nPOSITIVE_LONGITUDE_DIRECTION = EAST\nEND\n'''
    result = inspect_label(raw, filename="sample.lbl")
    assert result["format"] == "PDS3_LABEL"
    assert result["identified_fields"]["TARGET_NAME"] == "MARS"
    assert result["identified_fields"]["INSTRUMENT_ID"] == "CTX"
    assert result["raw_label"].startswith("PDS_VERSION_ID")
    assert len(result["source_sha256"]) == 64


def test_pds4_label_extracts_product_and_axis_metadata():
    raw = b'''<?xml version="1.0"?>
    <Product_Observational xmlns="http://pds.nasa.gov/pds4/pds/v1">
      <Identification_Area><logical_identifier>urn:nasa:pds:demo:product</logical_identifier><version_id>1.0</version_id></Identification_Area>
      <Observation_Area><Time_Coordinates><start_date_time>2025-01-01T00:00:00Z</start_date_time></Time_Coordinates>
        <Investigation_Area><Observing_System><Observing_System_Component><name>CTX</name></Observing_System_Component></Observing_System></Investigation_Area>
        <Target_Identification><name>Mars</name></Target_Identification>
      </Observation_Area>
      <File_Area_Observational><File><file_name>demo.img</file_name><file_size>2048</file_size></File><Array_2D_Image><Axis_Array><axis_name>Line</axis_name><elements>4</elements></Axis_Array></Array_2D_Image></File_Area_Observational>
    </Product_Observational>'''
    result = inspect_label(raw, filename="sample.xml")
    assert result["format"] == "PDS4_XML_LABEL"
    assert result["product_id"] == "urn:nasa:pds:demo:product"
    assert result["identified_fields"]["axis_arrays"][0]["axis_name"] == "Line"
    assert result["raw_label"].startswith("<?xml")


def test_rems_and_rad_observation_csv_require_explicit_instrument_fields():
    rems = b"sol,temp,pressure\n100, -65, 820\n101,-64,815\n"
    record = import_observation_csv(
        rems, instrument="REMS", source_name="rems.csv",
        mapping={"sol": "sol", "temperature_c": "temp", "pressure_pa": "pressure"},
    )
    assert record["row_count"] == 2
    assert record["summary"]["temperature_c"]["min"] == -65
    assert record["provenance_note"].startswith("Imported from a user-supplied table")
    with pytest.raises(ValueError, match="radiation_value"):
        import_observation_csv(b"value\n1\n", instrument="RAD", source_name="rad.csv", mapping={"radiation_value": "value"})


def test_science_assistant_retrieves_curated_boxwork_evidence():
    result = answer_question("What evidence links the boxwork fractures and groundwater?")
    assert result["mode"] == "bm25_extractively_grounded"
    assert result["evidence"]
    assert all(item["url"].startswith("https://") for item in result["evidence"])


def test_official_download_rejects_unapproved_hosts():
    from app.services.official_downloads import download_official_file
    with pytest.raises(ValueError, match="allow-listed official"):
        download_official_file("https://example.com/product.tif", Path("/tmp/marscope-download-test"))


def test_official_download_preserves_bytes_redirect_chain_and_hash(tmp_path):
    from app.services.official_downloads import download_official_file
    payload = b"official archive test bytes"
    calls = []

    def handler(request: httpx.Request):
        calls.append(str(request.url))
        if request.url.host == "pds.nasa.gov":
            return httpx.Response(302, headers={"Location": "https://pds-geosciences.wustl.edu/test/product.tif"})
        return httpx.Response(200, content=payload, headers={"Content-Type": "image/tiff", "Content-Length": str(len(payload))})

    with mock_client(handler) as client:
        # The injected client is also configured not to follow redirects.
        record = download_official_file("https://pds.nasa.gov/test/start.tif", tmp_path, client=client)
    stored = tmp_path / record["stored_filename"]
    assert stored.read_bytes() == payload
    assert len(record["sha256"]) == 64
    assert record["size_bytes"] == len(payload)
    assert len(calls) == 2
    assert stored.with_suffix(stored.suffix + ".provenance.json").exists()


def test_responses_api_rag_provider_uses_only_retrieved_context_and_disables_storage():
    from app.services.llm_provider import generate_grounded_answer
    captured = {}

    def handler(request: httpx.Request):
        captured["url"] = str(request.url)
        captured["body"] = json.loads(request.content)
        assert request.headers["authorization"] == "Bearer test-key"
        return httpx.Response(200, json={
            "id": "resp-test-123",
            "status": "completed",
            "output": [{"type": "message", "content": [{"type": "output_text", "text": "Curiosity observed mineral-hardened ridges [BOXWORK-01]."}]}],
        })

    evidence = [{"id": "BOXWORK-01", "title": "NASA Boxwork Panorama", "summary": "Ridges were mineral hardened.", "url": "https://science.nasa.gov/example"}]
    with mock_client(handler) as client:
        result = generate_grounded_answer("What were the ridges?", evidence, api_key="test-key", model="test-model", client=client)
    assert captured["url"] == "https://api.openai.com/v1/responses"
    assert captured["body"]["store"] is False
    assert "BOXWORK-01" in captured["body"]["input"]
    assert "https://science.nasa.gov/example" in captured["body"]["input"]
    assert result["answer"].endswith("[BOXWORK-01].")
    assert result["model"] == "test-model"


def test_science_assistant_falls_back_to_cited_extracts_without_api_key(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    result = answer_question("What evidence links boxwork fractures to groundwater activity?")
    assert result["mode"] == "bm25_extractively_grounded"
    assert result["evidence"]
    assert "extractive fallback" in result["caution"]
