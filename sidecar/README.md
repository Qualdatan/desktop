# qualdatan-sidecar

FastAPI-Sidecar fuer die [Qualdatan Desktop-App](https://github.com/Qualdatan/desktop).
Startet auf Loopback, verhandelt Port+Token via stdin-Handshake mit dem
Tauri-Parent, exponiert die APIs von `qualdatan-core` und `qualdatan-plugins`
fuer das React/TS-Frontend.

Dieses Paket wird **nicht** auf PyPI veroeffentlicht, sondern im
Tauri-Installer als PyInstaller-Binary gebundled.

## Status

**Phase F = Contract-Freeze.** Dieses Paket enthaelt aktuell ausschliesslich
den gefrorenen FastAPI-Kontrakt (Pydantic-Modelle + Endpoint-Signaturen)
und einen generierten `contract/openapi.json`. Die Endpoint-Koerper - mit
Ausnahme von `/healthz` - werfen `NotImplementedError("TODO Welle 1")`.

- `src/qualdatan_sidecar/contract/models.py` - Pydantic-Modelle.
- `src/qualdatan_sidecar/contract/endpoints.py` - sechs Router mit vollen
  Signaturen (`response_model=`, Param-Typen).
- `src/qualdatan_sidecar/contract/auth.py` - Token-Gate via
  `X-Sidecar-Token`-Header gegen `QUALDATAN_SIDECAR_TOKEN`.
- `src/qualdatan_sidecar/contract/app.py` - `build_app()` montiert alle
  Router und haengt das Token-Gate global an (ausser `/healthz`).
- `contract/openapi.json` - eingecheckte, deterministische OpenAPI-Spec.
  Welle 2 generiert hiervon den Frontend-Client, **ohne** dass der
  Sidecar laufen muss.

## Wellen-Aufteilung

| Welle | Scope |
|-------|-------|
| F (jetzt) | Contract, Modelle, Signaturen, `openapi.json`, Tests fuer Form. |
| 1 | Ersetzt die `NotImplementedError`-Koerper in `contract/endpoints.py` durch echte Calls auf `qualdatan_core` / `qualdatan_plugins`, haengt den Stdin-Handshake an, verdrahtet SSE-Progress. |
| 2 | Generiert TS-Client aus `contract/openapi.json`, baut das React-Frontend gegen diesen Client. |

## Entwicklung

```bash
cd repos/desktop/sidecar
uv sync
uv run pytest
```

### OpenAPI-Spec regenerieren

Wenn ein Modell oder eine Signatur angefasst wurde:

```bash
uv run python -m qualdatan_sidecar.contract.dump_openapi
```

Das schreibt `contract/openapi.json` deterministisch (sortierte Keys,
Indent 2). Der Test `test_dump_openapi_matches_checked_in_file` faellt,
wenn die eingecheckte Spec vom Code driftet - das ist die Drift-Guard
fuer Welle 2.

## Wo Welle 1 die Koerper hinhaengt

Jeder Stub in `contract/endpoints.py` ist mit `NotImplementedError("TODO Welle 1")`
markiert. Welle 1 ersetzt dort **nur** die Funktionskoerper - die
Signaturen (Parameter, `response_model`) bleiben stabil, sonst driftet
die Client-Generierung in Welle 2.

## Lizenz

AGPL-3.0-only - siehe [LICENSE](../LICENSE).
