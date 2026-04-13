# qualdatan-desktop

Desktop-App fuer [Qualdatan](https://github.com/Qualdatan):
Tauri-Shell (Rust) + React-Frontend (TypeScript/Vite/Tailwind/shadcn) +
Python-Sidecar (FastAPI ueber
[qualdatan-core](https://github.com/Qualdatan/core) und
[qualdatan-plugins](https://github.com/Qualdatan/plugins)).

Windows-Installer fuer x64 und ARM64 werden ueber GitHub Releases
ausgeliefert (keine PyPI-Veroeffentlichung).

**Status**: Scaffold (Phase G, Welle 1). Phase F baut den Sidecar
(`sidecar/`), Welle 2 fuellt die MVP-Views unter `src/views/`.

## Layout

```
sidecar/        FastAPI-Sidecar (Python-Paket qualdatan-sidecar, nicht PyPI)
src-tauri/      Rust/Tauri-Backend (spawnt Sidecar, verteilt Port+Token)
src/            React-Frontend (TS/Vite), shadcn-UI, TanStack Query+Router
installer/      PyInstaller + Tauri-Bundler, Matrix x64/ARM64 (Phase H)
```

## Development

```bash
# Dependencies
pnpm install           # oder: npm install
pnpm gen:sidecar       # generiert src/lib/sidecar.gen.ts aus openapi.json

# Dev-Mode (startet Vite + Tauri, Tauri spawnt Sidecar)
pnpm tauri dev
```

Voraussetzung im Dev-Modus: Entweder liegt `qualdatan-sidecar` auf dem
PATH (empfohlen: `cd sidecar && uv sync && uv run python -m
qualdatan_sidecar` zur Validierung) oder die gebuendelte Binary wurde
durch Phase H unter `src-tauri/binaries/qualdatan-sidecar[.exe]` abgelegt.

## Architektur in Kurz

1. Tauri startet und spawnt den Sidecar-Kindprozess.
2. Sidecar druckt auf stdout: `{"port": <u16>, "token": "<uuid>"}`.
3. Tauri liest die Zeile, legt Port+Token in den State.
4. Frontend holt beide via `invoke('get_sidecar_port' / 'get_sidecar_token')`
   und ruft den typed `sidecar`-Client auf (siehe `src/lib/sidecar.ts`),
   der `X-Sidecar-Token` injiziert.

## Dokumentation

- Live-Site: https://qualdatan.github.io/desktop/
- Lokaler Preview: `pip install mkdocs mkdocs-material && mkdocs serve`
- Docs-Policy und -Struktur: [CLAUDE.md](CLAUDE.md)

## Lizenz

AGPL-3.0-only — siehe [LICENSE](LICENSE). Die Affero-Klausel greift wenn
Teile der App als Netzwerkdienst laufen; der Installer verlinkt den Source.
