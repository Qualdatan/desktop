<!-- SPDX-License-Identifier: AGPL-3.0-only -->
<!--
  Settings-Seite (Welle 2, SV8).
  4 Cards in 2x2 Grid: Sidecar-Status, App-Datenbank, Plugin-Server, Ueber.
  HINWEIS: `get_env` und `reveal_in_folder` sind Tauri-Commands, die in
  Welle 3 (Rust-Seite) noch hinzugefuegt werden muessen. Aktuell im
  try/catch gekapselt, damit die Seite auch ohne diese Commands laedt.
-->
<script lang="ts">
  import {
    Card,
    CardBody,
    CardHeader,
    Row,
    Col,
    Button,
    Input,
    FormGroup,
    Label,
    Alert,
    Badge,
    Spinner
  } from '@sveltestrap/sveltestrap';
  import { api, apiBase, apiToken } from '$lib/sidecar';

  // --- Sidecar health ---
  type Health = { status: string; version: string } | null;
  let health = $state<Health>(null);
  let healthError = $state<string | null>(null);
  let healthLoading = $state(true);
  let sidecarPort = $state<string>('?');
  let tokenPreview = $state<string>('...');
  let tokenCopied = $state(false);

  async function pollHealth() {
    try {
      const [h, base, tok] = await Promise.all([
        api.get<{ status: string; version: string }>('/healthz'),
        apiBase(),
        apiToken()
      ]);
      health = h;
      healthError = null;
      const m = base.match(/:(\d+)$/);
      sidecarPort = m ? m[1] : base;
      tokenPreview = tok.slice(0, 8) + '...';
    } catch (e) {
      health = null;
      healthError = e instanceof Error ? e.message : String(e);
    } finally {
      healthLoading = false;
    }
  }

  $effect(() => {
    void pollHealth();
    const id = setInterval(() => void pollHealth(), 10_000);
    return () => clearInterval(id);
  });

  async function copyToken() {
    try {
      const tok = await apiToken();
      await navigator.clipboard.writeText(tok);
      tokenCopied = true;
      setTimeout(() => (tokenCopied = false), 2000);
    } catch (e) {
      console.error('Token-Kopie fehlgeschlagen', e);
    }
  }

  // --- App-Datenbank ---
  let dbPath = $state<string | null>(null);
  let dbFallback = $state(false);
  let dbRevealMsg = $state<string | null>(null);

  async function loadDbPath() {
    try {
      // TODO Welle 3: Tauri-Command `get_env` in src-tauri/ registrieren.
      const { invoke } = await import('@tauri-apps/api/core');
      const val = await invoke<string | null>('get_env', {
        name: 'QUALDATAN_SIDECAR_APP_DB'
      });
      if (val) {
        dbPath = val;
        dbFallback = false;
      } else {
        dbFallback = true;
      }
    } catch {
      dbFallback = true;
    }
  }

  async function revealDb() {
    if (!dbPath) return;
    try {
      // TODO Welle 3: Tauri-Command `reveal_in_folder` in src-tauri/ registrieren.
      const { invoke } = await import('@tauri-apps/api/core');
      await invoke('reveal_in_folder', { path: dbPath });
      dbRevealMsg = 'Im Dateimanager geoeffnet.';
    } catch {
      try {
        await navigator.clipboard.writeText(dbPath);
        dbRevealMsg = 'Pfad in Zwischenablage kopiert (Fallback).';
      } catch {
        dbRevealMsg = 'Konnte weder oeffnen noch kopieren.';
      }
    }
    setTimeout(() => (dbRevealMsg = null), 3000);
  }

  $effect(() => {
    void loadDbPath();
  });

  // --- Plugin-Server ---
  const PLUGIN_KEY = 'qualdatan.pluginServerUrl';
  let pluginUrl = $state<string>('http://localhost:8080');
  let pluginSaved = $state(false);

  $effect(() => {
    if (typeof localStorage !== 'undefined') {
      pluginUrl = localStorage.getItem(PLUGIN_KEY) ?? 'http://localhost:8080';
    }
  });

  function savePluginUrl() {
    try {
      localStorage.setItem(PLUGIN_KEY, pluginUrl);
      pluginSaved = true;
      setTimeout(() => (pluginSaved = false), 2000);
    } catch (e) {
      console.error(e);
    }
  }

  // --- Ueber ---
  const appVersion = (import.meta.env.VITE_APP_VERSION as string | undefined) ?? '0.1.0';
