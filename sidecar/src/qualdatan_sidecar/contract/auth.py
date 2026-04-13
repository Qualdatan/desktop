# SPDX-License-Identifier: AGPL-3.0-only
"""Token-Gate fuer die Sidecar-API.

Der Tauri-Shell fuettert das Token ueber den Stdin-Handshake in die
Sidecar-Prozessumgebung (``QUALDATAN_SIDECAR_TOKEN``). Jeder HTTP-Request
(ausser ``/healthz``) muss denselben Token im Header ``X-Sidecar-Token``
mitsenden, sonst antwortet die API mit ``401``.
"""

from __future__ import annotations

import os
import secrets

from fastapi import Header, HTTPException, status

TOKEN_ENV = "QUALDATAN_SIDECAR_TOKEN"
"""Name der Env-Var, aus der der erwartete Token gelesen wird."""

TOKEN_HEADER = "X-Sidecar-Token"
"""Name des HTTP-Headers, in dem der Client den Token senden muss."""


def _expected_token() -> str | None:
    """Liefert den erwarteten Token aus der Umgebung (oder ``None``).

    Returns:
        Den konfigurierten Token oder ``None``, wenn die Env-Var nicht
        gesetzt ist (dann gilt: **jeder Request ausser Health ist 401**,
        weil der Vergleich nie glueckt).
    """

    value = os.environ.get(TOKEN_ENV)
    if value is None or value == "":
        return None
    return value


async def verify_token(
    x_sidecar_token: str | None = Header(default=None, alias=TOKEN_HEADER),
) -> None:
    """FastAPI-Dependency: prueft den ``X-Sidecar-Token`` Header.

    Args:
        x_sidecar_token: Vom Client mitgelieferter Token.

    Raises:
        HTTPException: ``401``, wenn Header fehlt, Env-Var nicht gesetzt
            ist, oder die Werte nicht uebereinstimmen.
    """

    expected = _expected_token()
    if expected is None or x_sidecar_token is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid sidecar token.",
        )
    if not secrets.compare_digest(expected, x_sidecar_token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid sidecar token.",
        )
