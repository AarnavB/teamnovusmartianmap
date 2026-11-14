"""NASA/JPL Mars Trek WMTS discovery and bounded offline tile caching.

Layer IDs and coverage metadata below are copied from the official Mars Trek
layer catalogue. Capabilities remain authoritative for styles, matrix sets,
formats, tile dimensions and URL templates; no matrix identifiers are guessed.
"""
from __future__ import annotations

import math
import json
import re
import zipfile
from pathlib import Path
from typing import Any
from xml.etree import ElementTree as ET

import httpx

BASE = "https://trek.nasa.gov/tiles/Mars/EQ"
DOCS = "https://trek.nasa.gov/tiles/apidoc/trekAPI.html?body=mars"
USER_AGENT = "MARSCOPE/0.3.1 (research prototype; NASA/JPL Mars Trek WMTS client)"
MARS_RADIUS_M = 3_396_190.0

LAYERS: dict[str, dict[str, Any]] = {
    "curiosity_hirise_mosaic": {
        "title": "MRO HiRISE Curiosity Roving Site Mosaic",
        "instrument": "HiRISE",
        "coverage_wsen": [137.1224669, -4.9254743, 137.7298129, -4.2489588],
        "crs": "urn:ogc:def:crs:EPSG::104905",
        "resolution_text": "Capabilities-defined; inspect selected TileMatrix",
        "use": "High-resolution orbital image context around Curiosity's traverse; not a terrain elevation model.",
    },
    "Mars_MOLA_blend200ppx_HRSC_ClrShade_clon0dd_200mpp_lzw": {
        "title": "MOLA + HRSC Global Color Hillshade Blend",
        "instrument": "MOLA / HRSC",
        "coverage_wsen": [-180.0, -89.999224, 179.9984479, 90.0],
        "crs": "urn:ogc:def:crs:EPSG::104905",
        "resolution_text": "Approximately 200 m/pixel; global regional context only",
        "use": "Global topographic context; far too coarse for human-scale obstacle detection.",
    },
    "Mars_MGS_MOLA_ClrShade_merge_global_463m": {
        "title": "MGS MOLA Global Color Hillshade",
        "instrument": "MOLA",
        "coverage_wsen": [-180.0, -89.9991635, 179.9983271, 90.0],
        "crs": "urn:ogc:def:crs:EPSG::104905",
        "resolution_text": "Approximately 463 m/pixel",
        "use": "Global topographic context; not a local slope/roughness hazard product.",
    },
}


def _tag(element: ET.Element) -> str:
    return element.tag.rsplit("}", 1)[-1]


def _child_text(element: ET.Element, name: str, default: str = "") -> str:
    for child in element.iter():
        if _tag(child) == name and child.text:
            return child.text.strip()
    return default


def _children(element: ET.Element, name: str) -> list[ET.Element]:
    return [child for child in element.iter() if _tag(child) == name]


def _client(client: httpx.Client | None = None) -> tuple[httpx.Client, bool]:
    if client is not None:
        return client, False
    return httpx.Client(timeout=httpx.Timeout(15.0, connect=8.0), headers={"User-Agent": USER_AGENT}, follow_redirects=True), True


def _fetch_capabilities(layer_id: str, client: httpx.Client | None = None) -> tuple[str, bytes]:
    if layer_id not in LAYERS:
        raise ValueError(f"Unknown Mars Trek layer. Choose one of: {', '.join(LAYERS)}")
    endpoint = f"{BASE}/{layer_id}"
    candidates = [
        f"{endpoint}/1.0.0/WMTSCapabilities.xml",
        f"{endpoint}/WMTSCapabilities.xml",
        endpoint,
    ]
    http, owned = _client(client)
    try:
        last_error = ""
        for url in candidates:
            params = {"SERVICE": "WMTS", "REQUEST": "GetCapabilities"} if url == endpoint else None
            try:
                response = http.get(url, params=params)
                if response.status_code >= 400:
                    last_error = f"HTTP {response.status_code} from {url}"
                    continue
                body = response.content
                if b"Capabilities" in body[:10000] or b"ExceptionReport" in body[:10000]:
                    return str(response.url), body
                last_error = f"Non-WMTS response from {response.url}"
            except httpx.HTTPError as exc:
                last_error = str(exc)
        raise RuntimeError(f"Could not retrieve official WMTS GetCapabilities ({last_error}). Open the Mars Trek catalogue for the current service link.")
    finally:
        if owned:
            http.close()


