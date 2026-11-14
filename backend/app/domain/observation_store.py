from __future__ import annotations
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1] / "data" / "observations"


def save_observation_import(record: dict[str, Any], raw_content: bytes) -> Path:
    ROOT.mkdir(parents=True, exist_ok=True)
    digest = record["sha256"]
    (ROOT / f"{digest}.json").write_text(json.dumps(record, indent=2), encoding="utf-8")
    (ROOT / f"{digest}.csv").write_bytes(raw_content)
    return ROOT / f"{digest}.json"


def list_observation_imports() -> list[dict[str, Any]]:
    ROOT.mkdir(parents=True, exist_ok=True)
    results = []
    for path in sorted(ROOT.glob("*.json"), reverse=True):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            results.append({k: data.get(k) for k in ("instrument", "source_file", "sha256", "imported_utc", "row_count", "summary", "provenance_note")})
        except (OSError, json.JSONDecodeError):
            continue
    return results



def get_observation_import(digest: str) -> dict[str, Any] | None:
    if len(digest) != 64 or any(ch not in "0123456789abcdef" for ch in digest.lower()):
        return None
    path = ROOT / f"{digest}.json"
    if not path.is_file():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
