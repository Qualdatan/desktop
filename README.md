# qualdatan-desktop

Desktop-App fuer [Qualdatan](https://github.com/GeneralPawz/Qualdatan):
Tauri-Shell (Rust) + React-Frontend + Python-Sidecar (FastAPI ueber
[qualdatan-core](https://github.com/Qualdatan/core) und
[qualdatan-plugins](https://github.com/Qualdatan/plugins)).

Windows-Installer fuer x64 und ARM64 werden ueber GitHub Releases
ausgeliefert (keine PyPI-Veroeffentlichung).

**Status**: Scaffold. Phase F baut den Sidecar, Phase G die Tauri-Shell
plus MVP-Views.

## Layout

```
sidecar/        FastAPI-Sidecar (Python-Paket qualdatan-sidecar, nicht PyPI)
src-tauri/      Rust/Tauri-Backend (Phase G)
src/            Svelt-Frontend with Bootstrap for element styling (Phase G)
installer/      PyInstaller + Tauri-Bundler, Matrix x64/ARM64 (Phase H)
```

## Dokumentation

- Live-Site: https://qualdatan.github.io/desktop/
- Lokaler Preview: `pip install mkdocs mkdocs-material && mkdocs serve`
- Docs-Policy und -Struktur: [CLAUDE.md](CLAUDE.md)

## Lizenz

AGPL-3.0-only — siehe [LICENSE](LICENSE). Die Affero-Klausel greift wenn
Teile der App als Netzwerkdienst laufen; der Installer verlinkt den Source.
