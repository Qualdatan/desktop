# SPDX-License-Identifier: AGPL-3.0-only
"""Qualdatan sidecar: FastAPI app that exposes qualdatan-core and
qualdatan-plugins over a loopback HTTP API for the Tauri desktop frontend.

Phase F fills in ``app``, ``handshake`` (stdin port+token negotiation),
``routes`` (projects, runs, codebook, export, plugins) and the SSE
progress stream.
"""

__version__ = "0.1.0"
