"""Lightweight PDS3/PDS4 product-label inspection with raw-label preservation.

This module extracts metadata for review; it is not a replacement for the
instrument SIS, PDS label specification, calibration software or a full PDS
product parser. The untouched source label and its SHA-256 are retained.
"""
from __future__ import annotations

import hashlib
import re
from pathlib import Path
from typing import Any
from xml.etree import ElementTree as ET

PDS3_FIELDS = {
    "DATA_SET_ID", "PRODUCT_ID", "PRODUCT_VERSION_ID", "PRODUCT_CREATION_TIME",
    "SPACECRAFT_NAME", "INSTRUMENT_HOST_NAME", "INSTRUMENT_HOST_ID", "INSTRUMENT_NAME", "INSTRUMENT_ID", "INSTRUMENT_TYPE", "TARGET_NAME",
    "START_TIME", "STOP_TIME", "PLANET_DAY_NUMBER", "PLANETOCENTRIC_LATITUDE",
    "PLANETOGRAPHIC_LATITUDE", "EASTERNMOST_LONGITUDE", "WESTERNMOST_LONGITUDE",
    "POSITIVE_LONGITUDE_DIRECTION", "COORDINATE_SYSTEM_NAME", "MAP_PROJECTION_TYPE",
    "A_AXIS_RADIUS", "B_AXIS_RADIUS", "C_AXIS_RADIUS", "MAP_RESOLUTION", "MAP_SCALE",
    "LINES", "LINE_SAMPLES", "SAMPLE_BITS", "SAMPLE_TYPE", "SCALING_FACTOR", "OFFSET",
    "UNIT", "PRODUCT_TYPE", "IMAGE_LINES", "IMAGE_LINE_SAMPLES", "BANDS", "BAND_STORAGE_TYPE",
}


def _scalar(value: str) -> Any:
    value = value.strip().rstrip(",")
    if value.startswith('"') and value.endswith('"'):
        return value[1:-1]
    if value in {"TRUE", "FALSE"}:
        return value == "TRUE"
    try:
        return int(value)
    except ValueError:
        try:
            return float(value)
        except ValueError:
            return value


def parse_pds3(text: str) -> dict[str, Any]:
    fields: dict[str, Any] = {}
    objects: list[str] = []
    for line in text.splitlines():
        line = line.split("/*", 1)[0].strip()
        if not line or line.startswith("/*") or "=" not in line:
            continue
        key, value = [part.strip() for part in line.split("=", 1)]
        key = key.upper()
        if key == "OBJECT":
            objects.append(str(_scalar(value)))
            continue
        if key == "END_OBJECT":
            if objects:
                objects.pop()
            continue
        if key in PDS3_FIELDS or key.startswith("^"):
            fields[key] = _scalar(value)
    return {
        "format": "PDS3_LABEL",
        "identified_fields": fields,
        "product_id": fields.get("PRODUCT_ID"),
        "data_set_id": fields.get("DATA_SET_ID"),
        "mission": fields.get("SPACECRAFT_NAME"),
        "instrument": fields.get("INSTRUMENT_NAME") or fields.get("INSTRUMENT_ID"),
        "target": fields.get("TARGET_NAME"),
        "observation_start": fields.get("START_TIME"),
        "observation_stop": fields.get("STOP_TIME"),
        "map_projection": fields.get("MAP_PROJECTION_TYPE"),
        "coordinate_system": fields.get("COORDINATE_SYSTEM_NAME"),
        "positive_longitude_direction": fields.get("POSITIVE_LONGITUDE_DIRECTION"),
        "latitude_type_fields": {k: fields[k] for k in ("PLANETOCENTRIC_LATITUDE", "PLANETOGRAPHIC_LATITUDE") if k in fields},
        "map_resolution": fields.get("MAP_RESOLUTION"),
        "map_scale": fields.get("MAP_SCALE"),
        "object_context_note": "PDS3 OBJECT nesting is not interpreted as an instrument calibration model; inspect the complete original label.",
    }