def parse_capabilities(xml_bytes: bytes, *, layer_id: str, capabilities_url: str) -> dict[str, Any]:
    try:
        root = ET.fromstring(xml_bytes)
    except ET.ParseError as exc:
        raise RuntimeError("Mars Trek returned invalid WMTS capabilities XML.") from exc
    layers = [node for node in _children(root, "Layer") if _child_text(node, "Identifier") == layer_id]
    if not layers:
        # Some service endpoints expose only the requested layer but use another internal identifier.
        layers = [node for node in _children(root, "Layer") if _child_text(node, "Title").strip()]
    if not layers:
        raise RuntimeError(f"The WMTS capabilities document contains no layer metadata for {layer_id}.")
    layer = layers[0]
    styles = []
    for node in _children(layer, "Style"):
        identifier = _child_text(node, "Identifier")
        if identifier:
            styles.append(identifier)
    matrix_links = []
    for node in _children(layer, "TileMatrixSetLink"):
        matrix_set = _child_text(node, "TileMatrixSet")
        if matrix_set:
            matrix_links.append(matrix_set)
    resources = []
    for node in _children(layer, "ResourceURL"):
        if node.attrib.get("resourceType", "tile") == "tile" and node.attrib.get("template"):
            resources.append(node.attrib["template"])
    matrix_sets: dict[str, Any] = {}
    for node in _children(root, "TileMatrixSet"):
        identifier = _child_text(node, "Identifier")
        if not identifier or (matrix_links and identifier not in matrix_links):
            continue
        matrices = []
        for matrix in _children(node, "TileMatrix"):
            try:
                matrices.append({
                    "identifier": _child_text(matrix, "Identifier"),
                    "scale_denominator": float(_child_text(matrix, "ScaleDenominator")),
                    "top_left_corner": [float(v) for v in _child_text(matrix, "TopLeftCorner").replace(",", " ").split()],
                    "tile_width": int(_child_text(matrix, "TileWidth")),
                    "tile_height": int(_child_text(matrix, "TileHeight")),
                    "matrix_width": int(_child_text(matrix, "MatrixWidth")),
                    "matrix_height": int(_child_text(matrix, "MatrixHeight")),
                })
            except (TypeError, ValueError):
                continue
        matrix_sets[identifier] = {"crs": _child_text(node, "SupportedCRS"), "matrices": matrices}
    formats = [_child_text(node, "Format") for node in _children(layer, "Format") if _child_text(node, "Format")]
    output = {
        "layer_id": _child_text(layer, "Identifier", layer_id),
        "title": _child_text(layer, "Title", LAYERS[layer_id]["title"]),
        "formats": formats,
        "styles": styles,
        "matrix_sets": matrix_sets,
        "resource_templates": resources,
        "capabilities_url": capabilities_url,
        "service_documentation": DOCS,
    }
    if not matrix_sets:
        raise RuntimeError("WMTS capabilities did not expose a linked TileMatrixSet. The layer is discoverable but cannot be cached safely.")
    return output


def get_capabilities(layer_id: str, client: httpx.Client | None = None) -> dict[str, Any]:
    url, xml_bytes = _fetch_capabilities(layer_id, client)
    parsed = parse_capabilities(xml_bytes, layer_id=layer_id, capabilities_url=url)
    return {**LAYERS[layer_id], **parsed, "xml_bytes": len(xml_bytes)}


