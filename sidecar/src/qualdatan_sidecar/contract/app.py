# SPDX-License-Identifier: AGPL-3.0-only
"""FastAPI-App-Factory fuer den gefrorenen Sidecar-Kontrakt.

``build_app()`` montiert saemtliche Router und haengt das Token-Gate
:func:`qualdatan_sidecar.contract.auth.verify_token` als globale
Dependency an, **ausgenommen** ``/healthz``. Health-Endpoint ist absichtlich
offen, damit die Tauri-Shell den Port-/Health-Check machen kann, bevor
der Handshake abgeschlossen ist.
"""

from __future__ import annotations

from fastapi import Depends, FastAPI

from qualdatan_sidecar import __version__

from .auth import verify_token
from .endpoints import (
    codebook_router,
    export_router,
    health_router,
    plugins_router,
    projects_router,
    runs_router,
)


def build_app() -> FastAPI:
    """Baut die FastAPI-Instanz mit allen Routern.

    Returns:
        Eine fertig konfigurierte :class:`fastapi.FastAPI` Instanz.
        Der Health-Router haengt **ohne** Token-Gate, alle anderen
        Router mit ``Depends(verify_token)``.
    """

    app = FastAPI(
        title="Qualdatan Sidecar",
        version=__version__,
        description=(
            "Lokaler FastAPI-Sidecar fuer die Qualdatan-Desktop-App. "
            "Contract-first: diese OpenAPI-Spec ist in Phase F gefroren; "
            "Welle 1 implementiert die Endpoint-Koerper, Welle 2 generiert "
            "den Frontend-Client."
        ),
    )

    # Health ist offen (kein Token noetig).
    app.include_router(health_router)

    # Alle anderen Router: Token-Gate als Depends.
    gated = [Depends(verify_token)]
    app.include_router(projects_router, dependencies=gated)
    app.include_router(runs_router, dependencies=gated)
    app.include_router(codebook_router, dependencies=gated)
    app.include_router(plugins_router, dependencies=gated)
    app.include_router(export_router, dependencies=gated)

    return app


__all__ = ["build_app"]
