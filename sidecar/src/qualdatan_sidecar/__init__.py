# SPDX-License-Identifier: AGPL-3.0-only
"""Qualdatan sidecar: FastAPI app that exposes qualdatan-core and
qualdatan-plugins over a loopback HTTP API for the Tauri desktop frontend.

Phase F freezes the contract (Pydantic models + endpoint signatures);
Welle 1 fills in endpoint bodies, Welle 2 generates the frontend client
from the checked-in ``contract/openapi.json``.
"""

__version__ = "0.1.0"