def _tile_template(capabilities: dict[str, Any], layer_id: str) -> str:
    templates = capabilities.get("resource_templates") or []
    if templates:
        return templates[0]
    styles = capabilities.get("styles") or ["default"]
    matrices = capabilities.get("matrix_sets") or {}
    if not matrices:
        raise RuntimeError("No tile matrix set available.")
    matrix_set = next(iter(matrices))
    ext = "jpg" if "image/jpeg" in (capabilities.get("formats") or []) else "png"
    return f"{BASE}/{layer_id}/1.0.0/{styles[0]}/{matrix_set}/{{TileMatrix}}/{{TileRow}}/{{TileCol}}.{ext}"


def _project_eqc(lon_deg: float, lat_deg: float) -> tuple[float, float]:
    # Mars Trek's equirectangular products use the Mars body. Capabilities must
    # still declare a Mars/equirectangular CRS; this transform is not generic.
    return (MARS_RADIUS_M * math.radians(lon_deg), MARS_RADIUS_M * math.radians(lat_deg))


def plan_tile_requests(capabilities: dict[str, Any], layer_id: str, bbox_wsen: list[float], max_tiles: int = 96) -> dict[str, Any]:
    if len(bbox_wsen) != 4:
        raise ValueError("bbox_wsen must be [west, south, east, north].")
    west, south, east, north = [float(v) for v in bbox_wsen]
    if not (-180 <= west < east <= 180 and -90 <= south < north <= 90):
        raise ValueError("WMTS cache bounds must be valid east-positive longitude and latitude degrees.")
    candidate_sets = capabilities.get("matrix_sets", {})
    matrix_set_id = next((key for key, value in candidate_sets.items() if "104905" in value.get("crs", "") or "Mars" in value.get("crs", "")), None)
    if not matrix_set_id:
        raise ValueError("The WMTS layer does not expose the supported Mars equirectangular CRS. Tile indices are not inferred.")
    matrix_set = candidate_sets[matrix_set_id]
    matrices = sorted(matrix_set["matrices"], key=lambda m: m["scale_denominator"], reverse=True)
    if not matrices:
        raise ValueError("No tile matrices available in the WMTS capabilities.")
    x0, y0 = _project_eqc(west, south)
    x1, y1 = _project_eqc(east, north)
    chosen = None
    chosen_bounds = None
    for matrix in matrices:
        res_m_per_px = matrix["scale_denominator"] * 0.00028
        tile_span_x = res_m_per_px * matrix["tile_width"]
        tile_span_y = res_m_per_px * matrix["tile_height"]
        left, top = matrix["top_left_corner"]
        c0 = max(0, math.floor((x0 - left) / tile_span_x))
        c1 = min(matrix["matrix_width"] - 1, math.floor((x1 - left) / tile_span_x))
        r0 = max(0, math.floor((top - y1) / tile_span_y))
        r1 = min(matrix["matrix_height"] - 1, math.floor((top - y0) / tile_span_y))
        count = max(0, c1 - c0 + 1) * max(0, r1 - r0 + 1)
        if count and count <= max_tiles:
            chosen, chosen_bounds = matrix, (c0, c1, r0, r1)
    if chosen is None or chosen_bounds is None:
        raise ValueError(f"Requested bounds require more than {max_tiles} tiles at the available coarsest zoom. Reduce the bbox or raise the safety limit (maximum 256).")
    c0, c1, r0, r1 = chosen_bounds
    template = _tile_template(capabilities, layer_id)
    style = (capabilities.get("styles") or ["default"])[0]
    template = template.replace("{Style}", style).replace("{TileMatrixSet}", matrix_set_id)
    requests = []
    for row in range(r0, r1 + 1):
        for col in range(c0, c1 + 1):
            url = (template.replace("{TileMatrix}", chosen["identifier"])
                   .replace("{TileRow}", str(row)).replace("{TileCol}", str(col)))
            requests.append({"row": row, "col": col, "url": url})
    return {
        "layer_id": layer_id,
        "matrix_set": matrix_set_id,
        "matrix": chosen["identifier"],
        "resolution_m_per_pixel": round(chosen["scale_denominator"] * 0.00028, 6),
        "tile_count": len(requests),
        "bbox_wsen": [west, south, east, north],
        "tiles": requests,
    }


