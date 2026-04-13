# SPDX-License-Identifier: AGPL-3.0-only
"""Runs-Router (Welle 1 — Implementation inkl. SSE-Stream).

Endpoints:
    * ``POST /projects/{project_id}/runs`` — legt einen Run an.
    * ``GET  /runs``                         — listet Runs (optional nach
      ``project_id`` gefiltert).
    * ``GET  /runs/{run_id}``                — liefert einen Run-Record.
    * ``GET  /runs/{run_id}/stream``         — SSE-Stream ueber
      :class:`ProgressEvent` aus :mod:`qualdatan_sidecar.events_bridge`.

Core ↔ Contract Mapping:
    * ``Run.config_json`` (TEXT) ↔ ``RunOut.config`` (``RunConfig``).
    * ``Run.started_at`` bleibt im Core als Start; der Contract befuellt
      ``RunOut.started_at``, solange der Status != ``pending`` ist.
    * ``Run.finished_at`` → ``RunOut.finished_at``.
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime
from typing import cast

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sse_starlette.sse import EventSourceResponse

from qualdatan_core.app_db import AppDB
from qualdatan_core.app_db import projects as projects_dao

from ... import events_bridge
from ...deps import get_app_db
from ..models import ProgressEvent, RunConfig, RunCreate, RunOut, RunStatus

runs_router = APIRouter(tags=["runs"])


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


_TERMINAL_STATUSES = {"completed", "failed", "cancelled"}


def _parse_ts(value: str | None) -> datetime | None:
    if not value:
        return None
    normalised = value.replace(" ", "T", 1)
    try:
        return datetime.fromisoformat(normalised)
    except ValueError:
        return None


def _parse_config(config_json: str) -> RunConfig:
    try:
        raw = json.loads(config_json or "{}")
    except json.JSONDecodeError:
        raw = {}
    if not isinstance(raw, dict):
        raw = {}
    # Mindestens ``method`` muss vorhanden sein (Pydantic erzwingt es);
    # faellt zurueck auf Leerstring, damit alte Persistenz nicht crasht.
    raw.setdefault("method", "")
    try:
        return RunConfig.model_validate(raw)
    except Exception:
        return RunConfig(method=str(raw.get("method") or ""))


def _coerce_status(raw: str) -> RunStatus:
    """Mappt Core-Status ('pending'|'running'|'completed'|'failed') auf den
    Contract-Literal (inkl. 'cancelled'). Unbekannte Werte → 'pending'."""

    if raw in {"pending", "running", "completed", "failed", "cancelled"}:
        return cast(RunStatus, raw)
    return "pending"


def _to_out(run: projects_dao.Run) -> RunOut:
    run_status = _coerce_status(run.status)
    started = _parse_ts(run.started_at) if run_status != "pending" else None
    return RunOut(
        id=str(run.id),
        project_id=str(run.project_id),
        status=run_status,
        config=_parse_config(run.config_json),
        started_at=started,
        finished_at=_parse_ts(run.finished_at),
        error=None,
    )


def _coerce_id(kind: str, raw: str) -> int:
    try:
        return int(raw)
    except (TypeError, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"{kind} {raw!r} nicht gefunden.",
        ) from exc


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@runs_router.post(
    "/projects/{project_id}/runs",
    response_model=RunOut,
    status_code=status.HTTP_201_CREATED,
)
async def create_run(
    project_id: str,
    body: RunCreate,
    app_db: AppDB = Depends(get_app_db),
) -> RunOut:
    """Startet einen neuen Analyse-Run fuer das gegebene Projekt."""

    pid = _coerce_id("Projekt", project_id)
    project = projects_dao.get_project(app_db, pid)
    if project is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Projekt {project_id} nicht gefunden.",
        )

    config_json = json.dumps(body.config.model_dump(mode="json"))
    run_dir = f"runs/{uuid.uuid4().hex}"
    run = projects_dao.create_run(
        app_db,
        project_id=project.id,
        run_dir=run_dir,
        config_json=config_json,
        status="pending",
    )
    for material in body.materials:
        projects_dao.add_run_material(
            app_db,
            run.id,
            material_kind="unspecified",
            path=material,
            source_label=material,
        )
    return _to_out(run)


@runs_router.get("/runs", response_model=list[RunOut])
async def list_runs(
    project_id: str | None = None,
    app_db: AppDB = Depends(get_app_db),
) -> list[RunOut]:
    """Listet Runs; optional nach ``project_id`` gefiltert."""

    pid: int | None = None
    if project_id is not None:
        pid = _coerce_id("Projekt", project_id)
    runs = projects_dao.list_runs(app_db, project_id=pid)
    return [_to_out(r) for r in runs]


@runs_router.get("/runs/{run_id}", response_model=RunOut)
async def get_run(
    run_id: str,
    app_db: AppDB = Depends(get_app_db),
) -> RunOut:
    """Liefert einen Run-Record per ID."""

    rid = _coerce_id("Run", run_id)
    run = projects_dao.get_run(app_db, rid)
    if run is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Run {run_id} nicht gefunden.",
        )
    return _to_out(run)


@runs_router.get("/runs/{run_id}/stream")
async def stream_run(
    run_id: str,
    request: Request,
    app_db: AppDB = Depends(get_app_db),
) -> EventSourceResponse:
    """Server-Sent-Events: ``ProgressEvent``-Stream eines laufenden Runs.

    Ist der Run bereits in einem Terminal-Status, wird **ein** finales
    Event gesendet und der Stream sofort geschlossen.
    """

    rid = _coerce_id("Run", run_id)
    run = projects_dao.get_run(app_db, rid)
    if run is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Run {run_id} nicht gefunden.",
        )

    run_status = _coerce_status(run.status)

    async def _event_generator():
        # Terminal? Dann sofort ein finales Event emittieren und schliessen.
        if run_status in _TERMINAL_STATUSES:
            terminal = ProgressEvent(
                event_type="finished" if run_status == "completed" else "failed",
                run_id=run_id,
                message=run_status,
            )
            yield {
                "event": terminal.event_type,
                "data": terminal.model_dump_json(),
            }
            return

        async with events_bridge.subscribe(run_id) as stream:
            async for evt in stream:
                if await request.is_disconnected():
                    break
                yield {
                    "event": evt.event_type,
                    "data": evt.model_dump_json(),
                }
                if evt.event_type in {"finished", "failed"}:
                    break

    return EventSourceResponse(_event_generator())


__all__ = ["runs_router"]
