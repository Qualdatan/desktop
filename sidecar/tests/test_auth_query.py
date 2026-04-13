# SPDX-License-Identifier: AGPL-3.0-only
"""Tests fuer den Query-Param-Fallback der Token-Authentifizierung.

Hintergrund: Der Browser-``EventSource`` (verwendet vom RunMonitor fuer
``/runs/{id}/stream``) kann keine Custom-Header setzen. Daher akzeptiert
``verify_token`` zusaetzlich zum Header ``X-Sidecar-Token`` auch den
Query-Parameter ``?token=...``. Der Header hat Vorrang.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from qualdatan_sidecar.contract.app import build_app
from qualdatan_sidecar.contract.auth import TOKEN_ENV, TOKEN_HEADER


@pytest.fixture()
def app_with_token(monkeypatch: pytest.MonkeyPatch):
    """Setzt einen Dummy-Token und baut die App."""

    monkeypatch.setenv(TOKEN_ENV, "test-token")
    return build_app()


def test_query_param_grants_access(app_with_token) -> None:
    """``?token=<valid>`` ohne Header -> kein 401 (EventSource-Fall)."""

    client = TestClient(app_with_token, raise_server_exceptions=False)
    resp = client.get("/projects?token=test-token")
    assert resp.status_code != 401, resp.text


def test_query_param_wrong_token_rejected(app_with_token) -> None:
    """``?token=wrong`` -> 401."""

    client = TestClient(app_with_token)
    resp = client.get("/projects?token=wrong-token")
    assert resp.status_code == 401


def test_query_param_empty_rejected(app_with_token) -> None:
    """``?token=`` (leer) -> 401."""

    client = TestClient(app_with_token)
    resp = client.get("/projects?token=")
    assert resp.status_code == 401


def test_header_still_works(app_with_token) -> None:
    """Der Header-Pfad darf durch den Query-Fallback nicht regressieren."""

    client = TestClient(app_with_token, raise_server_exceptions=False)
    resp = client.get("/projects", headers={TOKEN_HEADER: "test-token"})
    assert resp.status_code != 401, resp.text


def test_header_takes_precedence_over_query(app_with_token) -> None:
    """Header hat Vorrang: gueltiger Header + falscher Query -> durch."""

    client = TestClient(app_with_token, raise_server_exceptions=False)
    resp = client.get(
        "/projects?token=wrong-token",
        headers={TOKEN_HEADER: "test-token"},
    )
    assert resp.status_code != 401, resp.text


def test_wrong_header_not_rescued_by_valid_query(app_with_token) -> None:
    """Header hat Vorrang: falscher Header bleibt 401, auch wenn Query gueltig.

    Konsequenz der Precedence-Regel: sobald der Header gesetzt ist, wird
    nur dieser geprueft; ein zusaetzlicher gueltiger Query-Param kann das
    nicht kompensieren.
    """

    client = TestClient(app_with_token)
    resp = client.get(
        "/projects?token=test-token",
        headers={TOKEN_HEADER: "wrong-token"},
    )
    assert resp.status_code == 401


def test_no_header_no_query_rejected(app_with_token) -> None:
    """Weder Header noch Query -> 401 (Regressionsschutz)."""

    client = TestClient(app_with_token)
    resp = client.get("/projects")
    assert resp.status_code == 401
