# SPDX-License-Identifier: AGPL-3.0-only
"""Per-Resource APIRouter-Module.

Welle 1 implementiert die Endpoint-Koerper jeweils im passenden Modul.
"""

from .codebook import codebook_router
from .export import export_router
from .health import health_router
from .plugins import plugins_router
from .projects import projects_router
from .runs import runs_router

__all__ = [
    "codebook_router",
    "export_router",
    "health_router",
    "plugins_router",
    "projects_router",
    "runs_router",
]
