# SPDX-License-Identifier: AGPL-3.0-only
"""PyInstaller entry script for the Qualdatan sidecar.

PyInstaller handles a concrete script path much more reliably than the
``python -m qualdatan_sidecar`` module invocation. This file is therefore
the *only* entry point referenced from ``qualdatan_sidecar.spec``; it simply
forwards to :func:`qualdatan_sidecar.bootstrap.main`.
"""

from __future__ import annotations

from qualdatan_sidecar.bootstrap import main


if __name__ == "__main__":
    main()
