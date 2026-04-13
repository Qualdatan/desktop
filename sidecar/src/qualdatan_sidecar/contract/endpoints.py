# SPDX-License-Identifier: AGPL-3.0-only
"""Backwards-Compat-Re-Exports.

Die Router leben ab Welle 1 in :mod:`qualdatan_sidecar.contract.routers`.
Dieses Modul re-exportiert sie unveraendert, damit existierender Import-
Code (``from .endpoints import projects_router``) weiterlaeuft.
"""

from .routers import (
    codebook_router,
    export_router,
    health_router,
    plugins_router,
    projects_router,
    runs_router,
)

__all__ = [
    "codebook_router",
    "export_router",
    "health_router",
    "plugins_router",
    "projects_router",
    "runs_router",
]
