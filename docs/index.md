# qualdatan-desktop

Desktop-App für [Qualdatan](https://github.com/GeneralPawz/Qualdatan): Tauri-Shell (Rust) + React-Frontend + Python-Sidecar (FastAPI über [qualdatan-core](https://github.com/Qualdatan/core) und [qualdatan-plugins](https://github.com/Qualdatan/plugins)).

Windows-Installer für x64 und ARM64 werden über GitHub Releases ausgeliefert (keine PyPI-Veröffentlichung).

**Status**: Scaffold. Phase F baut den Sidecar, Phase G die Tauri-Shell plus MVP-Views.

## Weiter

- [Architecture](architecture.md) — Komponenten, Lifecycle.
- [Installer](installer.md) — Build-Matrix.
- [API Reference](api.md) — wird aus rustdoc/typedoc/mkdocstrings generiert, sobald Code existiert.
- [Changelog](changelog.md).

## Lizenz

AGPL-3.0-only — siehe [LICENSE](https://github.com/Qualdatan/desktop/blob/main/LICENSE). Die Affero-Klausel greift, wenn Teile der App als Netzwerkdienst laufen; der Installer verlinkt den Source.
