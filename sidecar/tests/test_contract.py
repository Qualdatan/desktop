# SPDX-License-Identifier: AGPL-3.0-only
"""Tests fuer den gefrorenen Sidecar-Kontrakt.

Diese Tests pruefen **nur die Form**:

* ``build_app()`` konstruiert die FastAPI-Instanz ohne Fehler.
* Alle erwarteten Pfade sind registriert.
* ``/healthz`` ist ohne Token erreichbar.
* Alle anderen Endpunkte antworten ohne Token mit 401.
* ``dump_openapi`` erzeugt exakt die eingecheckte ``openapi.json``.

Die Endpoint-Koerper (Welle 1) sind explizit **nicht** getestet - sie
werfen ``NotImplementedError``.
"""

from __future__ import annotations

import os

import pytest
from fastapi.testclient import TestClient

from qualdatan_sidecar.contract.app import build_app
from qualdatan_sidecar.contract.auth import TOKEN_ENV, TOKEN_HEADER
from qualdatan_sidecar.contract.dump_openapi import OPENAPI_PATH, render_openapi

EXPECTED_PATHS = {
    "/healthz",
    "/projects",
    "/projects/{project_id}",
    "/projects/{project_id}/runs",
    "/runs",
    "/runs/{run_id}",
    "/runs/{run_id}/stream",
    "/codebook/{project_id}",
    "/codebook/{project_id}/codes/{code_id}",
    "/plugins",
    "/plugins/install",
    "/plugins/{bundle_id}/uninstall",
    "/projects/{project_id}/plugins/{bundle_id}/enable",
    "/projects/{project_id}/plugins/{bundle_id}/disable",
    "/plugins/available",
    "/export/qdpx",
    "/export/xlsx",
}

# Irgendein Nicht-Health-Endpoint, der *ohne* Token 401 liefern muss.
UNAUTH_SAMPLES = [
    ("GET", "/projects"),
    ("GET", "/runs"),
    ("GET", "/codebook/proj-123"),
    ("GET", "/plugins"),
    ("POST", "/export/qdpx"),
]


@pytest.fixture()
def app_with_token(monkeypatch: pytest.MonkeyPatch):
    """Setzt einen Dummy-Token und baut die App."""

    monkeypatch.setenv(TOKEN_ENV, "test-token")
    return build_app()


def test_build_app_registers_all_paths(app_with_token) -> None:
    """Alle erwarteten Routen existieren."""

    registered = {route.path for route in app_with_token.routes if hasattr(route, "path")}
    missing = EXPECTED_PATHS - registered
    assert not missing, f"missing routes: {missing}"


def test_healthz_is_open(app_with_token) -> None:
    """``/healthz`` braucht keinen Token."""

    client = TestClient(app_with_token)
    resp = client.get("/healthz")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert "version" in data


@pytest.mark.parametrize("method,path", UNAUTH_SAMPLES)
def test_other_endpoints_require_token(app_with_token, method: str, path: str) -> None:
    """Ohne ``X-Sidecar-Token`` -> 401 auf allen Nicht-Health-Endpunkten."""

    client = TestClient(app_with_token)
    resp = client.request(method, path)
    assert resp.status_code == 401, (method, path, resp.status_code, resp.text)


def test_healthz_open_even_without_env_token(monkeypatch: pytest.MonkeyPatch) -> None:
    """Health funktioniert auch, wenn der Env-Token gar nicht gesetzt ist."""

    monkeypatch.delenv(TOKEN_ENV, raising=False)
    app = build_app()
    client = TestClient(app)
    assert client.get("/healthz").status_code == 200
    # Nicht-Health antwortet ohne Env-Token trotzdem mit 401.
    assert client.get("/projects").status_code == 401


def test_token_header_accepts_valid_token(app_with_token) -> None:
    """Mit korrektem Header kommt der Request an den Endpoint-Body durch
    (der ``NotImplementedError`` wirft - also 500, nicht 401)."""

    client = TestClient(app_with_token, raise_server_exceptions=False)
    resp = client.get("/projects", headers={TOKEN_HEADER: "test-token"})
    assert resp.status_code != 401, resp.text


def test_dump_openapi_matches_checked_in_file() -> None:
    """Die eingecheckte ``openapi.json`` ist identisch mit dem frischen Dump."""

    # Fuer einen reproduzierbaren Dump muss der Token-Env nicht gesetzt sein;
    # die OpenAPI-Generierung ist unabhaengig davon.
    os.environ.pop(TOKEN_ENV, None)
    assert OPENAPI_PATH.exists(), f"run `python -m qualdatan_sidecar.contract.dump_openapi` (missing {OPENAPI_PATH})"
    on_disk = OPENAPI_PATH.read_text(encoding="utf-8")
    fresh = render_openapi()
    assert on_disk == fresh, "openapi.json is stale; re-run dump_openapi"
