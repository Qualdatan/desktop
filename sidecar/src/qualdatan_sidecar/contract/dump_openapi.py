# SPDX-License-Identifier: AGPL-3.0-only
"""Schreibt die OpenAPI-Spec des gefrorenen Sidecar-Kontrakts auf Platte.

Aufruf::

    python -m qualdatan_sidecar.contract.dump_openapi

Der Dump ist deterministisch (``sort_keys=True``, ``indent=2``, trailing
newline) und wird nach ``repos/desktop/sidecar/contract/openapi.json``
geschrieben. Der Dump **wird eingecheckt**, damit das Frontend (Welle 2)
den Client ohne laufenden Sidecar generieren kann und CI einen Drift
zwischen Code und gecheckter Spec erkennt.
"""

from __future__ import annotations

import json
from pathlib import Path

from .app import build_app

# contract/ dir beside this file -> sidecar/contract/openapi.json
_REPO_CONTRACT_DIR = Path(__file__).resolve().parents[3] / "contract"
OPENAPI_PATH = _REPO_CONTRACT_DIR / "openapi.json"
"""Pfad der eingecheckten OpenAPI-Spec (``<sidecar>/contract/openapi.json``)."""


def render_openapi() -> str:
    """Rendert die OpenAPI-Spec als deterministischen JSON-String.

    Returns:
        JSON-Text mit ``sort_keys=True``, ``indent=2`` und trailing
        newline.
    """

    spec = build_app().openapi()
    return json.dumps(spec, sort_keys=True, indent=2, ensure_ascii=False) + "\n"


def write_openapi(path: Path = OPENAPI_PATH) -> Path:
    """Schreibt die Spec nach ``path``.

    Args:
        path: Zielpfad. Default: :data:`OPENAPI_PATH`.

    Returns:
        Der geschriebene Pfad.
    """

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(render_openapi(), encoding="utf-8")
    return path


def main() -> None:
    """CLI-Einstieg fuer ``python -m qualdatan_sidecar.contract.dump_openapi``."""

    out = write_openapi()
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
