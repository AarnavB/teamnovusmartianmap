"""Validated GeoTIFF inspection and DEM-to-route-grid conversion."""
from __future__ import annotations

import hashlib
import math
from pathlib import Path
from typing import Any

import numpy as np


def _is_mars_ellipsoid(semi_major_m: float, semi_minor_m: float) -> bool:
    mars_equatorial = abs(semi_major_m - 3396190.0) <= 15000.0 or abs(semi_major_m - 3396000.0) <= 15000.0
    mars_polar = abs(semi_minor_m - 3376200.0) <= 20000.0
    mars_sphere = abs(semi_minor_m - semi_major_m) <= 15000.0
    return mars_equatorial and (mars_polar or mars_sphere)


def inspect_geotiff(path: Path) -> dict[str, Any]:
    try:
        import rasterio
    except ImportError as exc:
        raise RuntimeError("Install the optional geospatial requirements to inspect GeoTIFFs.") from exc
    try:
        from pyproj import CRS as PyprojCRS
    except ImportError as exc:
        raise RuntimeError("Install pyproj from backend/requirements-geospatial.txt to validate planetary CRS metadata.") from exc
    with rasterio.open(path) as src:
        if src.crs is None:
            raise ValueError("Raster has no CRS. Do not infer a Mars coordinate system from a filename.")
        pycrs = PyprojCRS.from_wkt(src.crs.to_wkt())
        ellipsoid = pycrs.ellipsoid
        semi_major = float(ellipsoid.semi_major_metre)
        semi_minor = float(ellipsoid.semi_minor_metre)
        mars_body = _is_mars_ellipsoid(semi_major, semi_minor)
        return {
            "path": str(path), "driver": src.driver, "width": src.width, "height": src.height,
            "band_count": src.count, "crs_wkt": src.crs.to_wkt(), "crs": src.crs.to_string(),
            "bounds": [src.bounds.left, src.bounds.bottom, src.bounds.right, src.bounds.top],
            "transform": list(src.transform), "resolution_native_units": list(src.res),
            "linear_units": src.crs.linear_units if src.crs.is_projected else "angular",
            "is_projected": src.crs.is_projected, "nodata": src.nodata,
            "ellipsoid": {"name": ellipsoid.name, "semi_major_m": semi_major, "semi_minor_m": semi_minor},
            "mars_reference_ellipsoid_check": mars_body,
            "mars_reference_ellipsoid_basis": "equatorial radius near 3,396 km and polar radius near 3,376 km, or accepted spherical Mars radius; still verify body and coordinate convention in the original PDS label",
            "descriptions": list(src.descriptions), "units": list(src.units),
            "tags": src.tags(), "band_tags": [src.tags(i) for i in range(1, src.count + 1)],
        }


def _local_std(array: np.ndarray) -> np.ndarray:
    padded = np.pad(array, 1, mode="edge")
    windows = [padded[dy:dy + array.shape[0], dx:dx + array.shape[1]] for dy in range(3) for dx in range(3)]
    stack = np.stack(windows, axis=0)
    return np.nanstd(stack, axis=0)


