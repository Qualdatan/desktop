# SPDX-License-Identifier: AGPL-3.0-only
"""Health-Router (offen, kein Token-Gate)."""

from __future__ import annotations

from fastapi import APIRouter

from qualdatan_sidecar import __version__

health_router = APIRouter(tags=["health"])


@health_router.get("/healthz")
async def healthz() -> dict[str, str]:
    """Liveness-Check.

    Returns:
        ``{"status": "ok", "version": <sidecar-version>}``.
    """

    return {"status": "ok", "version": __version__}


__all__ = ["health_router"]
