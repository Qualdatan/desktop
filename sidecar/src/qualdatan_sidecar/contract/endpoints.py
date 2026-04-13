# SPDX-License-Identifier: AGPL-3.0-only
"""Router-Stubs der gefrorenen Sidecar-API.

Jeder Router enthaelt vollstaendig typisierte Endpoint-Signaturen (mit
``response_model``), aber nur ``/healthz`` ist tatsaechlich
implementiert. Alle anderen Funktionen heben ``NotImplementedError`` -
sie sind **Contract**, nicht Code. Welle 1 ersetzt die Koerper durch
echte Orchestrator-Calls, ohne die Signaturen zu veraendern.
"""

from __future__ import annotations

from fastapi import APIRouter, status
from sse_starlette.sse import EventSourceResponse

from qualdatan_sidecar import __version__

from .models import (
    BundleAvailable,
    BundleInstallRequest,
    BundleSummary,
    CodebookEntryOut,
    CodeOverridePatch,
    ExportRequest,
    ExportResult,
    ProjectCreate,
    ProjectOut,
    ProjectPatch,
    RunCreate,
    RunOut,
)

_TODO = "TODO Welle 1"


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------

health_router = APIRouter(tags=["health"])


@health_router.get("/healthz")
async def healthz() -> dict[str, str]:
    """Liveness-Check. Einziger Endpoint ohne Token-Gate.

    Returns:
        ``{"status": "ok", "version": <sidecar-version>}``.
    """

    return {"status": "ok", "version": __version__}


# ---------------------------------------------------------------------------
# Projects
# ---------------------------------------------------------------------------

projects_router = APIRouter(prefix="/projects", tags=["projects"])


@projects_router.post("", response_model=ProjectOut, status_code=status.HTTP_201_CREATED)
async def create_project(body: ProjectCreate) -> ProjectOut:
    """Legt ein neues Projekt an."""

    raise NotImplementedError(_TODO)


@projects_router.get("", response_model=list[ProjectOut])
async def list_projects() -> list[ProjectOut]:
    """Listet alle Projekte."""

    raise NotImplementedError(_TODO)


@projects_router.get("/{project_id}", response_model=ProjectOut)
async def get_project(project_id: str) -> ProjectOut:
    """Liefert ein Projekt per ID."""

    raise NotImplementedError(_TODO)


@projects_router.patch("/{project_id}", response_model=ProjectOut)
async def patch_project(project_id: str, body: ProjectPatch) -> ProjectOut:
    """Teil-Update eines Projekts."""

    raise NotImplementedError(_TODO)


@projects_router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(project_id: str) -> None:
    """Loescht ein Projekt (inkl. aller Runs, Materialien, Overrides)."""

    raise NotImplementedError(_TODO)


# ---------------------------------------------------------------------------
# Runs
# ---------------------------------------------------------------------------

runs_router = APIRouter(tags=["runs"])


@runs_router.post(
    "/projects/{project_id}/runs",
    response_model=RunOut,
    status_code=status.HTTP_201_CREATED,
)
async def create_run(project_id: str, body: RunCreate) -> RunOut:
    """Startet einen neuen Analyse-Run fuer das gegebene Projekt."""

    raise NotImplementedError(_TODO)


@runs_router.get("/runs", response_model=list[RunOut])
async def list_runs(project_id: str | None = None) -> list[RunOut]:
    """Listet Runs; optional nach ``project_id`` gefiltert."""

    raise NotImplementedError(_TODO)


@runs_router.get("/runs/{run_id}", response_model=RunOut)
async def get_run(run_id: str) -> RunOut:
    """Liefert einen Run-Record per ID."""

    raise NotImplementedError(_TODO)


@runs_router.get("/runs/{run_id}/stream")
async def stream_run(run_id: str) -> EventSourceResponse:
    """Server-Sent-Events: ``ProgressEvent``-Stream eines laufenden Runs.

    Der Event-``data``-Anteil ist jeweils das JSON eines
    :class:`qualdatan_sidecar.contract.models.ProgressEvent`.
    """

    raise NotImplementedError(_TODO)