def dem_to_terrain(path: Path, *, width: int = 96, height: int = 96, vertical_units: str = "m") -> tuple[Any, dict[str, Any]]:
    """Convert a metric-projected DEM to route grid; unknown fields remain explicitly unknown.

    DEM pixel coordinates are interpreted only when CRS is projected with metre units.
    """
    try:
        import rasterio
        from rasterio.enums import Resampling
    except ImportError as exc:
        raise RuntimeError("Install backend/requirements-geospatial.txt before importing raster terrain.") from exc
    from ..terrain import Terrain

    info = inspect_geotiff(path)
    if not info["is_projected"] or str(info["linear_units"]).lower() not in {"metre", "meter", "meters", "metres"}:
        raise ValueError("DEM must already be in a projected CRS with metre units. Reproject using a Mars planetary CRS before import.")
    if not info["mars_reference_ellipsoid_check"]:
        raise ValueError("DEM CRS ellipsoid does not match the Mars reference ellipsoid range. This importer rejects Earth/unknown-body rasters instead of treating them as Mars coordinates.")
    if vertical_units != "m":
        raise ValueError("This import path currently accepts DEM vertical units in metres only. Convert using a documented scale factor before ingesting.")
    if info["band_count"] < 1:
        raise ValueError("DEM has no raster bands.")
    with rasterio.open(path) as src:
        if src.units and src.units[0]:
            band_unit = str(src.units[0]).strip().lower()
            if band_unit not in {"m", "meter", "meters", "metre", "metres"}:
                raise ValueError(f"DEM band metadata declares vertical units {src.units[0]!r}, not metres. Convert the data explicitly and preserve the scale factor.")
        masked = src.read(1, out_shape=(height, width), masked=True, resampling=Resampling.bilinear)
        z = np.asarray(masked.filled(np.nan), dtype=np.float64)
        mask = np.ma.getmaskarray(masked) | ~np.isfinite(z)
        if np.all(mask):
            raise ValueError("DEM contains no valid elevation cells.")
        # No-data is never filled with a made-up height; it becomes a blocked cell.
        fill_value = float(np.nanmedian(z))
        z_filled = np.where(mask, fill_value, z)
        if abs(src.transform.b) > 1e-9 or abs(src.transform.d) > 1e-9:
            raise ValueError("Rotated GeoTIFF grids are not supported in this DEM importer. Warp to a north-up projected grid first.")
        x_res = abs(src.transform.a) * (src.width / width)
        y_res = abs(src.transform.e) * (src.height / height)
        cell_m = float((x_res + y_res) / 2.0)
        if not math.isfinite(cell_m) or cell_m <= 0:
            raise ValueError("DEM has invalid metric pixel spacing.")

    gy, gx = np.gradient(z_filled, cell_m, cell_m)
    slope = np.degrees(np.arctan(np.hypot(gx, gy)))
    roughness_m = _local_std(z_filled)
    valid_ratio = float((~mask).sum() / mask.size)
    # Missing spatially resolved environment/radiation/soil/science data are NOT zero-risk.
    # Their placeholders are explicitly listed as unavailable and receive uncertainty cost.
    unknown = np.full((height, width), 0.65, dtype=np.float64)
    roughness_norm = np.clip(roughness_m / max(float(np.nanpercentile(roughness_m[~mask], 95)), 1e-6), 0, 1)
    obstacle = mask | (slope > 50.0)
    file_hash = hashlib.sha256(path.read_bytes()).hexdigest()
    grid = Terrain(
        width=width, height=height, cell_m=cell_m,
        elevation_m=z_filled.tolist(), slope_deg=slope.tolist(),
        roughness=roughness_norm.tolist(), regolith=np.full((height, width), 0.5).tolist(),
        temperature_c=np.full((height, width), -100.0).tolist(),
        environment_index=np.full((height, width), 0.5).tolist(),
        radiation_index=np.full((height, width), 0.5).tolist(),
        uncertainty=unknown.tolist(), science_potential=np.zeros((height, width)).tolist(),
        obstacle=obstacle.tolist(), targets=[], seed=0,
        available_layers={"elevation", "slope", "roughness", "uncertainty", "coverage_mask"},
        terrain_id=f"imported-dem-{file_hash[:12]}", status="NASA_OR_USER_SUPPLIED_GEOREFERENCED_DEM",
        warning="Elevation, slope and roughness are derived from the ingested GeoTIFF. Temperature, atmospheric, radiation, regolith and science layers are not connected. Unknown factors are penalized through the uncertainty model. This is not certified navigation data.",
        cell_units="metres", layer_provenance="Source GeoTIFF metadata retained in raster provenance; slope derived from metric DEM; roughness is local 3x3 standard deviation normalized to the valid-data 95th percentile.",
        coordinate_info={"crs": info["crs"], "crs_wkt": info["crs_wkt"], "bounds": info["bounds"], "transform": info["transform"], "pixel_spacing_m": [x_res, y_res]},
    )
    provenance = {
        "source": {key: value for key, value in info.items() if key != "path"}, "source_sha256": file_hash, "source_file_name": path.name,
        "processing": {"resampling": "bilinear to route grid", "route_grid": [width, height], "declared_vertical_units": vertical_units, "source_band_unit": info.get("units", [None])[0], "slope": "atan(sqrt(dz/dx^2 + dz/dy^2))", "roughness": "3x3 local standard deviation", "nodata": "blocked; not interpolated for planning"},
        "coverage_valid_fraction": round(valid_ratio, 6),
        "layers_created": ["elevation", "slope", "roughness", "coverage_mask"],
        "layers_unavailable": ["regolith", "temperature", "atmosphere", "radiation", "mineralogy", "science_targets"],
        "warning": "Confirm product identity, Mars body, datum, latitude/longitude convention, map projection, vertical units, scale and footprint using the original PDS label before operational interpretation.",
    }
    return grid, provenance