def download_tile_cache(layer_id: str, bbox_wsen: list[float], output_zip: Path, *, max_tiles: int = 96, client: httpx.Client | None = None) -> dict[str, Any]:
    capabilities = get_capabilities(layer_id, client)
    plan = plan_tile_requests(capabilities, layer_id, bbox_wsen, max_tiles=max_tiles)
    http, owned = _client(client)
    output_zip.parent.mkdir(parents=True, exist_ok=True)
    fetched = []
    try:
        with zipfile.ZipFile(output_zip, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=5) as archive:
            archive.writestr("manifest.json", __import__("json").dumps({
                "source": "NASA/JPL Mars Trek WMTS", "documentation": DOCS,
                "layer": {k: v for k, v in capabilities.items() if k != "xml_bytes"},
                "cache_plan": {k: v for k, v in plan.items() if k != "tiles"},
                "limitations": ["Rendered map tiles only; not calibrated source rasters.", "No terrain elevation is derived from color/hillshade tiles.", "This cache is for offline review, not certified EVA navigation."],
            }, indent=2))
            for tile in plan["tiles"]:
                response = http.get(tile["url"])
                response.raise_for_status()
                content_type = response.headers.get("content-type", "")
                if not content_type.startswith("image/"):
                    raise RuntimeError(f"WMTS tile {tile['row']}/{tile['col']} did not return an image ({content_type or 'unknown content type'}).")
                ext = "jpg" if "jpeg" in content_type else "png"
                archive.writestr(f"tiles/{plan['matrix']}/{tile['row']}/{tile['col']}.{ext}", response.content)
                fetched.append({"row": tile["row"], "col": tile["col"], "bytes": len(response.content), "url": tile["url"]})
            archive.writestr("tile_index.json", __import__("json").dumps(fetched, indent=2))
    finally:
        if owned:
            http.close()
    return {"path": str(output_zip), "tile_count": len(fetched), "total_bytes": sum(x["bytes"] for x in fetched), "layer_id": layer_id, "matrix": plan["matrix"], "resolution_m_per_pixel": plan["resolution_m_per_pixel"], "bbox_wsen": bbox_wsen}


def inspect_cached_packages(root: Path) -> dict[str, Any]:
    """Summarize locally cached official WMTS packages without unpacking tiles.

    This reports review-package availability only. It deliberately does not
    claim that these images are loaded into the planner mesh or suitable for
    offline EVA navigation.
    """
    packages: list[dict[str, Any]] = []
    warnings: list[str] = []
    for path in sorted(root.glob("*.zip")) if root.exists() else []:
        try:
            with zipfile.ZipFile(path, "r") as archive:
                manifest = json.loads(archive.read("manifest.json"))
                tile_index = json.loads(archive.read("tile_index.json"))
            if not isinstance(manifest, dict) or not isinstance(tile_index, list):
                raise ValueError("manifest or tile index has an unexpected structure")
            layer = manifest.get("layer") if isinstance(manifest.get("layer"), dict) else {}
            cache_plan = manifest.get("cache_plan") if isinstance(manifest.get("cache_plan"), dict) else {}
            packages.append({
                "filename": path.name,
                "layer_id": cache_plan.get("layer_id") or layer.get("layer_id"),
                "title": layer.get("title"),
                "tile_count": len(tile_index),
                "resolution_m_per_pixel": cache_plan.get("resolution_m_per_pixel"),
                "bbox_wsen": cache_plan.get("bbox_wsen"),
                "size_bytes": path.stat().st_size,
            })
        except (OSError, ValueError, KeyError, zipfile.BadZipFile, json.JSONDecodeError) as exc:
            warnings.append(f"{path.name}: {exc}")
    return {
        "package_count": len(packages),
        "tile_count": sum(item["tile_count"] for item in packages),
        "packages": packages,
        "warnings": warnings,
        "availability_scope": "Cached NASA/JPL rendered WMTS tiles for offline review only; not integrated into the 3D mesh and not validated for EVA navigation.",
    }
