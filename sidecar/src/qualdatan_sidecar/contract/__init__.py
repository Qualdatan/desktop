# SPDX-License-Identifier: AGPL-3.0-only
"""Frozen FastAPI contract for the Qualdatan sidecar.

Dieses Subpackage enthaelt **nur** die API-Form (Pydantic-Modelle,
Router-Signaturen, OpenAPI-Export). Die eigentliche Implementierung
(Orchestrator-Anbindung, Persistenz, Plugin-Bridging) wandert in Welle 1
in dieses Paket. Welle 2 generiert den Frontend-Client aus der
eingecheckten ``openapi.json``.
"""

from qualdatan_sidecar import __version__

__all__ = ["__version__"]
