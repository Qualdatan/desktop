# SPDX-License-Identifier: AGPL-3.0-only
"""Tests fuer den Codebook-Router (Welle 1).

Jeder Test nutzt eine frische :class:`~qualdatan_core.app_db.AppDB` auf
``tmp_path`` (ueber die Env-Var ``QUALDATAN_SIDECAR_APP_DB``) und einen
festen Dummy-Token. Das LRU-cached Sidecar-Singleton wird vor jedem
Test zurueckgesetzt.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from qualdatan_core.app_db import create_project, open_app_db
from qualdatan_sidecar.contract.app import build_app
from qualdatan_sidecar.contract.auth import TOKEN_ENV, TOKEN_HEADER
from qualdatan_sidecar.deps import reset_app_db_singleton

DB_ENV = "QUALDATAN_SIDECAR_APP_DB"
TOKEN = "test-token"
AUTH = {TOKEN_HEADER: TOKEN}


@pytest.fixture()
def seeded_client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """Baut eine frische AppDB + seed Projekt und liefert einen TestClient."""

    db_path = tmp_path / "app.db"
    monkeypatch.setenv(DB_ENV, str(db_path))
    monkeypatch.setenv(TOKEN_ENV, TOKEN)
    reset_app_db_singleton()

    # Seed ein Projekt (id=1) direkt ueber denselben DB-Pfad.
    with open_app_db(db_path) as db:
        project = create_project(db, name="HKS", description="Pilot")
    pid = project.id

    app = build_app()
    client = TestClient(app)
    try:
        yield client, pid
    finally:
        reset_app_db_singleton()


# ---------------------------------------------------------------------------
# GET
# ---------------------------------------------------------------------------
def test_get_codebook_empty(seeded_client) -> None:
    """Neu angelegtes Projekt hat kein Codebook-Override -> leere Liste."""

    client, pid = seeded_client
    resp = client.get(f"/codebook/{pid}", headers=AUTH)
    assert resp.status_code == 200, resp.text
    assert resp.json() == []


def test_get_codebook_bad_project(seeded_client) -> None:
    """Unbekannte Projekt-ID -> 404."""

    client, _pid = seeded_client
    resp = client.get("/codebook/9999", headers=AUTH)
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# PATCH + GET
# ---------------------------------------------------------------------------
def test_patch_creates_override_and_get_returns_it(seeded_client) -> None:
    """PATCH legt den Eintrag an, GET liefert ihn aufgeloest zurueck."""

    client, pid = seeded_client
    body = {
        "name": "Prozess Ausfuehrung",
        "description": "Alles, was auf der Baustelle passiert.",
        "color": "#ffcc00",
        "anchors": ["Beispiel A", "Beispiel B"],
    }
    resp = client.patch(
        f"/codebook/{pid}/codes/PROC-EXEC", headers=AUTH, json=body
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["code_id"] == "PROC-EXEC"
    assert data["name"] == body["name"]
    assert data["description"] == body["description"]
    assert data["color"] == "#ffcc00"
    assert data["anchors"] == ["Beispiel A", "Beispiel B"]

    # GET liefert den Eintrag zurueck.
    resp = client.get(f"/codebook/{pid}", headers=AUTH)
    assert resp.status_code == 200
    entries = resp.json()
    assert len(entries) == 1
    assert entries[0]["code_id"] == "PROC-EXEC"
    assert entries[0]["name"] == body["name"]


def test_patch_partial_preserves_untouched_fields(seeded_client) -> None:
    """Zweites PATCH aktualisiert nur das uebergebene Feld."""

    client, pid = seeded_client
    # Erstes PATCH: komplett.
    r1 = client.patch(
        f"/codebook/{pid}/codes/PROC-EXEC",
        headers=AUTH,
        json={
            "name": "Urspruenglich",
            "description": "Urspruengliche Definition.",
            "color": "#abcdef",
            "anchors": ["A1"],
        },
    )
    assert r1.status_code == 200

    # Zweites PATCH: nur Farbe.
    r2 = client.patch(
        f"/codebook/{pid}/codes/PROC-EXEC",
        headers=AUTH,
        json={"color": "#123456"},
    )
    assert r2.status_code == 200, r2.text
    data = r2.json()
    assert data["color"] == "#123456"
    assert data["name"] == "Urspruenglich"
    assert data["description"] == "Urspruengliche Definition."
    assert data["anchors"] == ["A1"]


def test_patch_bad_project(seeded_client) -> None:
    """PATCH auf nicht existierendes Projekt -> 404."""

    client, _pid = seeded_client
    resp = client.patch(
        "/codebook/9999/codes/PROC-EXEC",
        headers=AUTH,
        json={"name": "X"},
    )
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# DELETE
# ---------------------------------------------------------------------------
def test_delete_removes_override(seeded_client) -> None:
    """DELETE nach PATCH entfernt den Eintrag aus der Liste."""

    client, pid = seeded_client
    client.patch(
        f"/codebook/{pid}/codes/PROC-EXEC",
        headers=AUTH,
        json={"name": "Temp"},
    )
    r = client.delete(f"/codebook/{pid}/codes/PROC-EXEC", headers=AUTH)
    assert r.status_code == 204
    # Liste ist wieder leer.
    resp = client.get(f"/codebook/{pid}", headers=AUTH)
    assert resp.json() == []


def test_delete_nonexistent_code_is_204(seeded_client) -> None:
    """DELETE auf nicht existierenden Code ist idempotent -> 204."""

    client, pid = seeded_client
    r = client.delete(f"/codebook/{pid}/codes/NOPE", headers=AUTH)
    assert r.status_code == 204


def test_delete_bad_project(seeded_client) -> None:
    """DELETE auf nicht existierendes Projekt -> 404."""

    client, _pid = seeded_client
    r = client.delete("/codebook/9999/codes/PROC-EXEC", headers=AUTH)
    assert r.status_code == 404


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    "method,path_tmpl",
    [
        ("GET", "/codebook/{pid}"),
        ("PATCH", "/codebook/{pid}/codes/PROC-EXEC"),
        ("DELETE", "/codebook/{pid}/codes/PROC-EXEC"),
    ],
)
def test_endpoints_require_token(seeded_client, method: str, path_tmpl: str) -> None:
    """Ohne ``X-Sidecar-Token`` -> 401."""

    client, pid = seeded_client
    path = path_tmpl.format(pid=pid)
    resp = client.request(method, path, json={} if method == "PATCH" else None)
    assert resp.status_code == 401, (method, path, resp.status_code, resp.text)
