# qualdatan-sidecar

FastAPI-Sidecar fuer die [Qualdatan Desktop-App](https://github.com/Qualdatan/desktop).
Startet auf Loopback, verhandelt Port+Token via stdin-Handshake mit dem
Tauri-Parent, exponiert die APIs von `qualdatan-core` und `qualdatan-plugins`
fuer das React/TS-Frontend.

**Status:** Scaffold — Phase F fuellt `app.py`, `handshake.py`, `routes/` und
die SSE-Progress-Streams.

Dieses Paket wird **nicht** auf PyPI veroeffentlicht, sondern im
Tauri-Installer als PyInstaller-Binary gebundled.

## Lizenz

AGPL-3.0-only — siehe [LICENSE](../LICENSE).
