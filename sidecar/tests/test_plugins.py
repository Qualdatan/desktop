# SPDX-License-Identifier: AGPL-3.0-only
"""Tests fuer den Plugins-Router (Welle 1).

Die Tests verwenden einen Fake-PluginManager per
``app.dependency_overrides[get_plugin_manager]``. Der Plugin-Server-Client
wird per ``monkeypatch`` gegen einen In-Memory-Stub ersetzt, so dass keine
echten HTTP-Requests fliegen.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import pytest
from fastapi.testclient import TestClient

from qualdatan_plugins.manager import PluginManagerError
from qualdatan_plugins.server_client import PluginServerError, TapEntry, TapVersion
from qualdatan_sidecar.contract.app import build_app
from qualdatan_sidecar.contract.auth import TOKEN_ENV, TOKEN_HEADER
from qualdatan_sidecar.contract.routers import plugins as plugins_module
from qualdatan_sidecar.deps import get_plugin_manager


# ---------------------------------------------------------------------------
# Fake plumbing
# ---------------------------------------------------------------------------


@dataclass
class _FakeManifest:
    id: str
    version: str
    label: str = ""
    description: str = ""

    @property
    def name(self) -> str:
        return self.id.split("/", 1)[1]


@dataclass
class _FakeInstalled:
    manifest: _FakeManifest

    @property
    def id(self) -> str:
        return self.manifest.id

    @property
    def version(self) -> str:
        return self.manifest.version


@dataclass
class _FakeInstallResult:
    bundle: _FakeInstalled


class _FakeConn:
    """Minimaler SQLite-artiger Stub - unterstuetzt nur das eine Query."""

    def __init__(self, active: dict[str, list[str]]) -> None:
        self._active = active

    def execute(self, sql: str, params: tuple[Any, ...]) -> "_FakeCursor":
        # Der Router ruft: "SELECT project_id FROM active WHERE bundle_id=?"
        (bundle_id,) = params
        return _FakeCursor(self._active.get(bundle_id, []))


class _FakeCursor:
    def __init__(self, project_ids: list[str]) -> None:
        self._rows = [(p,) for p in project_ids]

    def fetchall(self) -> list[tuple[str]]:
        return self._rows


class _FakeRegistry:
    def __init__(self, installed: dict[str, _FakeInstalled], active: dict[str, list[str]]) -> None:
        self._installed = installed
        self._conn = _FakeConn(active)

    def get_installed(self, bundle_id: str, version: str | None = None) -> _FakeInstalled | None:
        return self._installed.get(bundle_id)


class FakeManager:
    """Stub der PluginManager-API, die der Router benoetigt."""

    def __init__(self) -> None:
        self._installed: dict[str, _FakeInstalled] = {}
        self._active: dict[str, list[str]] = {}
        self.registry = _FakeRegistry(self._installed, self._active)
        self.install_calls: list[tuple[str, str, str]] = []
        self.uninstall_calls: list[str] = []

    def list_installed(self) -> list[_FakeInstalled]:
        return list(self._installed.values())

    def install_from_git(self, repo_url: str, version: str, *, commit_sha: str = "") -> _FakeInstallResult:
        self.install_calls.append((repo_url, version, commit_sha))
        mf = _FakeManifest(
            id="qualdatan/bim-basic",
            version=version,
            label="BIM Basic",
            description="bundle for tests",
        )
        ib = _FakeInstalled(manifest=mf)
        self._installed[ib.id] = ib
        return _FakeInstallResult(bundle=ib)

    def uninstall(self, bundle_id: str, version: str | None = None) -> None:
        self.uninstall_calls.append(bundle_id)
        if bundle_id not in self._installed:
            raise PluginManagerError(f"Bundle '{bundle_id}' ist nicht installiert")
        del self._installed[bundle_id]
        self._active.pop(bundle_id, None)

    def activate(self, bundle_id: str, *, project_id: str = "", version: str | None = None) -> _FakeInstalled:
        if bundle_id not in self._installed:
            raise PluginManagerError(f"Bundle '{bundle_id}' ist nicht installiert")
        self._active.setdefault(bundle_id, [])
        if project_id not in self._active[bundle_id]:
            self._active[bundle_id].append(project_id)
        return self._installed[bundle_id]

    def deactivate(self, bundle_id: str, *, project_id: str = "") -> None:
        if bundle_id in self._active and project_id in self._active[bundle_id]:
            self._active[bundle_id].remove(project_id)


class _FakeServerClient:
    """Stub fuer :class:`PluginServerClient`.

    Verhalten wird per Klassenattributen gesteuert.
    """

    raise_on_search: bool = False
    raise_on_get_tap: bool = False
    search_results: list[TapEntry] = []
    tap_entry: TapEntry | None = None
    tap_versions: list[TapVersion] = []

    def __enter__(self) -> "_FakeServerClient":
        return self

    def __exit__(self, *a: object) -> None:  # pragma: no cover
        return None

    def search(self, query: str = "", *, limit: int = 25) -> list[TapEntry]:
        if self.raise_on_search:
            raise PluginServerError("boom")
        return list(self.search_results)

    def get_tap(self, namespace: str, name: str) -> tuple[TapEntry, list[TapVersion]]:
        if self.raise_on_get_tap or self.tap_entry is None:
            raise PluginServerError("unreachable")
        return self.tap_entry, list(self.tap_versions)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def fake_manager() -> FakeManager:
    return FakeManager()


@pytest.fixture()
def client(
    monkeypatch: pytest.MonkeyPatch, fake_manager: FakeManager
) -> TestClient:
    monkeypatch.setenv(TOKEN_ENV, "test-token")
    # Jeder Test beginnt mit frischem FakeServerClient-Zustand.
    _FakeServerClient.raise_on_search = False
    _FakeServerClient.raise_on_get_tap = False
    _FakeServerClient.search_results = []
    _FakeServerClient.tap_entry = None
    _FakeServerClient.tap_versions = []
    monkeypatch.setattr(plugins_module, "PluginServerClient", _FakeServerClient)

    app = build_app()
    app.dependency_overrides[get_plugin_manager] = lambda: fake_manager
    tc = TestClient(app)
    tc.headers.update({TOKEN_HEADER: "test-token"})
    return tc


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_list_plugins_empty(client: TestClient) -> None:
    resp = client.get("/plugins")
    assert resp.status_code == 200
    assert resp.json() == []


def test_install_plugin_happy_path(
    client: TestClient, fake_manager: FakeManager
) -> None:
    _FakeServerClient.tap_entry = TapEntry(
        namespace="qualdatan",
        name="bim-basic",
        repo_url="https://github.com/qualdatan/bim-basic",
        latest_version="0.2.0",
        label="BIM Basic",
        description="basic bim bundle",
        keywords=(),
        license="AGPL-3.0-only",
    )
    _FakeServerClient.tap_versions = [
        TapVersion(version="0.2.0", tag="v0.2.0", commit_sha="deadbeef", published_at="")
    ]

    resp = client.post(
        "/plugins/install", json={"bundle_id": "qualdatan/bim-basic"}
    )
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["bundle_id"] == "qualdatan/bim-basic"
    assert body["version"] == "0.2.0"
    assert body["name"] == "BIM Basic"

    # Manager wurde mit richtigen Args aufgerufen.
    assert fake_manager.install_calls == [
        ("https://github.com/qualdatan/bim-basic", "0.2.0", "deadbeef")
    ]


def test_install_plugin_server_unreachable_returns_502(client: TestClient) -> None:
    # Kein tap_entry -> get_tap wirft PluginServerError.
    resp = client.post(
        "/plugins/install", json={"bundle_id": "qualdatan/bim-basic"}
    )
    assert resp.status_code == 502


def test_uninstall_plugin(
    client: TestClient, fake_manager: FakeManager
) -> None:
    # Hinweis: Der frozen contract definiert ``{bundle_id}`` als einfachen
    # Path-Param; Starlette decodiert ``%2F`` vor dem Routing, daher kann ein
    # echter ``namespace/name``-Bundle-Id-String in einer URL nicht ohne
    # Serveranpassung (``:path``-Converter) ankommen. Fuer diesen Wiring-Test
    # nutzen wir einen Bundle-Id-Stub ohne Slash.
    fake_manager._installed["testbundle"] = _FakeInstalled(
        manifest=_FakeManifest(id="testbundle", version="0.1.0")
    )

    resp = client.post("/plugins/testbundle/uninstall")
    assert resp.status_code == 204
    assert fake_manager.uninstall_calls == ["testbundle"]
    assert "testbundle" not in fake_manager._installed

    # Zweiter Aufruf -> 404.
    resp2 = client.post("/plugins/testbundle/uninstall")
    assert resp2.status_code == 404


def test_enable_and_disable_plugin_for_project(
    client: TestClient, fake_manager: FakeManager
) -> None:
    # Wiring-Test mit slash-losem Bundle-Id (siehe Hinweis in
    # ``test_uninstall_plugin``).
    fake_manager._installed["testbundle"] = _FakeInstalled(
        manifest=_FakeManifest(id="testbundle", version="0.1.0", label="BIM Basic")
    )

    # Enable
    resp = client.post("/projects/proj-1/plugins/testbundle/enable")
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["bundle_id"] == "testbundle"
    assert "proj-1" in body["enabled_in_projects"]

    # list_plugins reflektiert Aktivierung.
    listed = client.get("/plugins").json()
    assert listed[0]["enabled_in_projects"] == ["proj-1"]

    # Disable
    resp2 = client.post("/projects/proj-1/plugins/testbundle/disable")
    assert resp2.status_code == 200, resp2.text
    body2 = resp2.json()
    assert body2["enabled_in_projects"] == []


def test_enable_unknown_bundle_returns_404(client: TestClient) -> None:
    resp = client.post("/projects/proj-1/plugins/nonexistent/enable")
    assert resp.status_code == 404


def test_available_plugins_unreachable_returns_empty(client: TestClient) -> None:
    _FakeServerClient.raise_on_search = True
    resp = client.get("/plugins/available")
    assert resp.status_code == 200
    assert resp.json() == []


def test_available_plugins_returns_entries(client: TestClient) -> None:
    _FakeServerClient.search_results = [
        TapEntry(
            namespace="qualdatan",
            name="bim-basic",
            repo_url="https://github.com/qualdatan/bim-basic",
            latest_version="0.2.0",
            label="BIM Basic",
            description="basic bim bundle",
            keywords=(),
            license="AGPL-3.0-only",
        )
    ]
    resp = client.get("/plugins/available")
    assert resp.status_code == 200
    body = resp.json()
    assert len(body) == 1
    assert body[0]["bundle_id"] == "qualdatan/bim-basic"
    assert body[0]["download_url"] == "https://github.com/qualdatan/bim-basic"
    assert body[0]["version"] == "0.2.0"
