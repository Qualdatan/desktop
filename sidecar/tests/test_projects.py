# SPDX-License-Identifier: AGPL-3.0-only
"""Tests fuer den Projects-Router (Welle 1)."""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from qualdatan_sidecar.contract.app import build_app
from qualdatan_sidecar.contract.auth import TOKEN_ENV, TOKEN_HEADER
from qualdatan_sidecar.deps import reset_app_db_singleton

_TOKEN = "test-token"
_HEADERS = {TOKEN_HEADER: _TOKEN}


@pytest.fixture()
def client(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> TestClient:
    """TestClient mit frischer App-DB und gesetztem Token."""

    monkeypatch.setenv(TOKEN_ENV, _TOKEN)
    monkeypatch.setenv("QUALDATAN_SIDECAR_APP_DB", str(tmp_path / "app.db"))
    reset_app_db_singleton()
    app = build_app()
    try:
        with TestClient(app) as c:
            yield c
    finally:
        reset_app_db_singleton()


def _create(client: TestClient, name: str, company: str = "HKS", desc: str | None = None):
    payload: dict[str, object] = {"name": name, "company": company}
    if desc is not None:
        payload["description"] = desc
    resp = client.post("/projects", json=payload, headers=_HEADERS)
    assert resp.status_code == 201, resp.text
    return resp.json()


def test_create_project_returns_persisted_record(client: TestClient) -> None:
    data = _create(client, "HKS-Alpha", company="HKS", desc="Bauprojekt 1")
    assert data["name"] == "HKS-Alpha"
    assert data["company"] == "HKS"
    assert data["description"] == "Bauprojekt 1"
    assert data["id"]
    assert data["created_at"]
    assert data["updated_at"]


def test_list_projects_empty_then_populated(client: TestClient) -> None:
    assert client.get("/projects", headers=_HEADERS).json() == []
    _create(client, "A")
    _create(client, "B", company="PBN")
    items = client.get("/projects", headers=_HEADERS).json()
    assert {p["name"] for p in items} == {"A", "B"}


def test_get_project_by_id(client: TestClient) -> None:
    created = _create(client, "HKS-Gamma")
    resp = client.get(f"/projects/{created['id']}", headers=_HEADERS)
    assert resp.status_code == 200
    assert resp.json()["name"] == "HKS-Gamma"


def test_get_project_404(client: TestClient) -> None:
    assert client.get("/projects/999", headers=_HEADERS).status_code == 404
    # Nicht-numerische ID -> ebenfalls 404 (Projekt existiert nicht).
    assert client.get("/projects/nope", headers=_HEADERS).status_code == 404


def test_patch_project_partial(client: TestClient) -> None:
    created = _create(client, "Orig", company="HKS", desc="alt")
    pid = created["id"]
    resp = client.patch(
        f"/projects/{pid}",
        json={"description": "neu"},
        headers=_HEADERS,
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["description"] == "neu"
    assert body["name"] == "Orig"  # unveraendert
    assert body["company"] == "HKS"


def test_patch_project_404(client: TestClient) -> None:
    resp = client.patch("/projects/999", json={"name": "x"}, headers=_HEADERS)
    assert resp.status_code == 404


def test_delete_project(client: TestClient) -> None:
    created = _create(client, "ToDelete")
    pid = created["id"]
    resp = client.delete(f"/projects/{pid}", headers=_HEADERS)
    assert resp.status_code == 204
    # Danach 404.
    assert client.get(f"/projects/{pid}", headers=_HEADERS).status_code == 404


def test_delete_project_404(client: TestClient) -> None:
    resp = client.delete("/projects/999", headers=_HEADERS)
    assert resp.status_code == 404
