#!/usr/bin/env python3
"""Reproject an already georeferenced Mars GeoTIFF to a local Mars AEQD CRS.

This script does not discover products, infer coordinates or fix a source CRS.
The input must already have a valid Mars CRS in its GeoTIFF metadata. Validate
that the source label's latitude and longitude convention matches that CRS.

Optional dependency: rasterio (install with conda-forge where GDAL wheels are
not available). The original file is never modified.
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path, help="Input georeferenced GeoTIFF")
    parser.add_argument("--output", required=True, type=Path, help="Output GeoTIFF in local Mars AEQD")
    parser.add_argument("--center-lat", required=True, type=float, help="Verified planetocentric latitude of local CRS origin, degrees")
    parser.add_argument("--center-lon", required=True, type=float, help="Verified east-positive longitude of local CRS origin, degrees")
    parser.add_argument("--resolution-m", type=float, default=None, help="Optional output pixel size in metres")
    parser.add_argument("--categorical", action="store_true", help="Use nearest-neighbour resampling for categorical data")
    args = parser.parse_args()

    try:
        import rasterio
        from rasterio.crs import CRS
        from rasterio.enums import Resampling
        from rasterio.warp import calculate_default_transform, reproject
    except ImportError as exc:
        raise SystemExit("Missing optional dependency. Install rasterio (and its GDAL stack) before running this script.") from exc

    if not args.input.is_file():
        raise SystemExit(f"Input file does not exist: {args.input}")
    if not -90.0 <= args.center_lat <= 90.0:
        raise SystemExit("--center-lat must be between -90 and 90 degrees")
    if not -360.0 <= args.center_lon <= 360.0:
        raise SystemExit("--center-lon must be between -360 and 360 degrees")
    if args.resolution_m is not None and args.resolution_m <= 0:
        raise SystemExit("--resolution-m must be positive")

    dst_crs = CRS.from_proj4(
        f"+proj=aeqd +lat_0={args.center_lat:.10f} +lon_0={args.center_lon:.10f} "
        "+a=3396190 +b=3376200 +units=m +no_defs +type=crs"
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    resampling = Resampling.nearest if args.categorical else Resampling.bilinear

    with rasterio.open(args.input) as src:
        if src.crs is None:
            raise SystemExit(
                "Input GeoTIFF has no CRS. Do not guess it: first interpret the PDS label / service metadata "
                "and write a validated source CRS."
            )
        transform, width, height = calculate_default_transform(
            src.crs, dst_crs, src.width, src.height, *src.bounds,
            resolution=args.resolution_m,
        )
        meta = src.meta.copy()
        meta.update({"crs": dst_crs, "transform": transform, "width": width, "height": height})
        with rasterio.open(args.output, "w", **meta) as dst:
            for band in range(1, src.count + 1):
                reproject(
                    source=rasterio.band(src, band),
                    destination=rasterio.band(dst, band),
                    src_transform=src.transform,
                    src_crs=src.crs,
                    src_nodata=src.nodata,
                    dst_transform=transform,
                    dst_crs=dst_crs,
                    dst_nodata=src.nodata,
                    resampling=resampling,
                )
            dst.update_tags(
                MARSCOPE_SOURCE_FILE=str(args.input.resolve()),
                MARSCOPE_PROCESSING="Local Mars AEQD reprojection; see provenance sidecar",
                MARSCOPE_CRS_ORIGIN_LAT_DEG=str(args.center_lat),
                MARSCOPE_CRS_ORIGIN_LON_EAST_DEG=str(args.center_lon),
            )

        sidecar = {
            "source_file": str(args.input.resolve()),
            "output_file": str(args.output.resolve()),
            "processed_utc": datetime.now(timezone.utc).isoformat(),
            "source_crs_wkt": src.crs.to_wkt(),
            "source_transform": list(src.transform),
            "source_bounds": list(src.bounds),
            "source_resolution": list(src.res),
            "source_nodata": src.nodata,
            "source_dimensions": [src.width, src.height, src.count],
            "destination_crs_proj4": dst_crs.to_proj4(),
            "mars_reference_figure_m": {"equatorial_radius": 3396190, "polar_radius": 3376200},
            "destination_origin": {
                "planetocentric_latitude_deg": args.center_lat,
                "east_positive_longitude_deg": args.center_lon,
            },
            "destination_transform": list(transform),
            "destination_dimensions": [width, height, src.count],
            "resampling": resampling.name,
            "warning": "Verify source coordinate convention and the CRS origin against original PDS labels / WMTS metadata. This script does not discover or validate source coordinates.",
        }
    args.output.with_suffix(args.output.suffix + ".provenance.json").write_text(json.dumps(sidecar, indent=2), encoding="utf-8")
    print(f"Wrote {args.output}")
    print(f"Wrote {args.output.with_suffix(args.output.suffix + '.provenance.json')}")


if __name__ == "__main__":
    main()
