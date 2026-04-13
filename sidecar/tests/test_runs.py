# SPDX-License-Identifier: AGPL-3.0-only
"""Tests fuer den Runs-Router inkl. SSE-Stream (Welle 1)."""

from __future__ import annotations

import asyncio
import json
import threading
import time
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from qualdatan_sidecar import events_bridge
from qualdatan_sidecar.contract.app import build_app
from qualdatan_sidecar.contract.auth import TOKEN_ENV, TOKEN_HEADER
from qualdatan_sidecar.contract.models import ProgressEvent
from qualdatan_sidecar.deps import reset_app_db_singleton

_TOKEN = "test-token"
_HEADERS = {TOKEN_HEADER: _TOKEN}
_CFG = {"config": {"method": "mayring", "codebook": "hks"}, "materials": []}


@pytest.fixture()
def client(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> TestClient:
    monkeypatch.setenv(TOKEN_ENV, _TOKEN)
    monkeypatch.setenv("QUALDATAN_SIDECAR_APP_DB", str(tmp_path / "app.db"))
    reset_app_db_singleton()
    app = build_app()
    try:
        with TestClient(app) as c:
            yield c
    finally:
        reset_app_db_singleton()


def _make_project(client: TestClient, name: str = "HKS-1") -> str:
    resp = client.post(
        "/projects", json={"name": name, "company": "HKS"}, headers=_HEADERS
    )
    assert resp.status_code == 201, resp.text
    return resp.json()["id"]


def _make_run(client: TestClient, project_id: str) -> dict:
    resp = client.post(
        f"/projects/{project_id}/runs", json=_CFG, headers=_HEADERS
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


# ---------------------------------------------------------------------------
# CRUD
# ---------------------------------------------------------------------------


def test_create_run_returns_record(client: TestClient) -> None:
    pid = _make_project(client)
    run = _make_run(client, pid)
    assert run["project_id"] == pid
    assert run["status"] == "pending"
    assert run["config"]["method"] == "mayring"
    assert run["config"]["codebook"] == "hks"


def test_create_run_project_missing_404(client: TestClient) -> None:
    resp = client.post("/projects/999/runs", json=_CFG, headers=_HEADERS)
    assert resp.status_code == 404


def test_list_runs_filtered_and_unfiltered(client: TestClient) -> None:
    p1 = _make_project(client, "P1")
    p2 = _make_project(client, "P2")
    r1 = _make_run(client, p1)
    r2 = _make_run(client, p2)

    all_runs = client.get("/runs", headers=_HEADERS).json()
    assert {r["id"] for r in all_runs} == {r1["id"], r2["id"]}

    only_p1 = client.get(f"/runs?project_id={p1}", headers=_HEADERS).json()
    assert [r["id"] for r in only_p1] == [r1["id"]]


def test_get_run(client: TestClient) -> None:
    pid = _make_project(client)
    run = _make_run(client, pid)
    resp = client.get(f"/runs/{run['id']}", headers=_HEADERS)
    assert resp.status_code == 200
    assert resp.json()["id"] == run["id"]


def test_get_run_404(client: TestClient) -> None:
    assert client.get("/runs/999", headers=_HEADERS).status_code == 404
    assert client.get("/runs/abc", headers=_HEADERS).status_code == 404


# ---------------------------------------------------------------------------
# SSE
# ---------------------------------------------------------------------------


def _parse_sse(stream_text: str) -> list[dict]:
    """Parst eine SSE-Payload in eine Liste von ``{event, data}``-Dicts."""

    events: list[dict] = []
    current: dict[str, str] = {}
    for line in stream_text.splitlines():
        if not line:
            if current:
                events.append(current)
                current = {}
            continue
        if line.startswith("event:"):
            current["event"] = line[len("event:"):].strip()
        elif line.startswith("data:"):
            current["data"] = line[len("data:"):].strip()
    if current:
        events.append(current)
    return events


def test_stream_run_delivers_published_events(client: TestClient) -> None:
    pid = _make_project(client)
    run = _make_run(client, pid)
    run_id = run["id"]

    def _publish_soon() -> None:
        # Warten, bis der SSE-Subscriber registriert ist, dann publishen.
        for _ in range(50):
            time.sleep(0.05)
            # Interne Registry pruefen (Test-only).
            with events_bridge._lock:
                if events_bridge._subscribers.get(run_id):
                    break
        events_bridge.publish(
            ProgressEvent(event_type="started", run_id=run_id, message="go")
        )
        events_bridge.publish(
            ProgressEvent(
                event_type="material_progress",
                run_id=run_id,
                step="extract",
                pct=50.0,
            )
        )
        events_bridge.publish(
            ProgressEvent(event_type="finished", run_id=run_id, message="done")
        )

    thread = threading.Thread(target=_publish_soon, daemon=True)
    thread.start()

    with client.stream("GET", f"/runs/{run_id}/stream", headers=_HEADERS) as resp:
        assert resp.status_code == 200
        text = "".join(chunk for chunk in resp.iter_text())

    thread.join(timeout=5)

    events = _parse_sse(text)
    types = [e["event"] for e in events]
    assert types[:3] == ["started", "material_progress", "finished"]

    first = json.loads(events[0]["data"])
    assert first["run_id"] == run_id
    assert first["event_type"] == "started"

    second = json.loads(events[1]["data"])
    assert second["pct"] == 50.0
    assert second["step"] == "extract"


def test_stream_run_terminal_status_closes_immediately(
    client: TestClient, tmp_path: Path
) -> None:
    """Ein bereits abgeschlossener Run liefert genau ein Terminal-Event."""

    pid = _make_project(client)
    run = _make_run(client, pid)
    run_id = run["id"]

    # Run auf 'completed' setzen (Core-DAO).
    from qualdatan_core.app_db import projects as projects_dao

    from qualdatan_sidecar.deps import get_app_db

    projects_dao.update_run_status(get_app_db(), int(run_id), "completed")

    with client.stream("GET", f"/runs/{run_id}/stream", headers=_HEADERS) as resp:
        assert resp.status_code == 200
        text = "".join(chunk for chunk in resp.iter_text())

    events = _parse_sse(text)
    assert len(events) == 1
    assert events[0]["event"] == "finished"


def test_stream_run_404(client: TestClient) -> None:
    resp = client.get("/runs/999/stream", headers=_HEADERS)
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# events_bridge direct
# ---------------------------------------------------------------------------


def test_events_bridge_subscribe_publish_roundtrip() -> None:
    """Direkter Unit-Test der Bruecke ohne HTTP."""

    async def _runner() -> list[ProgressEvent]:
        collected: list[ProgressEvent] = []
        async with events_bridge.subscribe("unit-1") as stream:
            events_bridge.publish(
                ProgressEvent(event_type="started", run_id="unit-1")
            )
            events_bridge.publish(
                ProgressEvent(event_type="finished", run_id="unit-1")
            )
            async for evt in stream:
                collected.append(evt)
                if evt.event_type == "finished":
                    break
        return collected

    got = asyncio.run(_runner())
    assert [e.event_type for e in got] == ["started", "finished"]
