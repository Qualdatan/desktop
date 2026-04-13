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

from fastapi import Header, HTTPException, Request, status

TOKEN_ENV = "QUALDATAN_SIDECAR_TOKEN"
"""Name der Env-Var, aus der der erwartete Token gelesen wird."""

TOKEN_HEADER = "X-Sidecar-Token"
"""Name des HTTP-Headers, in dem der Client den Token senden muss."""

TOKEN_QUERY_PARAM = "token"
"""Name des Query-Parameters als Fallback fuer Clients, die keine Header
setzen koennen (z.B. der Browser-``EventSource`` fuer SSE)."""


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
    request: Request,
    x_sidecar_token: str | None = Header(default=None, alias=TOKEN_HEADER),
) -> None:
    """FastAPI-Dependency: prueft den Sidecar-Token.

    Der Token wird primaer aus dem Header ``X-Sidecar-Token`` gelesen.
    Fehlt dieser, wird als Fallback der Query-Parameter ``?token=``
    ausgewertet - das ist noetig, weil der Browser-``EventSource``
    keine Custom-Header unterstuetzt und der Frontend-RunMonitor den
    Token daher an die SSE-URL anhaengt.

    Args:
        request: Der eingehende Request (fuer den Query-Fallback).
        x_sidecar_token: Vom Client mitgelieferter Token (Header).

    Raises:
        HTTPException: ``401``, wenn weder Header noch Query-Param
            gesetzt sind, die Env-Var nicht gesetzt ist, oder die
            Werte nicht uebereinstimmen.
    """

    expected = _expected_token()
    if expected is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid sidecar token.",
        )

    # Header hat Vorrang; Query-Param ist Fallback fuer EventSource.
    provided = x_sidecar_token
    if provided is None:
        provided = request.query_params.get(TOKEN_QUERY_PARAM)

    if provided is None or not secrets.compare_digest(expected, provided):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid sidecar token.",
        )
