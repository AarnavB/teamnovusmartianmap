"""Explicitly mapped ingestion for Curiosity REMS/RAD tabular exports."""
from __future__ import annotations

import csv
import hashlib
import io
from datetime import datetime, timezone
from typing import Any

ALLOWED_FIELDS = {"sol", "timestamp_utc", "temperature_c", "pressure_pa", "wind_speed_m_s", "radiation_value", "radiation_unit", "location_id"}


def import_observation_csv(content: bytes, *, instrument: str, source_name: str, mapping: dict[str, str]) -> dict[str, Any]:
    instrument = instrument.upper().strip()
    if instrument not in {"REMS", "RAD"}:
        raise ValueError("Instrument must be REMS or RAD.")
    if len(content) > 40 * 1024 * 1024:
        raise ValueError("CSV import is limited to 40 MB.")
    try:
        text = content.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise ValueError("CSV must be UTF-8 encoded. Preserve the original PDS product separately.") from exc
    reader = csv.DictReader(io.StringIO(text))
    columns = reader.fieldnames or []
    if not columns:
        raise ValueError("CSV has no header row.")
    if not mapping:
        raise ValueError("Provide an explicit mapping from normalized fields to source CSV column names.")
    invalid = set(mapping) - ALLOWED_FIELDS
    if invalid:
        raise ValueError(f"Unsupported normalized fields: {', '.join(sorted(invalid))}")
    missing = [column for column in mapping.values() if column not in columns]
    if missing:
        raise ValueError(f"Mapped source columns not found: {', '.join(missing)}")
    if instrument == "RAD" and not {"radiation_value", "radiation_unit"}.issubset(mapping):
        raise ValueError("RAD imports must explicitly map both radiation_value and radiation_unit.")
    if instrument == "REMS" and not any(field in mapping for field in ("temperature_c", "pressure_pa", "wind_speed_m_s")):
        raise ValueError("REMS imports must map at least one of temperature_c, pressure_pa or wind_speed_m_s.")
    rows: list[dict[str, Any]] = []
    for row_number, source_row in enumerate(reader, start=2):
        record: dict[str, Any] = {"source_row": row_number}
        for normalized, source_column in mapping.items():
            raw = (source_row.get(source_column) or "").strip()
            if not raw:
                continue
            if normalized in {"sol", "temperature_c", "pressure_pa", "wind_speed_m_s", "radiation_value"}:
                try:
                    record[normalized] = float(raw)
                except ValueError:
                    record[f"{normalized}_raw"] = raw
            else:
                record[normalized] = raw
        rows.append(record)
    numeric_fields = [f for f in ("temperature_c", "pressure_pa", "wind_speed_m_s", "radiation_value") if any(f in r for r in rows)]
    summary: dict[str, Any] = {}
    for field in numeric_fields:
        values = [float(r[field]) for r in rows if isinstance(r.get(field), (int, float))]
        if values:
            summary[field] = {"count": len(values), "min": min(values), "max": max(values), "mean": sum(values) / len(values)}
    digest = hashlib.sha256(content).hexdigest()
    if not rows:
        raise ValueError("CSV contains a header but no observation rows.")
    radiation_units = sorted({str(row.get("radiation_unit")) for row in rows if row.get("radiation_unit")})
    return {
        "instrument": instrument,
        "source_file": source_name,
        "sha256": digest,
        "imported_utc": datetime.now(timezone.utc).isoformat(),
        "source_columns": columns,
        "explicit_mapping": mapping,
        "row_count": len(rows),
        "summary": summary,
        "radiation_units": radiation_units,
        "records": rows[:5000],
        "provenance_note": "Imported from a user-supplied table. Units, calibration, coordinate association and time semantics must be confirmed against the original PDS label/SIS. These station observations are not spatially extrapolated across terrain.",
    }
