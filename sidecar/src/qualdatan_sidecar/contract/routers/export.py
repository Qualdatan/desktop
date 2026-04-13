# SPDX-License-Identifier: AGPL-3.0-only
"""Export-Router (Welle 1 Implementation).

Stellt zwei Export-Endpoints bereit:

* ``POST /export/qdpx`` — erzeugt eine REFI-QDA (``.qdpx``) Datei fuer
  einen abgeschlossenen Run.
* ``POST /export/xlsx`` — erzeugt eine Pivot-Excel (``.xlsx``) Datei mit
  den kodierten Segmenten eines Runs.

Beide Endpoints delegieren an die echten Exporter in
:mod:`qualdatan_core.steps.step3_qdpx` bzw.
:mod:`qualdatan_core.export.pivot` und liefern anschliessend Pfad und
Groesse der erzeugten Datei als :class:`ExportResult` zurueck.

Adaptation (TODO Wave 2+):
    Die Core-Exporter erwarten historisch ``AnalysisResult`` bzw.
    ``RunContext`` Objekte aus dem dateibasierten Pipeline-Flow
    (per-run ``pipeline.db`` + ``output/<run>/``). Im Sidecar-App-DB-
    only-Flow existieren diese Container nicht mehr. Die Zuordnung
    Run → Codings erfolgt hier via
    :func:`qualdatan_core.app_db.list_codings`. Die konkrete
    Konstruktion eines Core-kompatiblen Objekts (Segmente, Dokumente)
    ist in Welle 1 noch nicht fertig; der Router kann deshalb in der
    Produktion fehlschlagen, wenn die echten Exporter aufgerufen
    werden. Die Tests patchen die beiden Module-Level-Helpers
    :func:`_run_qdpx_export` / :func:`_run_xlsx_export`, sodass
    Routing, 404/409-Handling, Token-Gate und Response-Form
    unabhaengig vom Core-Pipeline-Kontext verifiziert werden koennen.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status

from qualdatan_core.app_db import AppDB
from qualdatan_core.app_db import projects as projects_dao

from ...deps import get_app_db
from ..models import ExportRequest, ExportResult

export_router = APIRouter(prefix="/export", tags=["export"])


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _coerce_run_id(run_id: str) -> int:
    """Konvertiert die Run-ID-String in ``int``; ``404`` bei Unfug."""

    try:
        return int(run_id)
    except (TypeError, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Run {run_id!r} nicht gefunden.",
        ) from exc


def _resolve_run(db: AppDB, body: ExportRequest) -> projects_dao.Run:
    """Laedt den Run-Record, ``404`` bei fehlend, ``409`` bei nicht ``completed``.

    Wenn ``body.run_id`` nicht gesetzt ist, wird der neueste Run des
    Projekts genommen (``status='completed'``-Filter ist *nicht* gesetzt;
    der nachgelagerte Status-Check entscheidet).
    """

    if body.run_id is not None:
        rid = _coerce_run_id(body.run_id)
        run = projects_dao.get_run(db, rid)
        if run is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Run {body.run_id!r} nicht gefunden.",
            )
    else:
        try:
            pid = int(body.project_id)
        except (TypeError, ValueError) as exc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Projekt {body.project_id!r} nicht gefunden.",
            ) from exc
        runs = projects_dao.list_runs(db, project_id=pid, limit=1)
        if not runs:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Kein Run fuer Projekt {body.project_id!r}.",
            )
        run = runs[0]

    if run.status != "completed":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"Run {run.id} hat Status {run.status!r}; "
                "nur abgeschlossene Runs koennen exportiert werden."
            ),
        )
    return run


def _output_dir(run: projects_dao.Run) -> Path:
    """Zielverzeichnis fuer Exporte.

    Wenn ``run.run_dir`` ein existierender Pfad ist, wird dieser genommen;
    sonst ein temporaerer Fallback (``Path(run.run_dir)`` kann im
    App-DB-only-Flow ein rein symbolischer Key sein).
    """

    candidate = Path(run.run_dir)
    if candidate.is_absolute() or candidate.exists():
        candidate.mkdir(parents=True, exist_ok=True)
        return candidate
    # Fallback: temporaeres Arbeitsverzeichnis unter CWD.
    fallback = Path.cwd() / ".qualdatan_exports" / run.run_dir
    fallback.mkdir(parents=True, exist_ok=True)
    return fallback


def _result_from_path(path: Path, fmt: str) -> ExportResult:
    """Baut :class:`ExportResult` aus einem Pfad (fuer ``created_at`` wird
    der Datei-mtime genommen, sonst ``utcnow``)."""

    try:
        mtime = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)
        size = path.stat().st_size
    except OSError:
        mtime = datetime.now(timezone.utc)
        size = 0
    return ExportResult(
        path=str(path),
        format=fmt,  # type: ignore[arg-type]
        size_bytes=size,
        created_at=mtime,
    )


# ---------------------------------------------------------------------------
# Core-Wrapper (von Tests monkeygepatcht)
# ---------------------------------------------------------------------------
def _run_qdpx_export(
    db: AppDB, run: projects_dao.Run, output_path: Path, options: dict[str, Any]
) -> None:
    """Ruft den QDPX-Exporter des Cores auf.

    Adaptation (TODO): Der Core-Entry
    :func:`qualdatan_core.steps.step3_qdpx.generate_qdpx` erwartet ein
    voll gefuelltes :class:`~qualdatan_core.models.AnalysisResult`. In
    Welle 1 muss dieses aus der App-DB rekonstruiert werden
    (``list_codings(db, run_id=run.id)`` liefert die Rohdaten). Die
    vollstaendige Adaptation ist Wave-2-Scope; dieser Wrapper ruft die
    Core-Funktion zunaechst mit einer minimalen Hilfsstruktur auf und
    wird in Tests via ``monkeypatch`` ersetzt.
    """

    # Späte Imports, damit Tests die Module patchen koennen, ohne dass
    # der Import selbst fehlschlaegt.
    from qualdatan_core.app_db import list_codings
    from qualdatan_core.models import AnalysisResult, CodedSegment
    from qualdatan_core.steps.step3_qdpx import generate_qdpx

    codings = list_codings(db, run_id=run.id)
    segments: list[Any] = []
    documents: dict[str, str] = {}
    for c in codings:
        doc = getattr(c, "document", "") or ""
        segments.append(
            CodedSegment(
                code_id=getattr(c, "code_id", "") or "",
                code_name=getattr(c, "code_id", "") or "",
                hauptkategorie="",
                text=getattr(c, "text", "") or "",
                char_start=getattr(c, "char_start", 0) or 0,
                char_end=getattr(c, "char_end", 0) or 0,
                document=doc,
            )
        )
        documents.setdefault(doc, "")

    result = AnalysisResult(segments=segments, documents=documents)
    generate_qdpx(result, output_path=output_path)


def _run_xlsx_export(
    db: AppDB, run: projects_dao.Run, output_path: Path, options: dict[str, Any]
) -> int:
    """Ruft den Pivot-XLSX-Exporter des Cores auf.

    Adaptation (TODO): :func:`qualdatan_core.export.pivot.build_pivot_excel`
    erwartet einen :class:`~qualdatan_core.run_context.RunContext`. Im
    App-DB-only-Flow existiert der nicht; eine duennschichtige Adapter-
    Klasse muss in Wave 2 nachgereicht werden. Fuer den Router-Vertrag
    reicht der Aufruf-Stub, der in Tests gepatcht wird.
    """

    from qualdatan_core.export.pivot import build_pivot_excel
    from qualdatan_core.run_context import RunContext  # noqa: F401 (TODO Wave 2)

    # TODO(Wave 2): RunContext aus AppDB-Daten rekonstruieren.
    return build_pivot_excel(None, output_path)  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------
@export_router.post("/qdpx", response_model=ExportResult)
async def export_qdpx(
    body: ExportRequest,
    db: AppDB = Depends(get_app_db),
) -> ExportResult:
    """Exportiert einen Run als REFI-QDA (QDPX)."""

    run = _resolve_run(db, body)
    out_dir = _output_dir(run)
    out_path = out_dir / f"run_{run.id}.qdpx"
    options = {"include_annotations": body.include_annotations}
    _run_qdpx_export(db, run, out_path, options)
    return _result_from_path(out_path, "qdpx")


@export_router.post("/xlsx", response_model=ExportResult)
async def export_xlsx(
    body: ExportRequest,
    db: AppDB = Depends(get_app_db),
) -> ExportResult:
    """Exportiert kodierte Segmente eines Runs als XLSX."""

    run = _resolve_run(db, body)
    out_dir = _output_dir(run)
    out_path = out_dir / f"run_{run.id}_pivot.xlsx"
    options = {"include_annotations": body.include_annotations}
    _run_xlsx_export(db, run, out_path, options)
    return _result_from_path(out_path, "xlsx")


__all__ = ["export_router"]
