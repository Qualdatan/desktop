<!-- SPDX-License-Identifier: AGPL-3.0-only -->
<script lang="ts">
  import { page } from '$app/stores';
  import {
    Card,
    CardBody,
    CardHeader,
    Row,
    Col,
    Button,
    Alert,
    Spinner,
    Badge
  } from 'sveltestrap';
  import { api } from '$lib/sidecar';

  type ExportResult = {
    path: string;
    format: string;
    size_bytes: number;
    created_at: string;
  };

  type FormatState = {
    status: 'idle' | 'running' | 'done' | 'error';
    result?: ExportResult;
    error?: string;
    httpStatus?: number;
  };

  let runId = $derived($page.params.runId);

  let qdpxState = $state<FormatState>({ status: 'idle' });
  let xlsxState = $state<FormatState>({ status: 'idle' });
  let toast = $state<{ color: string; message: string } | null>(null);

  /**
   * Formatiert eine Bytegroesse als KB/MB-String.
   */
  function formatBytes(n: number): string {
    if (n < 1024) return `${n} B`;
    if (n < 1024 * 1024) return `${(n / 1024).toFixed(1)} KB`;
    return `${(n / (1024 * 1024)).toFixed(2)} MB`;
  }

  function showToast(color: string, message: string) {
    toast = { color, message };
    setTimeout(() => {
      if (toast && toast.message === message) toast = null;
    }, 4000);
  }

  async function runExport(format: 'qdpx' | 'xlsx') {
    const state = format === 'qdpx' ? qdpxState : xlsxState;
    state.status = 'running';
    state.error = undefined;
    state.result = undefined;
    state.httpStatus = undefined;
    try {
      const result = await api.post<ExportResult>(`/export/${format}`, {
        run_id: runId
      });
      state.result = result;
      state.status = 'done';
    } catch (e: unknown) {
      const err = e as { status?: number; message?: string };
      state.httpStatus = err?.status;
      state.error = err?.message ?? String(e);
      state.status = 'error';
    }
  }

  async function revealInFolder(path: string) {
    try {
      const { invoke } = await import('@tauri-apps/api/core');
      await invoke('reveal_in_folder', { path });
    } catch (e) {
      // Fallback: Pfad in die Zwischenablage kopieren.
      try {
        await navigator.clipboard.writeText(path);
        showToast(
          'info',
          'Ordner-Anzeige nicht verfuegbar – Pfad in Zwischenablage kopiert.'
        );
      } catch {
        showToast('danger', `Pfad konnte nicht geoeffnet werden: ${path}`);
      }
    }
  }

  async function copyPath(path: string) {
    try {
      await navigator.clipboard.writeText(path);
      showToast('success', 'Pfad kopiert.');
    } catch {
      showToast('danger', 'Kopieren in Zwischenablage fehlgeschlagen.');
    }
  }
</script>

<h2>Export</h2>
<p class="text-muted">
  Run <code>{runId}</code>
</p>

{#if toast}
  <Alert color={toast.color} fade={false}>{toast.message}</Alert>
{/if}

<Row>
  {#each [{ key: 'qdpx', state: qdpxState, title: 'QDPX (REFI-QDA fuer MAXQDA)', desc: 'Exportiert Interviews und Kodierungen als REFI-QDA-Paket (.qdpx). Direkt in MAXQDA importierbar.' }, { key: 'xlsx', state: xlsxState, title: 'Pivot-Excel (XLSX)', desc: 'Exportiert ein Excel-Arbeitsbuch mit Pivot-Tabellen ueber Codes, Segmente und Projekte.' }] as fmt (fmt.key)}
    <Col md="6" class="mb-3">
      <Card>
        <CardHeader>
          <strong>{fmt.title}</strong>
        </CardHeader>
        <CardBody>
          <p>{fmt.desc}</p>

          <Button
            color="primary"
            disabled={fmt.state.status === 'running'}
            on:click={() => runExport(fmt.key as 'qdpx' | 'xlsx')}
          >
            {#if fmt.state.status === 'running'}
              <Spinner size="sm" /> Exportiere…
            {:else}
              Exportieren
            {/if}
          </Button>

          {#if fmt.state.status === 'error'}
            {#if fmt.state.httpStatus === 409}
              <Alert color="warning" class="mt-3"
                >Run ist noch nicht abgeschlossen.</Alert
              >
            {:else if fmt.state.httpStatus === 404}
              <Alert color="danger" class="mt-3"
                >Run wurde nicht gefunden.</Alert
              >
            {:else}
              <Alert color="danger" class="mt-3"
                >Export fehlgeschlagen: {fmt.state.error}</Alert
              >
            {/if}
          {/if}

          {#if fmt.state.status === 'done' && fmt.state.result}
            <div class="mt-3">
              <div class="mb-2">
                <Badge color="success">Fertig</Badge>
                <Badge color="secondary"
                  >{formatBytes(fmt.state.result.size_bytes)}</Badge
                >
              </div>
              <div class="mb-2">
                <small class="text-muted">Pfad:</small>
                <div>
                  <code class="small">{fmt.state.result.path}</code>
                </div>
              </div>
              <div class="d-flex gap-2 flex-wrap">
                <Button
                  size="sm"
                  color="secondary"
                  on:click={() => revealInFolder(fmt.state.result!.path)}
                >
                  Im Ordner zeigen
                </Button>
                <Button
                  size="sm"
                  color="outline-secondary"
                  on:click={() => copyPath(fmt.state.result!.path)}
                >
                  Pfad kopieren
                </Button>
              </div>
            </div>
          {/if}
        </CardBody>
      </Card>
    </Col>
  {/each}
</Row>
