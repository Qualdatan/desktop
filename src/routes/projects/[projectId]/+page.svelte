<!-- SPDX-License-Identifier: AGPL-3.0-only -->
<script lang="ts">
  import { page } from '$app/stores';
  import { goto } from '$app/navigation';
  import {
    Card,
    CardBody,
    CardHeader,
    Row,
    Col,
    Table,
    Button,
    Badge,
    Modal,
    ModalHeader,
    ModalBody,
    ModalFooter,
    Form,
    FormGroup,
    Label,
    Input,
    Alert,
    Spinner
  } from '@sveltestrap/sveltestrap';
  import { api } from '$lib/sidecar';
  import { createResource } from '$lib/queryHelpers';

  type ProjectOut = {
    id: string;
    name: string;
    company?: string | null;
    description?: string | null;
  };

  type RunOut = {
    id: string;
    project_id: string;
    status: 'pending' | 'running' | 'completed' | 'failed' | 'cancelled' | string;
    started_at?: string | null;
    finished_at?: string | null;
    error?: string | null;
  };

  type CodebookEntryOut = {
    id: string;
    project_id: string;
    code: string;
  };

  type BundleSummary = {
    id: string;
    name: string;
    enabled_in_projects?: string[];
  };

  const projectId = $derived($page.params.projectId);

  const project = createResource(() => api.get<ProjectOut>(`/projects/${projectId}`));
  const runs = createResource(() => api.get<RunOut[]>(`/runs?project_id=${projectId}`));
  const codebook = createResource(() =>
    api.get<CodebookEntryOut[]>(`/codebook/${projectId}`)
  );
  const plugins = createResource(() => api.get<BundleSummary[]>(`/plugins`));

  let editOpen = $state(false);
  let editForm = $state({ name: '', company: '', description: '' });
  let editError = $state<string | null>(null);
  let editSaving = $state(false);

  function openEditModal() {
    const p = project.data;
    if (!p) return;
    editForm = {
      name: p.name ?? '',
      company: p.company ?? '',
      description: p.description ?? ''
    };
    editError = null;
    editOpen = true;
  }

  function closeEditModal() {
    editOpen = false;
  }

  async function saveEdit() {
    editSaving = true;
    editError = null;
    try {
      await api.patch<ProjectOut>(`/projects/${projectId}`, {
        name: editForm.name,
        company: editForm.company || null,
        description: editForm.description || null
      });
      await project.refresh();
      editOpen = false;
    } catch (e) {
      editError = e instanceof Error ? e.message : String(e);
    } finally {
      editSaving = false;
    }
  }

  function statusColor(status: string): string {
    switch (status) {
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
  }

  function formatDate(s?: string | null): string {
    if (!s) return '–';
    try {
      return new Date(s).toLocaleString('de-DE');
    } catch {
      return s;
    }
  }

  const activeBundles = $derived(
    (plugins.data ?? []).filter((b) => (b.enabled_in_projects ?? []).includes(projectId))
  );
  const materialCount = $derived(0);
  const runCount = $derived((runs.data ?? []).length);
  const codeCount = $derived((codebook.data ?? []).length);
  const activeBundleCount = $derived(activeBundles.length);
</script>

<div class="mb-4">
  {#if project.loading}
    <Spinner size="sm" /> <span>Lade Projekt…</span>
  {:else if project.error}
    <Alert color="danger">Fehler beim Laden des Projekts: {String(project.error)}</Alert>
  {:else if project.data}
    <div class="d-flex align-items-center flex-wrap gap-2 mb-2">
      <h1 class="me-auto mb-0">{project.data.name}</h1>
      <Button color="secondary" on:click={openEditModal}>Bearbeiten</Button>
      <Button color="primary" on:click={() => goto(`/projects/${projectId}/runs/new`)}>
        Neuer Run
      </Button>
      <Button color="link" on:click={() => goto(`/projects/${projectId}/codebook`)}>
        Codebook
      </Button>
    </div>
    {#if project.data.company}
      <div class="text-muted">Unternehmen: {project.data.company}</div>
    {/if}
    {#if project.data.description}
      <p class="mt-2">{project.data.description}</p>
    {/if}
  {/if}
</div>

<Row class="mb-4">
  <Col md="3" class="mb-3">
    <Card>
      <CardBody>
        <div class="text-muted small">Materialien</div>
        <div class="fs-3 fw-bold">{materialCount}</div>
      </CardBody>
    </Card>
  </Col>
  <Col md="3" class="mb-3">
    <Card>
      <CardBody>
        <div class="text-muted small">Runs</div>
        <div class="fs-3 fw-bold">
          {#if runs.loading}<Spinner size="sm" />{:else}{runCount}{/if}
        </div>
      </CardBody>
    </Card>
  </Col>
  <Col md="3" class="mb-3">
    <Card>
      <CardBody>
        <div class="text-muted small">Codes</div>
        <div class="fs-3 fw-bold">
          {#if codebook.loading}<Spinner size="sm" />{:else}{codeCount}{/if}
        </div>
      </CardBody>
    </Card>
  </Col>
  <Col md="3" class="mb-3">
    <Card>
      <CardBody>
        <div class="text-muted small">Aktive Bundles</div>
        <div class="fs-3 fw-bold">
          {#if plugins.loading}<Spinner size="sm" />{:else}{activeBundleCount}{/if}
        </div>
      </CardBody>
    </Card>
  </Col>
</Row>

<Card class="mb-4">
  <CardHeader>
    <div class="d-flex align-items-center">
      <span class="me-auto">Runs</span>
      <Button size="sm" color="outline-secondary" on:click={runs.refresh}>Aktualisieren</Button>
    </div>
  </CardHeader>
  <CardBody>
    {#if runs.loading}
      <Spinner size="sm" /> <span>Lade Runs…</span>
    {:else if runs.error}
      <Alert color="danger">Fehler beim Laden der Runs: {String(runs.error)}</Alert>
    {:else if (runs.data ?? []).length === 0}
      <p class="text-muted mb-0">Noch keine Runs vorhanden.</p>
    {:else}
      <Table responsive hover>
        <thead>
          <tr>
            <th>ID</th>
            <th>Status</th>
            <th>Gestartet</th>
            <th>Beendet</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          {#each runs.data ?? [] as run (run.id)}
            <tr>
              <td><code>{run.id}</code></td>
              <td><Badge color={statusColor(run.status)}>{run.status}</Badge></td>
              <td>{formatDate(run.started_at)}</td>
              <td>{formatDate(run.finished_at)}</td>
              <td>
                <Button size="sm" color="outline-primary" on:click={() => goto(`/runs/${run.id}`)}>
                  Monitor
                </Button>
              </td>
            </tr>
          {/each}
        </tbody>
      </Table>
    {/if}
  </CardBody>
</Card>

<Modal isOpen={editOpen} toggle={closeEditModal}>
  <ModalHeader toggle={closeEditModal}>Projekt bearbeiten</ModalHeader>
  <ModalBody>
    {#if editError}
      <Alert color="danger">{editError}</Alert>
    {/if}
    <Form>
      <FormGroup>
        <Label for="edit-name">Name</Label>
        <Input id="edit-name" type="text" bind:value={editForm.name} />
      </FormGroup>
      <FormGroup>
        <Label for="edit-company">Unternehmen</Label>
        <Input id="edit-company" type="text" bind:value={editForm.company} />
      </FormGroup>
      <FormGroup>
        <Label for="edit-description">Beschreibung</Label>
        <Input id="edit-description" type="textarea" rows={4} bind:value={editForm.description} />
      </FormGroup>
    </Form>
  </ModalBody>
  <ModalFooter>
    <Button color="secondary" on:click={closeEditModal} disabled={editSaving}>Abbrechen</Button>
    <Button color="primary" on:click={saveEdit} disabled={editSaving}>
      {#if editSaving}<Spinner size="sm" /> {/if}Speichern
    </Button>
  </ModalFooter>
</Modal>
