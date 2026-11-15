"""Request-scoped client for the standalone MARSCOPE JEV decision service.

Provider keys are forwarded in request bodies only. This module never logs
payloads, writes keys to disk, or copies them into process environment.
"""
from __future__ import annotations

import os
from typing import Any

import httpx
from fastapi import HTTPException


async def _request_jev_service(
    endpoint: str,
    payload: dict[str, Any],
    required_result_field: str,
) -> dict[str, Any]:
    service_url = os.getenv("JEV_SERVICE_URL", "").strip().rstrip("/")
    service_token = os.getenv("MARSCOPE_JEV_SERVICE_TOKEN", "").strip()
    if not service_url or not service_token:
        raise HTTPException(
            status_code=503,
            detail="JEV decision service is not configured. The static balanced route remains available.",
        )

    timeout = httpx.Timeout(100.0, connect=5.0)
    try:
        async with httpx.AsyncClient(timeout=timeout, follow_redirects=False) as client:
            response = await client.post(
                f"{service_url}{endpoint}",
                json=payload,
                headers={"Authorization": f"Bearer {service_token}", "Cache-Control": "no-store"},
            )
    except httpx.TimeoutException as exc:
        raise HTTPException(
            status_code=504,
            detail="JEV decision service timed out. The static balanced route remains available.",
        ) from exc
    except httpx.HTTPError as exc:
        raise HTTPException(
            status_code=503,
            detail="JEV decision service is unavailable. The static balanced route remains available.",
        ) from exc

    try:
        data = response.json()
    except ValueError:
        data = {}

    if not response.is_success:
        detail = data.get("detail") if isinstance(data, dict) else None
        safe_detail = detail if isinstance(detail, str) else "JEV decision service rejected the request."
        status = response.status_code if 400 <= response.status_code < 500 else 502
        raise HTTPException(status_code=status, detail=safe_detail)

    if not isinstance(data, dict) or required_result_field not in data:
        raise HTTPException(
            status_code=502,
            detail="JEV decision service returned an invalid response. The static balanced route remains available.",
        )
    return data


async def request_jev_pathfinding_weights(payload: dict[str, Any]) -> dict[str, Any]:
    result = await _request_jev_service("/v1/pathfinding-weights", payload, "weights")
    if not isinstance(result["weights"], dict):
        raise HTTPException(
            status_code=502,
            detail="JEV decision service returned an invalid weight vector. The static balanced route remains available.",
        )
    return result


async def request_jev_evidence_assessment(payload: dict[str, Any]) -> dict[str, Any]:
    result = await _request_jev_service("/v1/evidence-assessment", payload, "results")
    if not isinstance(result["results"], list):
        raise HTTPException(status_code=502, detail="JEV returned an invalid evidence assessment.")
    return result
