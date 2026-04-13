# SPDX-License-Identifier: AGPL-3.0-only
"""Modul-Entry: ``python -m qualdatan_sidecar``.

Ruft :func:`qualdatan_sidecar.bootstrap.main` auf, das den Handshake
druckt und uvicorn startet.
"""

from __future__ import annotations

import sys

from qualdatan_sidecar.bootstrap import main

if __name__ == "__main__":
    sys.exit(main())
