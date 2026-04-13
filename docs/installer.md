# Installer

**Status**: Phase H, noch nicht implementiert.

## Ziel-Matrix

| Plattform | Arch | Format |
|-----------|------|--------|
| Windows | x64 | `.msi` (Tauri-Bundler) + portable `.exe` |
| Windows | ARM64 | `.msi` + portable `.exe` |

Linux/macOS sind aktuell nicht vorgesehen.

## Pipeline (geplant)

1. **PyInstaller** baut den Sidecar zu einer einzelnen Binary (pro Arch).
2. **Tauri-Bundler** zieht die Sidecar-Binary als Side-Resource ein und baut den finalen MSI.
3. **GitHub Releases**: Code-Signing via Zertifikat aus Secrets, Upload über Release-Workflow.

Details folgen mit Phase H.
