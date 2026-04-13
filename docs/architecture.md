# Architecture

Drei Prozesse, ein Installer-Paket.

```
+------------------+       IPC       +----------------------+
|  Tauri-Shell     | <-------------> |  React-Frontend      |
|  (Rust,          |   invoke()      |  (TypeScript, Vite)  |
|   src-tauri/)    |                 |  (src/)              |
+--------+---------+                 +----------+-----------+
         |                                      |
         | spawn + stdin/stdout JSON-RPC        | HTTP (loopback)
         v                                      v
     +------------------------------------------------+
     |  Python-Sidecar (FastAPI, sidecar/)            |
     |  -> qualdatan-core, qualdatan-plugins          |
     +------------------------------------------------+
```

## Komponenten

| Ordner | Rolle | Phase |
|--------|-------|-------|
| `src-tauri/` | Tauri/Rust Backend. Spawned Sidecar, Lifecycle, Windows-Signing. | G |
| `src/` | React/TypeScript-Frontend. MVP-Views. | G |
| `sidecar/` | FastAPI auf Loopback; wrappt `qualdatan-core`/`qualdatan-plugins`. Wird **nicht** auf PyPI publiziert. | F |
| `installer/` | PyInstaller + Tauri-Bundler; Matrix x64/ARM64. | H |

## Lizenz & SPDX

AGPL-3.0-only. Neue Quelldateien beginnen mit dem passenden SPDX-Header (`//` für Rust/TS, `#` für Python).
