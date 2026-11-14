"""Build a transparent, self-contained mission data export for offline review."""
from __future__ import annotations

import json
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from ..data_catalog import get_data_catalog
from .science_assistant import load_evidence


def create_package(*, output: Path, terrain: Any, plan: dict[str, Any] | None, data_root: Path) -> Path:
    output.parent.mkdir(parents=True, exist_ok=True)
    wmts_cache = data_root / "wmts_cache"
    wmts_archives = sorted(wmts_cache.glob("*.zip")) if wmts_cache.exists() else []
    downloads = data_root / "downloads"
    official_downloads = sorted(p for p in downloads.glob("*") if p.is_file()) if downloads.exists() else []
    labels = data_root / "pds_labels"
    preserved_labels = sorted(p for p in labels.glob("*") if p.is_file()) if labels.exists() else []
    manifest = {
        "application": "MARSCOPE",
        "package_created_utc": datetime.now(timezone.utc).isoformat(),
        "terrain_id": terrain.terrain_id,
        "terrain_status": terrain.status,
        "contains_offline_map_tiles": bool(wmts_archives),
        "cached_wmts_archives": [path.name for path in wmts_archives],
        "official_archive_downloads": [path.name for path in official_downloads],
        "preserved_pds_labels": [path.name for path in preserved_labels],
        "limitations": [
            "This package is for offline review and research only, not operational EVA navigation.",
            "Official archive metadata and evidence links are snapshots; no guarantee they remain current offline.",
            "Cached WMTS images are rendered map tiles, not calibrated science rasters or elevation data.",
            "Rover station observations are not spatially extrapolated over the terrain.",
        ],
    }
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
        archive.writestr("manifest.json", json.dumps(manifest, indent=2))
        archive.writestr("terrain.json", json.dumps(terrain.to_dict(), separators=(",", ":")))
        archive.writestr("data_catalog.json", json.dumps(get_data_catalog(), indent=2))
        archive.writestr("science_evidence.json", json.dumps(load_evidence(), indent=2))
        if plan is not None:
            archive.writestr("mission_plan.json", json.dumps(plan, indent=2))
        observations = data_root / "observations"
        if observations.exists():
            for path in observations.glob("*"):
                archive.write(path, f"observations/{path.name}")
        for path in wmts_archives:
            archive.write(path, f"wmts_cache/{path.name}")
        for path in official_downloads:
            archive.write(path, f"downloads/{path.name}")
        for path in preserved_labels:
            archive.write(path, f"pds_labels/{path.name}")
        ingested = data_root / "ingested"
        if ingested.exists():
            for path in ingested.glob("*"):
                if path.is_file() and path.suffix.lower() in {".tif", ".tiff", ".json"}:
                    archive.write(path, f"ingested/{path.name}")
    return output
