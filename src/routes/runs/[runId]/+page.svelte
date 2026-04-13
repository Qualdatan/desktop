<!-- SPDX-License-Identifier: AGPL-3.0-only -->
<!--
  Run-Monitor mit Live-Progress via Server-Sent Events.

  NOTE (Welle 3 / Sidecar): `EventSource` unterstuetzt keine Custom-Header,
  deshalb wird das Session-Token hier als Query-Parameter `?token=...`
  uebergeben. Die Sidecar-Dependency `verify_token` muss diesen Fallback
  zusaetzlich zum `X-Sidecar-Token`-Header akzeptieren (TODO Welle 3).
-->
<script lang="ts">
  import { onMount } from 'svelte';
  import { page } from '$app/stores';
  import { goto } from '$app/navigation';
  import {
    Alert,
    Badge,
    Button,
    Card,
    CardBody,
    CardHeader,
    Progress,
    Spinner,
    Table
  } from 'sveltestrap';
  import { createResource } from '$lib/queryHelpers';
  import { api, apiBase, apiToken } from '$lib/sidecar';

  type RunStatus = 'pending' | 'running' | 'completed' | 'failed' | 'cancelled';

  type RunOut = {
    id: string;
    project_id?: string;
    status: RunStatus;
    config?: Record<string, unknown>;
    started_at?: string | null;
    finished_at?: string | null;
    error?: string | null;
  };

  type ProgressEvent = {
    event_type: string;
    run_id: string;
    material?: string | null;
    step?: string | null;
    pct?: number | null;
    message?: string | null;
  };

  type LoggedEvent = ProgressEvent & { _ts: string };

  const runId = $derived($page.params.runId);
  const run = createResource<RunOut>(() => api.get<RunOut>(`/runs/${runId}`));

  let events = $state<LoggedEvent[]>([]);
  let sseError = $state<string | null>(null);
  let logContainer: HTMLDivElement | undefined = $state();

  const lastPct = $derived.by(() => {
    for (let i = events.length - 1; i >= 0; i--) {
      const p = events[i].pct;
      if (typeof p === 'number') return p;
    }
    return null;
  });

  const statusColor = $derived.by<string>(() => {
    switch (run.data?.status) {
      case 'pending':
        return 'secondary';
      case 'running':
        return 'primary';
      case 'completed':
        return 'success';
      case 'failed':
        return 'danger';
      case 'cancelled':
        return 'warning';
      default:
        return 'secondary';
    }
  });

  function handleEvent(raw: string) {
    try {
      const evt = JSON.parse(raw) as ProgressEvent;
      const logged: LoggedEvent = { ...evt, _ts: new Date().toISOString() };
      events = [...events.slice(-199), logged];
      return evt.event_type;
    } catch (e) {
      sseError = `Ungueltiger SSE-Payload: ${(e as Error).message}`;
      return null;
    }
  }

  onMount(() => {
    let es: EventSource | null = null;
    let cancelled = false;

    (async () => {
      try {
        const base = await apiBase();
        const token = await apiToken();
        if (cancelled) return;
        es = new EventSource(
          `${base}/runs/${runId}/stream?token=${encodeURIComponent(token)}`
        );

        const onAny = (e: MessageEvent) => {
          const type = handleEvent(e.data);
          if (type === 'finished' || type === 'failed') {
            es?.close();
            void run.refresh();
          }
        };

        es.onmessage = onAny;
        // Named SSE events (FastAPI kann `event:` Feld setzen).
        for (const name of ['progress', 'started', 'finished', 'failed', 'cancelled']) {
          es.addEventListener(name, onAny as EventListener);
        }
        es.onerror = () => {
          sseError = 'SSE-Verbindung unterbrochen.';
        };
      } catch (e) {
        sseError = (e as Error).message;
      }
    })();

    return () => {
      cancelled = true;
      es?.close();
    };
  });

  // Auto-Scroll Event-Log.
  $effect(() => {
    // Reagiert auf events-Aenderung.
    events.length;
    if (logContainer) {
      logContainer.scrollTop = logContainer.scrollHeight;
    }
  });

  function formatTs(iso: string): string {
    try {
      return new Date(iso).toLocaleTimeString('de-DE', { hour12: false });
    } catch {
      return iso;
    }
  }
</script>

<div class="d-flex justify-content-between align-items-center mb-3">
  <h2 class="mb-0">Run-Monitor</h2>
  <div class="d-flex gap-2">
    <Button
      color="secondary"
      outline
      onclick={() => {
        const pid = run.data?.project_id;
        if (pid) void goto(`/projects/${pid}`);
        else void goto('/');
      }}
    >
      Zurueck
    </Button>
    <Button
      color="primary"
      disabled={run.data?.status !== 'completed'}
      onclick={() => goto(`/runs/${runId}/export`)}
    >
      Export
    </Button>
  </div>
</div>

{#if run.loading}
  <div class="text-center py-4">
    <Spinner /> <span class="ms-2">Lade Run <code>{runId}</code> ...</span>
  </div>
{:else if run.error}
  <Alert color="danger">
    Fehler beim Laden des Runs: {String(run.error)}
  </Alert>
{:else if run.data}
  <Card class="mb-3">
    <CardHeader>
      <div class="d-flex justify-content-between align-items-center">
        <div>
          <strong>Run</strong> <code>{run.data.id}</code>
        </div>
        <Badge color={statusColor}>{run.data.status}</Badge>
      </div>
    </CardHeader>
    <CardBody>
      <div class="row small text-muted mb-2">
        <div class="col-md-6">
          Gestartet: {run.data.started_at ? formatTs(run.data.started_at) : '-'}
        </div>
        <div class="col-md-6">
          Beendet: {run.data.finished_at ? formatTs(run.data.finished_at) : '-'}
        </div>
      </div>
      <Progress value={lastPct ?? 0} max={100}>
        {lastPct != null ? `${Math.round(lastPct)} %` : ''}
      </Progress>
      {#if run.data.error}
        <Alert color="danger" class="mt-3 mb-0">
          <strong>Fehler:</strong>
          {run.data.error}
        </Alert>
      {/if}
    </CardBody>
  </Card>
{/if}

{#if sseError}
  <Alert color="warning">{sseError}</Alert>
{/if}

<Card>
  <CardHeader>Event-Log ({events.length})</CardHeader>
  <CardBody class="p-0">
    <div bind:this={logContainer} style="max-height: 400px; overflow-y: auto;">
      <Table size="sm" hover class="mb-0">
        <thead class="table-light sticky-top">
          <tr>
            <th style="width: 7rem;">Zeit</th>
            <th style="width: 8rem;">Event</th>
            <th style="width: 10rem;">Material</th>
            <th>Nachricht</th>
          </tr>
        </thead>
        <tbody>
          {#each events as evt (evt._ts + evt.event_type + (evt.material ?? '') + (evt.message ?? ''))}
            <tr>
              <td><code class="small">{formatTs(evt._ts)}</code></td>
              <td><Badge color="info">{evt.event_type}</Badge></td>
              <td class="small">{evt.material ?? ''}</td>
              <td class="small">
                {evt.step ? `[${evt.step}] ` : ''}{evt.message ?? ''}
                {#if typeof evt.pct === 'number'}
                  <span class="text-muted">({Math.round(evt.pct)} %)</span>
                {/if}
              </td>
            </tr>
          {:else}
            <tr>
              <td colspan="4" class="text-center text-muted py-3">
                Noch keine Events empfangen.
              </td>
            </tr>
          {/each}
        </tbody>
      </Table>
    </div>
  </CardBody>
</Card>
