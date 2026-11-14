from __future__ import annotations

from types import SimpleNamespace

import pytest

pyproj = pytest.importorskip("pyproj")
from pyproj import CRS, Transformer

from app.domain.jezero import planetocentric_to_planetographic, poi_to_grid


def test_planetocentric_to_planetographic_is_identity_at_equator():
    assert planetocentric_to_planetographic(0.0, 3396190.0, 3376200.0) == 0.0


def test_poi_is_mapped_using_active_mars_crs_bounds():
    crs = CRS.from_proj4(
        "+proj=eqc +lat_ts=0 +lat_0=0 +lon_0=0 "
        "+a=3396190 +b=3376200 +units=m +no_defs +type=crs"
    )
    geographic = crs.geodetic_crs
    transformer = Transformer.from_crs(geographic, crs, always_xy=True)
    east, north = transformer.transform(77.45, 18.44)
    terrain = SimpleNamespace(
        coordinate_info={
            "crs_wkt": crs.to_wkt(),
            "bounds": [east - 10000, north - 10000, east + 10000, north + 10000],
        },
        width=100,
        height=100,
    )
    poi = {"latitude": 18.44, "longitude": 77.45}
    result = poi_to_grid(poi, terrain)
    assert result["status"] == "MAPPED_TO_ACTIVE_DEM"
    assert result["grid"] == {"x": 50, "y": 50}


def test_poi_reports_outside_active_dem():
    crs = CRS.from_proj4(
        "+proj=eqc +lat_ts=0 +lat_0=0 +lon_0=0 "
        "+a=3396190 +b=3376200 +units=m +no_defs +type=crs"
    )
    terrain = SimpleNamespace(
        coordinate_info={"crs_wkt": crs.to_wkt(), "bounds": [0, 0, 1000, 1000]},
        width=32,
        height=32,
    )
    result = poi_to_grid({"latitude": 18.44, "longitude": 77.45}, terrain)
    assert result["status"] == "OUTSIDE_ACTIVE_DEM"


def test_poi_reports_no_georeference_for_synthetic_terrain():
    terrain = SimpleNamespace(coordinate_info={}, width=64, height=64)
    result = poi_to_grid({"latitude": 18.44, "longitude": 77.45}, terrain)
    assert result["status"] == "DEM_NOT_GEOREFERENCED"
    assert result["grid"] is None
