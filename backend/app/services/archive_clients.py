"""Read-only clients for NASA PDS Search and the PDS Geosciences ODE REST service.

These clients intentionally return archive metadata and source URLs. They never
rewrite, reinterpret, or claim scientific values not present in source metadata.
"""
from __future__ import annotations

from typing import Any
from urllib.parse import quote
import httpx

PDS_SEARCH_BASE = "https://pds.nasa.gov/api/search/1"
ODE_REST_BASE = "https://oderest.rsl.wustl.edu/live2"
USER_AGENT = "MARSCOPE/0.3.1 (research prototype; NASA PDS archive client)"


class ArchiveServiceError(RuntimeError):
    pass


def _client(client: httpx.Client | None = None) -> tuple[httpx.Client, bool]:
    if client is not None:
        return client, False
    return httpx.Client(
        timeout=httpx.Timeout(35.0, connect=12.0),
        headers={"User-Agent": USER_AGENT, "Accept": "application/json"},
        follow_redirects=True,
    ), True


def _unwrap_records(payload: Any) -> list[dict[str, Any]]:
    """Best-effort list extraction while preserving the original response separately."""
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    if not isinstance(payload, dict):
        return []
    for key in ("data", "products", "results", "items", "hits"):
        value = payload.get(key)
        if isinstance(value, list):
            return [item for item in value if isinstance(item, dict)]
        if isinstance(value, dict):
            nested = _unwrap_records(value)
            if nested:
                return nested
    for key in ("Product", "product", "ProductResults", "ProductList"):
        value = payload.get(key)
        if isinstance(value, list):
            return [item for item in value if isinstance(item, dict)]
        if isinstance(value, dict):
            nested = _unwrap_records(value)
            if nested:
                return nested
    embedded = payload.get("_embedded")
    if isinstance(embedded, dict):
        return _unwrap_records(embedded)
    # Some XML-to-JSON conversions wrap Product records in one or more named objects.
    for value in payload.values():
        if isinstance(value, dict):
            nested = _unwrap_records(value)
            if nested:
                return nested
    return []


def _request_json(url: str, params: dict[str, Any], client: httpx.Client | None = None) -> dict[str, Any]:
    http, owned = _client(client)
    try:
        response = http.get(url, params=params)
        response.raise_for_status()
        try:
            body = response.json()
        except ValueError as exc:
            raise ArchiveServiceError("The official archive returned a non-JSON response; inspect its documentation or status page.") from exc
        if not isinstance(body, dict):
            raise ArchiveServiceError("The official archive response was not a JSON object.")
        return body
    except httpx.HTTPError as exc:
        raise ArchiveServiceError(f"Archive request failed: {exc}") from exc
    finally:
        if owned:
            http.close()


def search_pds(keywords: str, limit: int = 20, client: httpx.Client | None = None) -> dict[str, Any]:
    """Search PDS4 products via documented PDS Search API free-text keywords."""
    query = keywords.strip()
    if not query:
        raise ValueError("Enter one or more search keywords.")
    if len(query) > 180:
        raise ValueError("Search keywords must be 180 characters or fewer.")
    limit = max(1, min(int(limit), 100))
    body = _request_json(
        f"{PDS_SEARCH_BASE}/products",
        {"keywords": query, "limit": limit},
        client,
    )
    records = _unwrap_records(body)
    return {
        "archive": "NASA Planetary Data System Search API",
        "endpoint": f"{PDS_SEARCH_BASE}/products",
        "query": {"keywords": query, "limit": limit},
        "record_count": len(records),
        "records": records,
        "raw": body,
        "documentation": "https://nasa-pds.github.io/pds-api/guides/search.html",
        "note": "PDS Search indexes PDS archive products. It is a discovery API; product labels remain authoritative for units, coordinate conventions, processing level and file interpretation.",
    }


def resolve_pds_product(identifier: str, client: httpx.Client | None = None) -> dict[str, Any]:
    lid = identifier.strip()
    if not lid or len(lid) > 400:
        raise ValueError("A valid PDS product LID or LIDVID is required.")
    url = f"{PDS_SEARCH_BASE}/products/{quote(lid, safe=':') }"
    body = _request_json(url, {}, client)
    return {
        "archive": "NASA Planetary Data System Search API",
        "identifier": lid,
        "endpoint": url,
        "product": body,
        "documentation": "https://nasa-pds.github.io/pds-api/guides/search/endpoints.html",
    }


def search_ode(
    *,
    instrument: str = "HiRISE",
    min_lat: float,
    max_lat: float,
    west_lon: float,
    east_lon: float,
    product_type: str | None = None,
    limit: int = 50,
    client: httpx.Client | None = None,
) -> dict[str, Any]:
    """Search ODE product metadata using the documented Mars bbox query syntax."""
    if not (-90 <= min_lat < max_lat <= 90):
        raise ValueError("Latitude bounds must satisfy -90 <= min < max <= 90.")
    if not (0 <= west_lon <= 360 and 0 <= east_lon <= 360):
        raise ValueError("ODE east-positive longitude bounds must be between 0 and 360 degrees.")
    instrument = instrument.strip()
    allowed = {"HiRISE", "CTX", "CRISM"}
    if instrument not in allowed:
        raise ValueError(f"Instrument must be one of: {', '.join(sorted(allowed))}. Additional instruments require an ODE IIPT product-type lookup first.")
    # These product types are grounded in ODE's documented examples and CRISM
    # type nomenclature. The query's exact product type is still returned to UI.
    defaults = {"HiRISE": "RDRV11", "CTX": "EDR", "CRISM": "TRDR"}
    product_type = (product_type or defaults[instrument]).strip()
    params: dict[str, Any] = {
        "target": "mars",
        "query": "products",
        "results": "cmpf",
        "output": "JSON",
        "ihid": "MRO",
        "iid": {"HiRISE": "HIRISE", "CTX": "CTX", "CRISM": "CRISM"}[instrument],
        "minlat": min_lat,
        "maxlat": max_lat,
        "westernlon": west_lon,
        "easternlon": east_lon,
        "loc": "b",  # product footprint intersects the input bounding box
        "limit": max(1, min(int(limit), 100)),
    }
    params["pt"] = product_type
    body = _request_json(ODE_REST_BASE, params, client)
    return {
        "archive": "PDS Geosciences Node Orbital Data Explorer (ODE) REST",
        "endpoint": ODE_REST_BASE,
        "query": params,
        "record_count": len(_unwrap_records(body)),
        "records": _unwrap_records(body),
        "raw": body,
        "documentation": "https://oderest.rsl.wustl.edu/ODE_REST_V2.1.6.pdf",
        "note": "Bounding-box search uses ODE's product-footprint intersection mode. Returned footprints and product labels must be checked before treating any product as a local layer.",
    }
