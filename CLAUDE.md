# CLAUDE.md — qualdatan-desktop

## Docs-Policy

Docs sind **nicht optional** und werden **mit dem Code** gepflegt. Die Site wird automatisch per GitHub Pages unter `https://qualdatan.github.io/desktop/` veröffentlicht.

### Primäre Doku = Inline-Dokumentation

- **Rust** (`src-tauri/`): Rustdoc-Kommentare (`///`) an öffentlichen Items. Später per `cargo doc` in `docs/` eingelinkt.
- **TypeScript/React** (`src/`): TSDoc (`/** ... */`) an exportierten Komponenten, Hooks, Types. Später via Typedoc eingelinkt.
- **Python-Sidecar** (`sidecar/`): Google-Docstrings (`Args:`, `Returns:`, `Raises:`, `Example:`). Section-Marker englisch, Prosa darf deutsch sein.

Mkdocstrings ist aktuell **nicht** im Plugin-Set aktiv (Sidecar-Code entsteht erst in Phase F). Sobald `sidecar/` eigenständig paketiert wird, kann der `python`-Handler zu `mkdocs.yml` hinzugefügt werden.

### Narrative Docs unter `docs/`

- `docs/index.md` — Purpose, Layout, Status.
- `docs/architecture.md` — Tauri-Shell + React-Frontend + FastAPI-Sidecar, Lifecycle.
- `docs/installer.md` — Build-Matrix x64/ARM64 (Phase H).
- `docs/api.md` — Platzhalter; später rustdoc-/typedoc-/mkdocstrings-Direktiven.
- `docs/changelog.md` — Keep-a-Changelog.
- Neue Konzepte → neue MD-Datei + Eintrag in `mkdocs.yml` unter `nav`.

### Lokaler Preview

```bash
pip install mkdocs mkdocs-material
mkdocs serve
```

### Deploy

Automatisch via `.github/workflows/docs.yml` bei Push auf `main`. Pages-Quelle einmalig auf Branch `gh-pages` setzen.