NORMALIZED_LAYER_FIELDS = {
    "regolith": "regolith",
    "environment_index": "environment_index",
    "radiation_index": "radiation_index",
    "science_potential": "science_potential",
    "uncertainty": "uncertainty",
}


def import_aligned_layer(path: Path, terrain: Any, *, layer: str, value_min: float, value_max: float, band: int = 1, source_unit: str = "unspecified") -> dict[str, Any]:
    """Align a user-selected, explicitly interpreted raster band to an active DEM grid.

    The user must state the field mapping and normalization range. This function
    never infers that arbitrary spectral/thermal values represent risk.
    """
    try:
        import rasterio
        from rasterio.enums import Resampling
        from rasterio.warp import reproject
        from rasterio.transform import from_bounds
    except ImportError as exc:
        raise RuntimeError("Install backend/requirements-geospatial.txt before importing aligned layers.") from exc
    allowed_layers = set(NORMALIZED_LAYER_FIELDS) | {"temperature_c"}
    if layer not in allowed_layers:
        raise ValueError(f"Layer must be one of: {', '.join(sorted(allowed_layers))}.")
    if not (math.isfinite(value_min) and math.isfinite(value_max) and value_min < value_max):
        raise ValueError("Source bounds must be finite and value_min must be less than value_max.")
    celsius_units = {"c", "degc", "celsius", "degreecelsius", "degreescelsius"}
    normalized_source_unit = source_unit.strip().lower().replace("°", "deg").replace("_", "").replace(" ", "")
    if layer == "temperature_c" and normalized_source_unit not in celsius_units:
        raise ValueError("temperature_c requires a source unit of C, degC or Celsius. Convert Kelvin/Fahrenheit explicitly before import.")
    target_info = terrain.coordinate_info or {}
    target_crs = target_info.get("crs_wkt") or target_info.get("crs")
    bounds = target_info.get("bounds")
    if not target_crs or not isinstance(bounds, list) or len(bounds) != 4:
        raise ValueError("The active terrain has no verified geospatial transform/bounds. Import a Mars DEM first.")
    try:
        from pyproj import CRS as PyprojCRS
    except ImportError as exc:
        raise RuntimeError("Install pyproj from backend/requirements-geospatial.txt before importing aligned layers.") from exc
    with rasterio.open(path) as src:
        if src.crs is None or not src.crs.is_projected:
            raise ValueError("The input layer must use a projected CRS.")
        if str(src.crs.linear_units).lower() not in {"metre", "meter", "meters", "metres"}:
            raise ValueError("The input layer must use projected metre units.")
        ellipsoid = PyprojCRS.from_wkt(src.crs.to_wkt()).ellipsoid
        if not _is_mars_ellipsoid(float(ellipsoid.semi_major_metre), float(ellipsoid.semi_minor_metre)):
            raise ValueError("Input layer ellipsoid does not match the Mars reference ellipsoid range. Both equatorial and polar radii must be compatible.")
        if not (1 <= band <= src.count):
            raise ValueError("Requested raster band does not exist.")
        band_unit = str(src.units[band - 1]).strip() if src.units and src.units[band - 1] else None
        normalized_band_unit = band_unit.lower().replace("°", "deg").replace("_", "").replace(" ", "") if band_unit else None
        if layer == "temperature_c" and normalized_band_unit and normalized_band_unit not in celsius_units:
            raise ValueError(f"The raster band declares unit {band_unit!r}, which is not Celsius. Convert the values and update the band unit metadata before importing as temperature_c.")
        target = np.full((terrain.height, terrain.width), np.nan, dtype=np.float32)
        target_transform = from_bounds(bounds[0], bounds[1], bounds[2], bounds[3], terrain.width, terrain.height)
        source = src.read(band, masked=True)
        source_values = source.filled(np.nan).astype(np.float32)
        reproject(
            source=source_values, destination=target,
            src_transform=src.transform, src_crs=src.crs, src_nodata=np.nan,
            dst_transform=target_transform, dst_crs=target_crs, dst_nodata=np.nan,
            resampling=Resampling.bilinear,
        )
        metadata = {
            "source_filename": path.name, "source_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "source_crs": src.crs.to_string(), "source_band": band,
            "band_description": src.descriptions[band - 1] if src.descriptions else None,
            "band_unit": band_unit,
            "user_declared_unit": source_unit, "normalization": {"min": value_min, "max": value_max, "clip": True},
            "resampling": "bilinear", "aligned_to_terrain_id": terrain.terrain_id,
        }
    valid = np.isfinite(target)
    valid_fraction = float(valid.sum() / valid.size)
    if valid_fraction < 0.05:
        raise ValueError("Less than 5% of the active terrain grid is covered by this raster. Check the footprints and CRS.")
    if layer == "temperature_c":
        physically_valid = valid & (target >= -150.0) & (target <= 50.0)
        if physically_valid.sum() < max(1, int(valid.size * 0.05)):
            raise ValueError("Fewer than 5% of aligned temperature cells fall in the allowed -150 to 50 °C range.")
        values = np.full_like(target, -100.0, dtype=np.float32)
        values[physically_valid] = target[physically_valid]
        # Temperature is a hard exclusion field when enabled. A cell without
        # valid temperature coverage must not inherit a plausible cold value.
        missing_temperature = ~physically_valid
        terrain.obstacle = (np.asarray(terrain.obstacle, dtype=bool) | missing_temperature).tolist()
        field = "temperature_c"
        valid = physically_valid
    else:
        values = np.zeros_like(target, dtype=np.float32)
        values[valid] = np.clip((target[valid] - value_min) / (value_max - value_min), 0.0, 1.0)
        values[~valid] = 0.65
        field = NORMALIZED_LAYER_FIELDS[layer]
    setattr(terrain, field, values.tolist())
    terrain.uncertainty = np.maximum(np.asarray(terrain.uncertainty), np.where(valid, 0.0, 0.85)).tolist()
    if layer == "temperature_c":
        terrain.available_layers.add("temperature")
    elif layer == "environment_index":
        terrain.available_layers.add("atmosphere")
    elif layer == "radiation_index":
        terrain.available_layers.add("radiation")
    elif layer == "science_potential":
        terrain.available_layers.add("science")
    elif layer == "regolith":
        terrain.available_layers.add("regolith")
    metadata["coverage_valid_fraction"] = round(valid_fraction, 6)
    metadata["missing_cells_policy"] = "temperature NoData/out-of-range cells are marked as no-go; normalized layers receive a 0.65 placeholder and elevated uncertainty, with coverage fraction retained"
    layer_meta = terrain.coordinate_info.setdefault("imported_layer_provenance", {})
    layer_meta[layer] = metadata
    terrain.layer_provenance += f" Additional layer {layer} imported from {path.name}; see coordinate_info.imported_layer_provenance.{layer}."
    return metadata
