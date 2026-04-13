# SPDX-License-Identifier: AGPL-3.0-only
# -*- mode: python ; coding: utf-8 -*-
#
# PyInstaller spec for the Qualdatan sidecar.
#
# Build locally:
#     uv sync
#     uv run pyinstaller qualdatan_sidecar.spec --noconfirm --clean
#
# Output:
#     dist/qualdatan-sidecar        (Linux/macOS)
#     dist/qualdatan-sidecar.exe    (Windows)
#
# The Tauri bundler expects the binary under
# ``repos/desktop/src-tauri/binaries/`` with the Rust target triple appended
# to the filename (see ``tauri.conf.json`` -> ``externalBin``). The
# rename/move step lives in the GitHub Actions workflow so this spec stays
# platform-neutral.

from PyInstaller.utils.hooks import collect_submodules

block_cipher = None

# uvicorn/fastapi/pydantic load a lot of things lazily; collect everything
# we can so cold-start inside the one-file bundle does not explode.
hiddenimports = []
for pkg in (
    "uvicorn",
    "uvicorn.logging",
    "uvicorn.loops",
    "uvicorn.loops.auto",
    "uvicorn.protocols",
    "uvicorn.protocols.http",
    "uvicorn.protocols.http.auto",
    "uvicorn.protocols.websockets",
    "uvicorn.protocols.websockets.auto",
    "uvicorn.lifespan",
    "uvicorn.lifespan.on",
    "fastapi",
    "sse_starlette",
    "pydantic",
    "pydantic.deprecated.decorator",
    "platformdirs",
    "qualdatan_core",
    "qualdatan_plugins",
    "qualdatan_sidecar",
):
    hiddenimports.extend(collect_submodules(pkg))


a = Analysis(
    ["sidecar_entry.py"],
    pathex=["src"],
    binaries=[],
    datas=[],
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # Test frameworks and GUI toolkits that would otherwise get vacuumed
        # up transitively and bloat the one-file bundle.
        "tkinter",
        "pytest",
        "IPython",
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name="qualdatan-sidecar",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    # console=False: no terminal window pops up at launch. Tauri reads the
    # handshake JSON via piped stdout regardless of this flag.
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
