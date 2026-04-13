# SPDX-License-Identifier: AGPL-3.0-only
"""Tests fuer :mod:`qualdatan_sidecar.bootstrap`.

Validiert die Handshake-Helfer ohne Netzwerk- oder uvicorn-Start:
``pick_free_port``, ``generate_token``, ``handshake_payload`` sowie
die ``main(--print-handshake-only)``-Variante, die deterministisch
ohne Server-Boot ausloest.
"""

from __future__ import annotations

import json
import socket

import pytest

from qualdatan_sidecar import bootstrap


def test_pick_free_port_returns_usable_port() -> None:
    """``pick_free_port`` liefert einen Loopback-Port, den wir binden koennen."""

    port = bootstrap.pick_free_port()
    assert isinstance(port, int)
    assert 1024 <= port <= 65535

    # Port sollte nach Close erneut bindbar sein.
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", port))


def test_generate_token_is_urlsafe_and_long_enough() -> None:
    """Token ist URL-safe und hat >= 32 Zeichen."""

    token = bootstrap.generate_token()
    assert isinstance(token, str)
    assert len(token) >= 32
    allowed = set(
        "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_"
    )
    assert set(token).issubset(allowed)
    # Zwei Aufrufe duerfen nicht kollidieren.
    assert bootstrap.generate_token() != token


def test_handshake_payload_roundtrips_via_json_loads() -> None:
    """``handshake_payload`` ist einzeilig und JSON-roundtrip-fest."""

    line = bootstrap.handshake_payload(5123, "tok-abc")
    assert "\n" not in line
    parsed = json.loads(line)
    assert parsed == {"port": 5123, "token": "tok-abc"}


def test_main_print_handshake_only_exits_without_starting_uvicorn(
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """``main(--print-handshake-only)`` druckt Handshake und kehrt zurueck."""

    def _boom(*_a: object, **_k: object) -> None:
        raise AssertionError("uvicorn.run darf nicht aufgerufen werden")

    monkeypatch.setattr(bootstrap.uvicorn, "run", _boom)

    rc = bootstrap.main(
        ["--port", "5432", "--token", "deterministic-token", "--print-handshake-only"]
    )
    assert rc == 0

    out = capsys.readouterr().out.strip()
    parsed = json.loads(out)
    assert parsed == {"port": 5432, "token": "deterministic-token"}


def test_main_print_handshake_only_generates_port_and_token_when_omitted(
    capsys: pytest.CaptureFixture[str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Ohne ``--port``/``--token`` werden Werte generiert."""

    monkeypatch.delenv("QUALDATAN_SIDECAR_TOKEN", raising=False)
    monkeypatch.setattr(bootstrap.uvicorn, "run", lambda *a, **k: None)

    rc = bootstrap.main(["--print-handshake-only"])
    assert rc == 0

    parsed = json.loads(capsys.readouterr().out.strip())
    assert isinstance(parsed["port"], int)
    assert 1024 <= parsed["port"] <= 65535
    assert isinstance(parsed["token"], str)
    assert len(parsed["token"]) >= 32
