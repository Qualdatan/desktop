# SPDX-License-Identifier: AGPL-3.0-only
"""Bootstrap- und Handshake-Modul fuer den Qualdatan-Sidecar.

Die Tauri-Shell spawnt den Sidecar als Subprozess. Vor dem Start der
FastAPI-App muss der Sidecar einen freien Loopback-Port waehlen, ein
frisches Session-Token erzeugen und beide Werte als einzeilige
JSON-Handshake-Zeile auf ``stdout`` ausgeben. Anschliessend startet
uvicorn gebunden an ``127.0.0.1:<port>`` mit gesetzter
``QUALDATAN_SIDECAR_TOKEN``-Umgebungsvariable, damit das bestehende
:func:`qualdatan_sidecar.contract.auth.verify_token`-Gate das Token
akzeptiert.

Example:
    ``python -m qualdatan_sidecar`` oder Konsolen-Skript
    ``qualdatan-sidecar`` startet den Handshake und die App.
"""

from __future__ import annotations

import argparse
import json
import os
import secrets
import socket
import sys
from typing import Sequence

import uvicorn

_TOKEN_ENV_VAR = "QUALDATAN_SIDECAR_TOKEN"


def pick_free_port(host: str = "127.0.0.1") -> int:
    """Waehlt einen freien TCP-Port auf ``host`` via Ephemeral-Bind.

    Args:
        host: Interface, auf dem gesucht wird. Default Loopback.

    Returns:
        Port-Nummer (1024-65535), den das Betriebssystem als frei
        gemeldet hat. Es gibt ein Race-Fenster zwischen Close und
        erneutem Bind; fuer den Sidecar-Handshake toleriert.
    """

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind((host, 0))
        return int(sock.getsockname()[1])


def generate_token() -> str:
    """Erzeugt ein URL-sicheres Session-Token.

    Returns:
        Mindestens 32 Zeichen lange URL-safe-Base64-Zeichenkette
        (``secrets.token_urlsafe(32)`` liefert ~43 Zeichen).
    """

    return secrets.token_urlsafe(32)


def handshake_payload(port: int, token: str) -> str:
    """Serialisiert die Handshake-Zeile.

    Args:
        port: Port, auf dem uvicorn gebunden wird.
        token: Session-Token, identisch zu ``QUALDATAN_SIDECAR_TOKEN``.

    Returns:
        Einzeilige JSON-Zeichenkette ``{"port": ..., "token": "..."}``
        ohne Zeilenumbruch und ohne verschachtelte Objekte.
    """

    return json.dumps({"port": int(port), "token": str(token)}, separators=(",", ":"))


def serve(
    *,
    host: str = "127.0.0.1",
    port: int | None = None,
    token: str | None = None,
) -> None:
    """Druckt Handshake und startet uvicorn.

    Args:
        host: Bind-Interface, default Loopback.
        port: Optionaler fester Port; sonst ephemerer freier Port.
        token: Optionales festes Token; sonst frisch generiert.
            Wenn ``QUALDATAN_SIDECAR_TOKEN`` bereits in der Env
            gesetzt ist und ``token`` ``None``, wird der vorhandene
            Env-Wert wiederverwendet.

    Returns:
        Kehrt erst zurueck, wenn uvicorn beendet.
    """

    if port is None:
        port = pick_free_port(host)
    if token is None:
        token = os.environ.get(_TOKEN_ENV_VAR) or generate_token()

    # Token in Env schreiben, damit verify_token es akzeptiert.
    os.environ[_TOKEN_ENV_VAR] = token

    # Handshake-Zeile auf stdout (Tauri liest exakt diese Zeile).
    print(handshake_payload(port, token), flush=True)

    uvicorn.run(
        "qualdatan_sidecar.contract.app:build_app",
        factory=True,
        host=host,
        port=port,
        log_level="info",
    )


def _build_parser() -> argparse.ArgumentParser:
    """Baut den argparse-Parser fuer ``main()``."""

    parser = argparse.ArgumentParser(
        prog="qualdatan-sidecar",
        description="Qualdatan Sidecar: Handshake + uvicorn-Launcher.",
    )
    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="Bind-Interface (default: 127.0.0.1).",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=None,
        help="Fester Port; sonst ephemerer freier Port.",
    )
    parser.add_argument(
        "--token",
        default=None,
        help="Festes Session-Token; sonst frisch generiert.",
    )
    parser.add_argument(
        "--print-handshake-only",
        action="store_true",
        help=(
            "Druckt nur die Handshake-Zeile und beendet sich, ohne "
            "uvicorn zu starten. Primaer fuer Tests/Smoke-Check."
        ),
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Konsolen-Skript-Entry (``[project.scripts]``).

    Args:
        argv: Optionale Argumentliste; default ``sys.argv[1:]``.

    Returns:
        Exit-Code (0 bei Erfolg). Blockiert normalerweise bis
        uvicorn terminiert; mit ``--print-handshake-only`` kehrt
        sofort zurueck.
    """

    parser = _build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)

    host: str = args.host
    port: int = args.port if args.port is not None else pick_free_port(host)
    token: str = args.token or os.environ.get(_TOKEN_ENV_VAR) or generate_token()

    if args.print_handshake_only:
        print(handshake_payload(port, token), flush=True)
        return 0

    serve(host=host, port=port, token=token)
    return 0


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())


__all__ = [
    "pick_free_port",
    "generate_token",
    "handshake_payload",
    "serve",
    "main",
]