</script>

<h2 class="mb-4"><i class="bi bi-gear-fill me-2"></i>Einstellungen</h2>

<Row>
  <Col md="6" class="mb-4">
    <Card>
      <CardHeader><strong>Sidecar</strong></CardHeader>
      <CardBody>
        {#if healthLoading && !health && !healthError}
          <Spinner size="sm" /> Pruefe Sidecar...
        {:else if health}
          <p class="mb-2">
            Status: <Badge color="success">{health.status}</Badge>
          </p>
          <p class="mb-1"><small>Version: <code>{health.version}</code></small></p>
          <p class="mb-1"><small>Port: <code>{sidecarPort}</code></small></p>
          <p class="mb-2"><small>Token: <code>{tokenPreview}</code></small></p>
          <Button size="sm" color="secondary" on:click={copyToken}>
            {tokenCopied ? 'Kopiert!' : 'Token kopieren'}
          </Button>
        {:else}
          <p class="mb-2">
            Status: <Badge color="danger">offline</Badge>
          </p>
          {#if healthError}
            <Alert color="warning" class="mb-0"><small>{healthError}</small></Alert>
          {/if}
        {/if}
        <p class="mt-2 mb-0 text-muted"><small>Polling alle 10&nbsp;Sekunden.</small></p>
      </CardBody>
    </Card>
  </Col>

  <Col md="6" class="mb-4">
    <Card>
      <CardHeader><strong>App-Datenbank</strong></CardHeader>
      <CardBody>
        {#if dbPath && !dbFallback}
          <p class="mb-2"><small>Pfad: <code>{dbPath}</code></small></p>
          <Button size="sm" color="secondary" on:click={revealDb}>Im Ordner zeigen</Button>
        {:else}
          <p class="mb-2"><em>Default-Pfad (platformdirs)</em></p>
          <p class="mb-0 text-muted">
            <small
              >Umgebungsvariable <code>QUALDATAN_SIDECAR_APP_DB</code> nicht gesetzt
              oder Tauri-Command <code>get_env</code> noch nicht verfuegbar.</small
            >
          </p>
        {/if}
        {#if dbRevealMsg}
          <Alert color="info" class="mt-2 mb-0"><small>{dbRevealMsg}</small></Alert>
        {/if}
      </CardBody>
    </Card>
  </Col>

  <Col md="6" class="mb-4">
    <Card>
      <CardHeader><strong>Plugin-Server</strong></CardHeader>
      <CardBody>
        <FormGroup>
          <Label for="plugin-url">URL</Label>
          <Input
            id="plugin-url"
            type="url"
            bind:value={pluginUrl}
            placeholder="http://localhost:8080"
          />
        </FormGroup>
        <Button size="sm" color="primary" on:click={savePluginUrl}>
          {pluginSaved ? 'Gespeichert!' : 'Speichern'}
        </Button>
        <p class="mt-2 mb-0 text-muted">
          <small
            >Hinweis: Der Sidecar liest die URL aus seiner eigenen Umgebung. Diese
            Einstellung ist aktuell informativ und wird in einer spaeteren Welle an
            den Sidecar uebergeben.</small
          >
        </p>
      </CardBody>
    </Card>
  </Col>

  <Col md="6" class="mb-4">
    <Card>
      <CardHeader><strong>Ueber</strong></CardHeader>
      <CardBody>
        <p class="mb-1">App-Version: <code>{appVersion}</code></p>
        <p class="mb-0">
          <small
            >Lizenzen: AGPL-3.0-only (Code), CC-BY-NC-SA-4.0
            (Default-Bundles).</small
          >
        </p>
      </CardBody>
    </Card>
  </Col>
</Row>
