"""Jezero POI loading and geographic-to-planner-grid conversion."""
from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any


POI_FILE = Path(__file__).resolve().parents[4] / "data" / "jezero" / "pois.json"


def load_jezero_pois() -> list[dict[str, Any]]:
    """Load curated Jezero POIs; coordinates are planetocentric, east-positive."""
    with POI_FILE.open("r", encoding="utf-8") as handle:
        records = json.load(handle)
    if not isinstance(records, list):
        raise ValueError("Jezero POI catalogue must be a JSON array.")
    return records


def planetocentric_to_planetographic(latitude_deg: float, equatorial_radius_m: float, polar_radius_m: float) -> float:
    """Convert geocentric/planetocentric latitude to geodetic/planetographic latitude."""
    if not -90.0 <= latitude_deg <= 90.0:
        raise ValueError("Latitude must be between -90 and 90 degrees.")
    if abs(equatorial_radius_m - polar_radius_m) < 1e-6 or abs(latitude_deg) in (0.0, 90.0):
        return latitude_deg
    phi_c = math.radians(latitude_deg)
    return math.degrees(math.atan((equatorial_radius_m**2 / polar_radius_m**2) * math.tan(phi_c)))


def poi_to_grid(poi: dict[str, Any], terrain: Any) -> dict[str, Any]:
    """Convert a planetocentric east-positive POI into active DEM planner-grid indices."""
    info = terrain.coordinate_info or {}
    crs_wkt = info.get("crs_wkt")
    bounds = info.get("bounds")
    if not crs_wkt or not isinstance(bounds, list) or len(bounds) != 4:
        return {"grid": None, "projected_m": None, "status": "DEM_NOT_GEOREFERENCED"}

    try:
        from pyproj import CRS, Transformer
    except ImportError as exc:
        raise RuntimeError("Install pyproj to convert Jezero coordinates.") from exc

    projected_crs = CRS.from_wkt(crs_wkt)
    geographic_crs = projected_crs.geodetic_crs
    if geographic_crs is None:
        return {"grid": None, "projected_m": None, "status": "SOURCE_CRS_HAS_NO_GEOGRAPHIC_BASE"}

    ellipsoid = projected_crs.ellipsoid
    lat_planetographic = planetocentric_to_planetographic(
        float(poi["latitude"]),
        float(ellipsoid.semi_major_metre),
        float(ellipsoid.semi_minor_metre),
    )
    transformer = Transformer.from_crs(geographic_crs, projected_crs, always_xy=True)
    east_m, north_m = transformer.transform(float(poi["longitude"]), lat_planetographic)

    left, bottom, right, top = (float(value) for value in bounds)
    if right <= left or top <= bottom:
        raise ValueError("Active DEM has invalid projected bounds.")

    # Bounds describe pixel edges; subtract half a cell to obtain nearest centre index.
    fx = ((east_m - left) / (right - left)) * terrain.width - 0.5
    fy = ((top - north_m) / (top - bottom)) * terrain.height - 0.5
    inside = -0.5 <= fx < terrain.width - 0.5 and -0.5 <= fy < terrain.height - 0.5
    if not inside:
        return {"grid": None, "projected_m": {"easting": east_m, "northing": north_m}, "status": "OUTSIDE_ACTIVE_DEM"}
    x = max(0, min(terrain.width - 1, int(round(fx))))
    y = max(0, min(terrain.height - 1, int(round(fy))))
    return {
        "grid": {"x": x, "y": y},
        "grid_fractional": {"x": fx, "y": fy},
        "projected_m": {"easting": east_m, "northing": north_m},
        "status": "MAPPED_TO_ACTIVE_DEM",
    }
