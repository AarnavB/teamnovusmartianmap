"""Controlled downloads from allow-listed official planetary archive hosts.

This service deliberately downloads one user-supplied URL at a time. It blocks
non-HTTPS URLs, credentials, unexpected redirect hosts and oversized products.
Original bytes, SHA-256 and URL/header provenance are retained without silently
converting PDS products into GeoTIFFs.
"""
from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import unquote, urljoin, urlparse
from typing import Any

import httpx

ALLOWED_HOSTS = {
    "pds.nasa.gov",
    "pds-imaging.jpl.nasa.gov",
    "pds.jpl.nasa.gov",
    "pds-geosciences.wustl.edu",
    "ode.rsl.wustl.edu",
    "pds-ppi.igpp.ucla.edu",
    "pdsppi.igpp.ucla.edu",
    "pds-atmospheres.nmsu.edu",
    "hirise.lpl.arizona.edu",
    "uahirise.org",
}
ALLOWED_EXTENSIONS = {
    ".tif", ".tiff", ".jp2", ".img", ".lbl", ".xml", ".csv", ".tab",
    ".txt", ".dat", ".qub", ".cub", ".zip", ".tar", ".gz", ".fits",
}
MAX_DOWNLOAD_BYTES = 250 * 1024 * 1024
USER_AGENT = "MARSCOPE/0.3.1 (research prototype; official archive downloader)"


class DownloadError(RuntimeError):
    pass


def _is_allowed_host(hostname: str | None) -> bool:
    if not hostname:
        return False
    host = hostname.lower().rstrip(".")
    return any(host == allowed or host.endswith("." + allowed) for allowed in ALLOWED_HOSTS)


def _validate_url(url: str) -> str:
    parsed = urlparse(url.strip())
    if parsed.scheme != "https" or not _is_allowed_host(parsed.hostname):
        raise ValueError("Only HTTPS URLs hosted by the allow-listed official NASA/PDS/mission archive domains can be downloaded.")
    if parsed.username or parsed.password:
        raise ValueError("URLs containing embedded credentials are not accepted.")
    if not parsed.path or parsed.path.endswith("/"):
        raise ValueError("The URL must point to a specific archive file, not a directory.")
    suffix = Path(unquote(parsed.path)).suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        raise ValueError(f"Unsupported archive file extension {suffix or '(none)'}. Supported: {', '.join(sorted(ALLOWED_EXTENSIONS))}.")
    return url


def download_official_file(url: str, root: Path, *, max_bytes: int = MAX_DOWNLOAD_BYTES, client: httpx.Client | None = None) -> dict[str, Any]:
    original_url = _validate_url(url)
    max_bytes = max(1, min(int(max_bytes), MAX_DOWNLOAD_BYTES))
    root.mkdir(parents=True, exist_ok=True)
    owned = client is None
    http = client or httpx.Client(
        timeout=httpx.Timeout(90.0, connect=15.0),
        headers={"User-Agent": USER_AGENT},
        follow_redirects=False,
    )
    digest = hashlib.sha256()
    bytes_written = 0
    response_headers: dict[str, str] = {}
    final_url = original_url
    response_content_type = "application/octet-stream"
    temp_path = root / f".download-{__import__('secrets').token_hex(12)}.part"
    try:
        current_url = original_url
        response = None
        for _ in range(6):
            parsed = urlparse(current_url)
            if parsed.scheme != "https" or not _is_allowed_host(parsed.hostname):
                raise DownloadError("An archive redirect left the allow-listed official HTTPS domains; download blocked.")
            response = http.stream("GET", current_url)
            with response as streamed:
                if streamed.status_code in {301, 302, 303, 307, 308}:
                    location = streamed.headers.get("location")
                    if not location:
                        raise DownloadError("Archive returned a redirect without a Location header.")
                    current_url = urljoin(current_url, location)
                    continue
                if streamed.status_code != 200:
                    raise DownloadError(f"Archive returned HTTP {streamed.status_code}.")
                length = streamed.headers.get("content-length")
                if length and int(length) > max_bytes:
                    raise DownloadError(f"Archive file exceeds the {max_bytes // (1024 * 1024)} MB download limit.")
                final_url = str(streamed.url)
                final_parsed = urlparse(final_url)
                if final_parsed.scheme != "https" or not _is_allowed_host(final_parsed.hostname) or final_parsed.username or final_parsed.password:
                    raise DownloadError("The final archive response URL is outside the allow-listed official HTTPS domains; download blocked.")
                response_content_type = streamed.headers.get("content-type", response_content_type)
                response_headers = {key: value for key, value in streamed.headers.items() if key.lower() in {"content-type", "content-length", "last-modified", "etag", "content-disposition"}}
                with temp_path.open("wb") as output:
                    for chunk in streamed.iter_bytes(chunk_size=1024 * 1024):
                        bytes_written += len(chunk)
                        if bytes_written > max_bytes:
                            raise DownloadError(f"Archive file exceeded the {max_bytes // (1024 * 1024)} MB download limit while streaming.")
                        digest.update(chunk)
                        output.write(chunk)
                break
        else:
            raise DownloadError("Archive exceeded the maximum redirect count.")
        if bytes_written == 0:
            raise DownloadError("Archive returned an empty file.")
        # Filename is derived from the final path, never directly trusted from HTTP headers.
        raw_name = Path(unquote(urlparse(final_url).path)).name
        safe_name = re.sub(r"[^A-Za-z0-9._-]+", "_", raw_name)[:120].strip("._") or "archive-product"
        suffix = Path(safe_name).suffix.lower()
        if suffix not in ALLOWED_EXTENSIONS:
            raise DownloadError("The final redirected URL does not have an accepted archive file extension.")
        record_id = digest.hexdigest()
        stored_name = f"{record_id[:16]}-{safe_name}"
        destination = root / stored_name
        temp_path.replace(destination)
        provenance = {
            "record_id": record_id,
            "original_url": original_url,
            "final_url": final_url,
            "retrieved_utc": datetime.now(timezone.utc).isoformat(),
            "stored_filename": stored_name,
            "sha256": record_id,
            "size_bytes": bytes_written,
            "content_type": response_content_type,
            "response_headers": response_headers,
            "source_host": urlparse(final_url).hostname,
            "archive_identity": "User-supplied link from an allow-listed official NASA/PDS/mission archive domain; verify it against the archive record and product label.",
            "limitations": [
                "Downloaded bytes are preserved as received; no scientific calibration or format conversion is performed.",
                "Inspect the original PDS label and applicable instrument SIS before interpreting data values, units or coordinates.",
                "A PDS image file is not automatically a DEM. Use a validated planetary GDAL workflow and preserve its label.",
            ],
        }
        sidecar = destination.with_suffix(destination.suffix + ".provenance.json")
        sidecar.write_text(json.dumps(provenance, indent=2), encoding="utf-8")
        return provenance
    except httpx.HTTPError as exc:
        raise DownloadError(f"Official archive download failed: {exc}") from exc
    except OSError as exc:
        raise DownloadError(f"Could not store archive file: {exc}") from exc
    finally:
        temp_path.unlink(missing_ok=True)
        if owned:
            http.close()
