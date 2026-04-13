# SPDX-License-Identifier: AGPL-3.0-only
"""Projects-Router (Welle 1 — Implementation).

Mappt die Pydantic-Vertraege (``ProjectCreate``/``ProjectOut``/
``ProjectPatch``) auf die DAO-Funktionen in
:mod:`qualdatan_core.app_db.projects`.

Feld-Mapping Core ↔ Contract:
    * ``Project.preset_id`` ↔ ``ProjectOut.company``
    * ``Project.created_at`` (str, ISO) ↔ ``created_at`` und (als
      Platzhalter) ``updated_at`` — die Core-Tabelle trackt derzeit kein
      ``updated_at``, es wird mit ``created_at`` befuellt.
"""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status

from qualdatan_core.app_db import AppDB
from qualdatan_core.app_db import projects as projects_dao

from ...deps import get_app_db
from ..models import ProjectCreate, ProjectOut, ProjectPatch

projects_router = APIRouter(prefix="/projects", tags=["projects"])


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _parse_ts(value: str | None) -> datetime:
    """Parst einen ISO-Timestamp aus der App-DB tolerant.

    Die App-DB speichert Timestamps via ``CURRENT_TIMESTAMP`` als
    ``YYYY-MM-DD HH:MM:SS`` (ohne ``T``). Pydantic akzeptiert das nicht
    nativ, daher hier manuell geparst.
    """

    if not value:
        return datetime.utcnow()
    # Sowohl "YYYY-MM-DD HH:MM:SS" als auch "YYYY-MM-DDTHH:MM:SS".
    normalised = value.replace(" ", "T", 1)
    try:
        return datetime.fromisoformat(normalised)
    except ValueError:
        return datetime.utcnow()


def _to_out(project: projects_dao.Project) -> ProjectOut:
    ts = _parse_ts(project.created_at)
    return ProjectOut(
        id=str(project.id),
        name=project.name,
        company=project.preset_id or "",
        description=project.description or None,
        created_at=ts,
        updated_at=ts,
    )


def _coerce_id(project_id: str) -> int:
    try:
        return int(project_id)
    except (TypeError, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Projekt {project_id!r} nicht gefunden.",
        ) from exc


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@projects_router.post("", response_model=ProjectOut, status_code=status.HTTP_201_CREATED)
async def create_project(
    body: ProjectCreate,
    app_db: AppDB = Depends(get_app_db),
) -> ProjectOut:
    """Legt ein neues Projekt an."""

    project = projects_dao.create_project(
        app_db,
        name=body.name,
        description=body.description or "",
        preset_id=body.company,
    )
    return _to_out(project)


@projects_router.get("", response_model=list[ProjectOut])
async def list_projects(
    app_db: AppDB = Depends(get_app_db),
) -> list[ProjectOut]:
    """Listet alle Projekte (alphabetisch nach Name)."""

    return [_to_out(p) for p in projects_dao.list_projects(app_db)]


@projects_router.get("/{project_id}", response_model=ProjectOut)
async def get_project(
    project_id: str,
    app_db: AppDB = Depends(get_app_db),
) -> ProjectOut:
    """Liefert ein Projekt per ID."""

    pid = _coerce_id(project_id)
    project = projects_dao.get_project(app_db, pid)
    if project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Projekt {project_id} nicht gefunden.",
        )
    return _to_out(project)


@projects_router.patch("/{project_id}", response_model=ProjectOut)
async def patch_project(
    project_id: str,
    body: ProjectPatch,
    app_db: AppDB = Depends(get_app_db),
) -> ProjectOut:
    """Teil-Update eines Projekts."""

    pid = _coerce_id(project_id)
    try:
        project = projects_dao.update_project(
            app_db,
            pid,
            name=body.name,
            description=body.description,
            preset_id=body.company,
        )
    except LookupError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc
    return _to_out(project)


@projects_router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    project_id: str,
    app_db: AppDB = Depends(get_app_db),
) -> None:
    """Loescht ein Projekt (kaskadiert auf Runs/Materials/Overrides)."""

    pid = _coerce_id(project_id)
    if projects_dao.get_project(app_db, pid) is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Projekt {project_id} nicht gefunden.",
        )
    projects_dao.delete_project(app_db, pid)


__all__ = ["projects_router"]
