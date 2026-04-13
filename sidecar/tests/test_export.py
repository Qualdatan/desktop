# SPDX-License-Identifier: AGPL-3.0-only
"""Tests fuer den Export-Router (Welle 1).

Die echten Core-Exporter (``generate_qdpx`` / ``build_pivot_excel``)
werden via ``monkeypatch`` durch leichte Stubs ersetzt, die eine kleine
Datei schreiben. So laesst sich das Routing, die 404/409-Logik, das
Token-Gate und die Response-Form pruefen, ohne den kompletten
Pipeline-Kontext (AnalysisResult / RunContext) aufzubauen.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from qualdatan_core.app_db import (
    create_project,
    create_run,
    open_app_db,
    update_run_status,
)
from qualdatan_sidecar.contract import routers as routers_pkg
from qualdatan_sidecar.contract.app import build_app
from qualdatan_sidecar.contract.auth import TOKEN_ENV, TOKEN_HEADER
from qualdatan_sidecar.deps import reset_app_db_singleton

DB_ENV = "QUALDATAN_SIDECAR_APP_DB"
TOKEN = "test-token"
AUTH = {TOKEN_HEADER: TOKEN}


# ---------------------------------------------------------------------------
# Fixture: frische AppDB + Projekt + completed-Run
# ---------------------------------------------------------------------------
@pytest.fixture()
def seeded(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """Seeded AppDB mit einem Projekt und einem ``completed`` Run.

    Der ``run_dir`` zeigt auf ein real existierendes Verzeichnis unter
    ``tmp_path``, sodass der Export-Router darin seine Output-Datei
    ablegen kann.
    """

    db_path = tmp_path / "app.db"
    run_dir = tmp_path / "run_output"
    run_dir.mkdir()

    monkeypatch.setenv(DB_ENV, str(db_path))
    monkeypatch.setenv(TOKEN_ENV, TOKEN)
    reset_app_db_singleton()

    with open_app_db(db_path) as db:
        project = create_project(db, name="HKS", description="Pilot")
        completed = create_run(
            db,
            project_id=project.id,
            run_dir=str(run_dir),
            config_json="{}",
            status="pending",
        )
        completed = update_run_status(db, completed.id, "completed")
        pending = create_run(
            db,
            project_id=project.id,
            run_dir=str(tmp_path / "pending_run"),
            config_json="{}",
            status="pending",
        )

    app = build_app()
    client = TestClient(app)
    try:
        yield {
            "client": client,
            "project_id": project.id,
            "completed_run_id": completed.id,
            "pending_run_id": pending.id,
            "run_dir": run_dir,
        }
    finally:
        reset_app_db_singleton()


def _install_stub_exporters(monkeypatch: pytest.MonkeyPatch) -> dict[str, int]:
    """Patcht die Core-Wrapper im Export-Router auf winzige Stubs.

    Returns:
        Dict mit ``calls`` (Counter), hauptsaechlich damit Tests
        verifizieren koennen, dass der Wrapper wirklich aufgerufen wurde.
    """

    counters: dict[str, int] = {"qdpx": 0, "xlsx": 0}

    def fake_qdpx(db, run, output_path: Path, options) -> None:
        counters["qdpx"] += 1
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(b"PK\x03\x04stub-qdpx")

    def fake_xlsx(db, run, output_path: Path, options) -> int:
        counters["xlsx"] += 1
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(b"PK\x03\x04stub-xlsx-content")
        return 1

    monkeypatch.setattr(routers_pkg.export, "_run_qdpx_export", fake_qdpx)
    monkeypatch.setattr(routers_pkg.export, "_run_xlsx_export", fake_xlsx)
    return counters


# ---------------------------------------------------------------------------
# Success paths
# ---------------------------------------------------------------------------
def test_export_qdpx_success(seeded, monkeypatch: pytest.MonkeyPatch) -> None:
    """Happy Path QDPX: 200, korrekte Form, Datei existiert, size_bytes stimmt."""

    counters = _install_stub_exporters(monkeypatch)
    client = seeded["client"]

    body = {
        "project_id": str(seeded["project_id"]),
        "run_id": str(seeded["completed_run_id"]),
        "include_annotations": True,
    }
    resp = client.post("/export/qdpx", headers=AUTH, json=body)
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["format"] == "qdpx"
    assert data["size_bytes"] > 0
    path = Path(data["path"])
    assert path.exists()
    assert path.stat().st_size == data["size_bytes"]
    assert counters["qdpx"] == 1


def test_export_xlsx_success(seeded, monkeypatch: pytest.MonkeyPatch) -> None:
    """Happy Path XLSX: 200, Format-Literal, Datei existiert."""

    counters = _install_stub_exporters(monkeypatch)
    client = seeded["client"]

    body = {
        "project_id": str(seeded["project_id"]),
        "run_id": str(seeded["completed_run_id"]),
    }
    resp = client.post("/export/xlsx", headers=AUTH, json=body)
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["format"] == "xlsx"
    assert data["size_bytes"] > 0
    assert Path(data["path"]).exists()
    assert counters["xlsx"] == 1


# ---------------------------------------------------------------------------
# Error paths
# ---------------------------------------------------------------------------
def test_export_qdpx_missing_run_returns_404(
    seeded, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Unbekannte Run-ID -> 404."""

    _install_stub_exporters(monkeypatch)
    client = seeded["client"]
    body = {"project_id": str(seeded["project_id"]), "run_id": "99999"}
    resp = client.post("/export/qdpx", headers=AUTH, json=body)
    assert resp.status_code == 404, resp.text


def test_export_qdpx_non_completed_run_returns_409(
    seeded, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Run mit Status ``pending`` -> 409 Conflict."""

    _install_stub_exporters(monkeypatch)
    client = seeded["client"]
    body = {
        "project_id": str(seeded["project_id"]),
        "run_id": str(seeded["pending_run_id"]),
    }
    resp = client.post("/export/qdpx", headers=AUTH, json=body)
    assert resp.status_code == 409, resp.text


def test_export_xlsx_non_completed_run_returns_409(
    seeded, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Auch XLSX verlangt ``completed``."""

    _install_stub_exporters(monkeypatch)
    client = seeded["client"]
    body = {
        "project_id": str(seeded["project_id"]),
        "run_id": str(seeded["pending_run_id"]),
    }
    resp = client.post("/export/xlsx", headers=AUTH, json=body)
    assert resp.status_code == 409, resp.text


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("path", ["/export/qdpx", "/export/xlsx"])
def test_export_requires_token(seeded, path: str) -> None:
    """Ohne ``X-Sidecar-Token`` -> 401."""

    client = seeded["client"]
    resp = client.post(path, json={"project_id": "1"})
    assert resp.status_code == 401, (path, resp.status_code, resp.text)
