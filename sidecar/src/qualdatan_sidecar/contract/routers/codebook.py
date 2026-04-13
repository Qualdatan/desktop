# SPDX-License-Identifier: AGPL-3.0-only
"""Codebook-Router (Welle 1 Implementation).

Stellt die drei Codebook-Endpoints bereit:

* ``GET /codebook/{project_id}`` — listet alle aufgeloesten Codebook-
  Eintraege eines Projekts.
* ``PATCH /codebook/{project_id}/codes/{code_id}`` — legt einen
  Projekt-Override an oder aktualisiert ihn.
* ``DELETE /codebook/{project_id}/codes/{code_id}`` — setzt einen
  Override zurueck (idempotent).

Die Aufloesung (Label / Farbe / Definition / Beispiele) passiert durch
den :mod:`qualdatan_core.config_resolver` nach der 3-Ebenen-Praezedenz
(run_config → DB-Override → Bundle-Default → Fallback). In Welle 1
steht noch **kein** ``run_config`` zur Verfuegung (Runs sind work in
progress) und es gibt noch keinen Bundle-Loader, der Defaults fuer die
Sidecar liefert — daher wird ``run_config=None`` und
``bundle_default=None`` uebergeben.

TODO Wave 2+: Sobald der Bundle-Loader (Plugin-Server-Integration)
existiert, muss ``bundle_default`` aus dem geladenen Bundle fuer das
``preset_id`` des Projekts aufgeloest werden.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from qualdatan_core.app_db import (
    AppDB,
    CodebookEntry,
    get_project,
    list_codebook_entries,
    reset_codebook_entry,
    upsert_codebook_entry,
)
from qualdatan_core.config_resolver import (
    resolve_color,
    resolve_definition,
    resolve_examples,
    resolve_label,
)

from ..models import CodebookEntryOut, CodeOverridePatch
from ...deps import get_app_db

codebook_router = APIRouter(prefix="/codebook", tags=["codebook"])


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _parse_project_id(project_id: str) -> int:
    """Konvertiert die Path-String-ID in ``int``; ``404`` bei Unfug."""

    try:
        return int(project_id)
    except (TypeError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Projekt {project_id!r} existiert nicht.",
        )


def _require_project(db: AppDB, project_id: str) -> int:
    """Validiert, dass das Projekt existiert; gibt die numerische ID zurueck."""

    pid = _parse_project_id(project_id)
    if get_project(db, pid) is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Projekt {project_id!r} existiert nicht.",
        )
    return pid


def _resolved_entry_out(
    db: AppDB, project_id: int, code_id: str
) -> CodebookEntryOut:
    """Baut ein :class:`CodebookEntryOut` via ``config_resolver``.

    ``run_config`` und ``bundle_default`` sind in Welle 1 immer ``None``.
    """

    return CodebookEntryOut(
        code_id=code_id,
        name=resolve_label(
            code_id,
            project_id=project_id,
            run_config=None,
            app_db=db,
            bundle_default=None,
        ),
        description=resolve_definition(
            code_id,
            project_id=project_id,
            run_config=None,
            app_db=db,
            bundle_default=None,
        )
        or None,
        parent_id=None,
        color=resolve_color(
            code_id,
            project_id=project_id,
            run_config=None,
            app_db=db,
            bundle_default=None,
        ),
        anchors=resolve_examples(
            code_id,
            project_id=project_id,
            run_config=None,
            app_db=db,
            bundle_default=None,
        ),
    )


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------
@codebook_router.get("/{project_id}", response_model=list[CodebookEntryOut])
async def get_codebook(
    project_id: str,
    db: AppDB = Depends(get_app_db),
) -> list[CodebookEntryOut]:
    """Liefert das zusammengefuehrte Codebook eines Projekts."""

    pid = _require_project(db, project_id)
    entries: list[CodebookEntry] = list_codebook_entries(db, pid)
    return [_resolved_entry_out(db, pid, e.code_id) for e in entries]


@codebook_router.patch(
    "/{project_id}/codes/{code_id}",
    response_model=CodebookEntryOut,
)
async def patch_codebook_entry(
    project_id: str,
    code_id: str,
    body: CodeOverridePatch,
    db: AppDB = Depends(get_app_db),
) -> CodebookEntryOut:
    """Legt ein Projekt-Override fuer einen Codebook-Eintrag an."""

    pid = _require_project(db, project_id)
    patch = body.model_dump(exclude_unset=True)
    kwargs: dict = {}
    if "name" in patch:
        kwargs["label_override"] = patch["name"]
    if "description" in patch:
        kwargs["definition_override"] = patch["description"]
    if "color" in patch:
        kwargs["color_override"] = patch["color"]
    if "anchors" in patch:
        kwargs["examples_override"] = patch["anchors"]

    upsert_codebook_entry(db, pid, code_id, **kwargs)
    return _resolved_entry_out(db, pid, code_id)


@codebook_router.delete(
    "/{project_id}/codes/{code_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_codebook_entry(
    project_id: str,
    code_id: str,
    db: AppDB = Depends(get_app_db),
) -> None:
    """Entfernt einen Codebook-Override (Reset auf Bundle-Default)."""

    pid = _require_project(db, project_id)
    reset_codebook_entry(db, pid, code_id)
    return None


__all__ = ["codebook_router"]