def parse_pds4(text: str) -> dict[str, Any]:
    try:
        root = ET.fromstring(text)
    except ET.ParseError as exc:
        raise ValueError("The uploaded XML is not a valid PDS4 label.") from exc

    def name(el: ET.Element) -> str:
        return el.tag.rsplit("}", 1)[-1]

    def all_values(tag: str) -> list[str]:
        return [el.text.strip() for el in root.iter() if name(el) == tag and el.text and el.text.strip()]

    fields = {}
    tags = (
        "logical_identifier", "version_id", "title", "start_date_time", "stop_date_time",
        "primary_result_summary", "investigation_name", "instrument_host_name", "instrument_name",
        "target_name", "discipline_name", "local_identifier", "file_name", "file_size",
        "offset", "object_length", "sampling_parameter_name", "scaling_factor", "value_offset",
        "unit_id", "unit", "coordinate_space_reference", "reference_frame_id",
    )
    for tag in tags:
        values = all_values(tag)
        if values:
            fields[tag] = values[0] if len(values) == 1 else values
    arrays = []
    for node in root.iter():
        if name(node) == "Axis_Array":
            array = {}
            for child in node:
                if child.text and child.text.strip():
                    array[name(child)] = child.text.strip()
            if array:
                arrays.append(array)
    fields["axis_arrays"] = arrays
    file_areas = []
    for node in root.iter():
        if name(node) in {"File_Area_Observational", "File_Area_Ancillary", "File_Area_Inventory"}:
            file_info = {name(child): child.text.strip() for child in node.iter() if child.text and child.text.strip() and name(child) in {"file_name", "file_size", "records", "record_length", "offset", "md5_checksum"}}
            if file_info:
                file_areas.append({"area_type": name(node), **file_info})
    fields["file_areas"] = file_areas
    return {
        "format": "PDS4_XML_LABEL",
        "identified_fields": fields,
        "product_id": fields.get("logical_identifier"),
        "mission": fields.get("instrument_host_name"),
        "instrument": fields.get("instrument_name"),
        "target": fields.get("target_name"),
        "observation_start": fields.get("start_date_time"),
        "observation_stop": fields.get("stop_date_time"),
        "object_context_note": "PDS4 label extraction is a metadata aid. Validate array structure, units, coordinate reference and processing details in the complete label and applicable SIS.",
    }


def inspect_label(content: bytes, *, filename: str) -> dict[str, Any]:
    if len(content) > 10 * 1024 * 1024:
        raise ValueError("PDS label upload is limited to 10 MB.")
    try:
        text = content.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise ValueError("PDS labels must be UTF-8 or ASCII text. Preserve non-text payloads separately.") from exc
    suffix = Path(filename).suffix.lower()
    if suffix == ".xml" or text.lstrip().startswith("<?xml") or "<Product_" in text[:1000]:
        result = parse_pds4(text)
    elif suffix in {".lbl", ".txt"} or "PDS_VERSION_ID" in text[:2000]:
        result = parse_pds3(text)
    else:
        raise ValueError("Unrecognized label format. Upload a PDS3 .LBL or PDS4 .XML label.")
    result["source_filename"] = Path(filename).name
    result["source_sha256"] = hashlib.sha256(content).hexdigest()
    result["source_size_bytes"] = len(content)
    result["raw_label"] = text
    result["preservation_note"] = "Original label text is included verbatim in this record. Parsed fields are convenience extracts; original label/SIS take precedence."
    return result


def save_label(label: dict[str, Any], root: Path) -> Path:
    root.mkdir(parents=True, exist_ok=True)
    digest = str(label["source_sha256"])
    json_path = root / f"{digest}.json"
    json_path.write_text(__import__("json").dumps(label, indent=2), encoding="utf-8")
    raw_path = root / f"{digest}.lbl"
    raw_path.write_text(str(label["raw_label"]), encoding="utf-8")
    return json_path