# ---------------------------------------------------------------------------
# Codebook
# ---------------------------------------------------------------------------

codebook_router = APIRouter(prefix="/codebook", tags=["codebook"])


@codebook_router.get("/{project_id}", response_model=list[CodebookEntryOut])
async def get_codebook(project_id: str) -> list[CodebookEntryOut]:
    """Liefert das zusammengefuehrte Codebook eines Projekts."""

    raise NotImplementedError(_TODO)


@codebook_router.patch(
    "/{project_id}/codes/{code_id}",
    response_model=CodebookEntryOut,
)
async def patch_codebook_entry(
    project_id: str,
    code_id: str,
    body: CodeOverridePatch,
) -> CodebookEntryOut:
    """Legt ein Projekt-Override fuer einen Codebook-Eintrag an."""

    raise NotImplementedError(_TODO)


@codebook_router.delete(
    "/{project_id}/codes/{code_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_codebook_entry(project_id: str, code_id: str) -> None:
    """Entfernt einen Codebook-Eintrag (nur Override bzw. Projekt-lokal)."""

    raise NotImplementedError(_TODO)


# ---------------------------------------------------------------------------
# Plugins
# ---------------------------------------------------------------------------

plugins_router = APIRouter(tags=["plugins"])


@plugins_router.get("/plugins", response_model=list[BundleSummary])
async def list_plugins() -> list[BundleSummary]:
    """Listet lokal installierte Plugin-Bundles."""

    raise NotImplementedError(_TODO)


@plugins_router.post(
    "/plugins/install",
    response_model=BundleSummary,
    status_code=status.HTTP_201_CREATED,
)
async def install_plugin(body: BundleInstallRequest) -> BundleSummary:
    """Installiert ein Bundle aus dem Plugin-Server."""

    raise NotImplementedError(_TODO)


@plugins_router.post("/plugins/{bundle_id}/uninstall", status_code=status.HTTP_204_NO_CONTENT)
async def uninstall_plugin(bundle_id: str) -> None:
    """Deinstalliert ein lokal installiertes Bundle."""

    raise NotImplementedError(_TODO)


@plugins_router.post(
    "/projects/{project_id}/plugins/{bundle_id}/enable",
    response_model=BundleSummary,
)
async def enable_plugin_for_project(project_id: str, bundle_id: str) -> BundleSummary:
    """Aktiviert ein Bundle fuer ein Projekt."""

    raise NotImplementedError(_TODO)


@plugins_router.post(
    "/projects/{project_id}/plugins/{bundle_id}/disable",
    response_model=BundleSummary,
)
async def disable_plugin_for_project(project_id: str, bundle_id: str) -> BundleSummary:
    """Deaktiviert ein Bundle fuer ein Projekt."""

    raise NotImplementedError(_TODO)


@plugins_router.get("/plugins/available", response_model=list[BundleAvailable])
async def list_available_plugins() -> list[BundleAvailable]:
    """Listet im Plugin-Server verfuegbare (noch nicht installierte) Bundles."""

    raise NotImplementedError(_TODO)


# ---------------------------------------------------------------------------
# Export
# ---------------------------------------------------------------------------

export_router = APIRouter(prefix="/export", tags=["export"])


@export_router.post("/qdpx", response_model=ExportResult)
async def export_qdpx(body: ExportRequest) -> ExportResult:
    """Exportiert einen Run als REFI-QDA (QDPX)."""

    raise NotImplementedError(_TODO)


@export_router.post("/xlsx", response_model=ExportResult)
async def export_xlsx(body: ExportRequest) -> ExportResult:
    """Exportiert kodierte Segmente eines Runs als XLSX."""

    raise NotImplementedError(_TODO)


__all__ = [
    "health_router",
    "projects_router",
    "runs_router",
    "codebook_router",
    "plugins_router",
    "export_router",
]
