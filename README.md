# qualdatan-desktop

Desktop-App fuer [Qualdatan](https://github.com/Qualdatan):
Tauri-Shell (Rust) + SvelteKit-Frontend (TypeScript, adapter-static, sveltestrap/Bootstrap 5) +
Python-Sidecar (FastAPI ueber
[qualdatan-core](https://github.com/Qualdatan/core) und
[qualdatan-plugins](https://github.com/Qualdatan/plugins)).

Windows-Installer fuer x64 und ARM64 werden ueber GitHub Releases
ausgeliefert (keine PyPI-Veroeffentlichung).

**Status**: Scaffold (Phase G, Welle 1). Phase F baut den Sidecar
(`sidecar/`), Welle 2 fuellt die MVP-Views unter `src/routes/`.

## Layout

```
sidecar/        FastAPI-Sidecar (Python-Paket qualdatan-sidecar, nicht PyPI)
src-tauri/      Rust/Tauri-Backend (spawnt Sidecar, verteilt Port+Token)
src/            SvelteKit-Frontend (TS/Vite, sveltestrap, Bootstrap 5)
  routes/       File-based Routing (8 Views, SPA via adapter-static)
  lib/          sidecar.ts (typed client) + queryHelpers.ts (SWR-Runes)
installer/      PyInstaller + Tauri-Bundler, Matrix x64/ARM64 (Phase H)
```

## Development

```bash
# Dependencies
pnpm install           # oder: npm install
pnpm gen:sidecar       # generiert src/lib/sidecar.gen.ts aus openapi.json

# Dev-Mode (startet Vite auf 127.0.0.1:1420 + Tauri, Tauri spawnt Sidecar)
pnpm tauri:dev
```

Fuer reines Browser-Debugging ohne Tauri: `pnpm dev` und die Env-Variablen
`VITE_SIDECAR_PORT` / `VITE_SIDECAR_TOKEN` setzen, nachdem der Sidecar
manuell gestartet wurde.

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

## Building installers

Der Windows-Installer (MSI) wird via GitHub Actions gebaut
(`.github/workflows/desktop-build.yml`). Trigger:

- Push eines Tags `v*` (z. B. `git tag v0.1.0 && git push --tags`).
- Manuell via `workflow_dispatch` im Actions-Tab.

Die Pipeline:

1. `cd sidecar && uv sync --extra dev`
2. `uv run pyinstaller qualdatan_sidecar.spec --noconfirm --clean`
   → `sidecar/dist/qualdatan-sidecar.exe`
3. Kopie nach
   `src-tauri/binaries/qualdatan-sidecar-x86_64-pc-windows-msvc.exe`
   (Tauri-Target-Triple-Konvention für `externalBin`).
4. `pnpm install && pnpm gen:sidecar && pnpm tauri build`
5. Upload der MSI aus `src-tauri/target/release/bundle/msi/` als Artifact.

Lokales Äquivalent (auf Windows, mit `uv`, `pnpm`, Rust-Toolchain):

```powershell
# 1. Sidecar bauen
cd sidecar
uv sync --extra dev
uv run pyinstaller qualdatan_sidecar.spec --noconfirm --clean
cd ..

# 2. Binary an Tauri-konforme Stelle legen
New-Item -ItemType Directory -Force -Path src-tauri/binaries | Out-Null
Copy-Item sidecar/dist/qualdatan-sidecar.exe `
  src-tauri/binaries/qualdatan-sidecar-x86_64-pc-windows-msvc.exe -Force

# 3. Frontend + Tauri-Installer
pnpm install
pnpm gen:sidecar
pnpm tauri build
```

ARM64 (`aarch64-pc-windows-msvc`) ist vorgemerkt, sobald ein
GitHub-Hosted ARM64-Runner verfügbar ist — siehe TODO in der
Workflow-Matrix.

## Releases & Updates

Ab Phase H werden die Windows-Installer als **NSIS-Setup (.exe)** gebaut
(nicht mehr MSI) und ueber **GitHub Releases** ausgeliefert. Installierte
Apps pollen beim Start das Updater-Manifest `latest.json` und bieten dem
Nutzer ein Update-Dialog an (Tauri-Updater-Plugin).

### Einmalige Einrichtung (Maintainer)

1. **Signing-Keypair lokal erzeugen** (einmalig, nicht einchecken):

   ```powershell
   pnpm tauri signer generate -w $HOME\.tauri\qualdatan.key
   ```

   Erzeugt `qualdatan.key` (privat, passphrase-geschuetzt) und
   `qualdatan.key.pub` (public).

2. **Public Key in `src-tauri/tauri.conf.json`** unter
   `plugins.updater.pubkey` einsetzen (Inhalt von `qualdatan.key.pub`,
   Base64-String ohne Newlines). Der Platzhalter
   `REPLACE_WITH_PUBLIC_KEY` muss ersetzt werden, sonst weigert sich
   Tauri beim Build.

3. **GitHub-Secrets setzen** (Repo → Settings → Secrets → Actions):

   - `TAURI_SIGNING_PRIVATE_KEY` — Inhalt von `~/.tauri/qualdatan.key`
     (gesamte Datei als String).
   - `TAURI_SIGNING_PRIVATE_KEY_PASSWORD` — zugehoerige Passphrase.

### Release-Flow

```bash
git tag v0.1.0
git push origin v0.1.0
```

Der Workflow `.github/workflows/desktop-build.yml` erzeugt dann:

- `Qualdatan Desktop_<version>_x64-setup.exe` (NSIS-Installer mit
  Komponenten-Auswahl: Desktop App = Pflicht, TUI Launcher = optional).
- `…_x64-setup.exe.sig` (Updater-Signatur, wenn Secrets gesetzt sind).
- `latest.json` (Updater-Manifest, zeigt auf die obige `.exe`).

Alle drei Dateien werden als Release-Assets am Tag veroeffentlicht
(`https://github.com/Qualdatan/desktop/releases/tag/v0.1.0`).

### Update-Flow (Installed App)

Die App pollt beim Start

```
https://github.com/Qualdatan/desktop/releases/latest/download/latest.json
```

(GitHub leitet `latest` auf den jeweils neuesten Release um). Ist eine
hoehere Version verfuegbar, zeigt Tauri einen Dialog mit Release-Notes
an; bei Bestaetigung wird der NSIS-Installer heruntergeladen, gegen den
Public-Key verifiziert und gestartet.

### NSIS-Komponenten

Der Installer fragt per **Component-Page**:

| Komponente   | Default | Zweck |
|--------------|---------|-------|
| Desktop App  | an (RO) | Qualdatan-Hauptanwendung (Pflicht). |
| TUI Launcher | aus     | Schreibt Marker fuer optionales `pipx install qualdatan-tui`. |

Die TUI-Komponente installiert Python/pipx **nicht** automatisch; nach
Setup zeigt NSIS den pipx-Befehl als MessageBox, und die Desktop-App
liest `%LOCALAPPDATA%\Qualdatan\install_tui.flag`, um den Nutzer ggf.
nochmals zu erinnern.

## winget Distribution

> Hinweis: Diese Sektion setzt den vorhergehenden Release-Flow voraus (siehe
> "Building installers" weiter oben — dort laedt PH12-TAURI den NSIS-Installer
> als Release-Asset hoch). Die winget-Submission fuehrt danach aus.

Nach jedem GitHub-Release publiziert
`.github/workflows/winget-submit.yml` einen Pull-Request gegen
[`microsoft/winget-pkgs`](https://github.com/microsoft/winget-pkgs), damit
Endnutzer die App per

```powershell
winget install Qualdatan.Desktop
```

installieren koennen. Die Manifest-Templates liegen unter
[`winget/`](./winget) (Platzhalter `{{VERSION}}`, `{{INSTALLER_URL}}`,
`{{INSTALLER_SHA256}}` werden im Workflow substituiert). Das Tooling ist
[komac](https://github.com/russellbanks/Komac).

### Einmalige Einrichtung durch den Maintainer

1. `microsoft/winget-pkgs` forken (eigener GitHub-Account, da der PR aus
   einem Fork kommen muss).
2. Fine-grained Personal Access Token fuer diesen Fork erstellen
   (`contents: read/write`, `pull-requests: read/write`).
3. Token als Actions-Secret hinterlegen: **`WINGET_GH_TOKEN`**.
4. Optional: Publisher-Namespace `Qualdatan` via den ersten PR bei
   Microsoft registrieren lassen (Moderatoren-Review).

### Opt-in-Verhalten

Fehlt `WINGET_GH_TOKEN`, **endet der Workflow mit einem Hinweis** statt zu
failen — das Release selbst bleibt also unberuehrt. Erst nach dem Hinzufuegen
des Secrets werden kuenftige Releases automatisch bei winget eingereicht. Der
eigentliche Merge des PRs erfolgt durch die Microsoft-Moderatoren upstream.

Manuell ausloesbar via Actions-Tab (`workflow_dispatch` mit `version`-Input).

## Lizenz

AGPL-3.0-only — siehe [LICENSE](LICENSE). Die Affero-Klausel greift wenn
Teile der App als Netzwerkdienst laufen; der Installer verlinkt den Source.
