<!-- SPDX-License-Identifier: AGPL-3.0-only -->
<script lang="ts">
  import {
    Card,
    CardBody,
    CardHeader,
    Table,
    Button,
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
  } from 'sveltestrap';
  import { goto } from '$app/navigation';
  import { api } from '$lib/sidecar';
  import { createResource } from '$lib/queryHelpers';

  type ProjectOut = {
    id: string;
    name: string;
    company: string;
    description?: string | null;
    created_at: string;
    updated_at: string;
  };

  const projects = createResource<ProjectOut[]>(() => api.get('/projects'));

  let modalOpen = $state(false);
  let form = $state({ name: '', company: '', description: '' });
  let saving = $state(false);
  let saveError = $state<string | null>(null);

  function openModal() {
    form = { name: '', company: '', description: '' };
    saveError = null;
    modalOpen = true;
  }

  async function createProject() {
    saving = true;
    saveError = null;
    try {
      await api.post('/projects', form);
      modalOpen = false;
      form = { name: '', company: '', description: '' };
      await projects.refresh();
    } catch (e) {
      saveError = String(e);
    } finally {
      saving = false;
    }
  }

  async function deleteProject(id: string) {
    if (!confirm('Projekt wirklich löschen?')) return;
    try {
      await api.delete(`/projects/${id}`);
      await projects.refresh();
    } catch (e) {
      alert(`Löschen fehlgeschlagen: ${String(e)}`);
    }
  }

  function formatDate(iso: string): string {
    try {
      return new Date(iso).toLocaleString('de-DE');
    } catch {
      return iso;
    }
  }
</script>

<div class="d-flex justify-content-between align-items-center mb-3">
  <h1 class="mb-0">Projekte</h1>
  <Button color="primary" on:click={openModal}>
    <i class="bi bi-plus-lg me-1"></i>Neues Projekt
  </Button>
</div>

{#if projects.loading}
  <div class="d-flex justify-content-center py-5">
    <Spinner />
  </div>
{:else if projects.error}
  <Alert color="danger">{projects.error}</Alert>
{:else if projects.data?.length === 0}
  <Alert color="info">Noch keine Projekte. Lege eines an.</Alert>
{:else}
  <Card>
    <CardBody>
      <Table hover responsive>
        <thead>
          <tr>
            <th>Name</th>
            <th>Unternehmen</th>
            <th>Erstellt</th>
            <th class="text-end">Aktionen</th>
          </tr>
        </thead>
        <tbody>
          {#each projects.data ?? [] as p (p.id)}
            <tr>
              <td>{p.name}</td>
              <td>{p.company}</td>
              <td>{formatDate(p.created_at)}</td>
              <td class="text-end">
                <Button
                  size="sm"
                  color="outline-primary"
                  class="me-2"
                  on:click={() => goto(`/projects/${p.id}`)}
                >
                  Öffnen
                </Button>
                <Button size="sm" color="outline-danger" on:click={() => deleteProject(p.id)}>
                  Löschen
                </Button>
              </td>
            </tr>
          {/each}
        </tbody>
      </Table>
    </CardBody>
  </Card>
{/if}

<Modal isOpen={modalOpen} toggle={() => (modalOpen = !modalOpen)}>
  <ModalHeader toggle={() => (modalOpen = !modalOpen)}>Neues Projekt</ModalHeader>
  <ModalBody>
    {#if saveError}
      <Alert color="danger">{saveError}</Alert>
    {/if}
    <Form>
      <FormGroup>
        <Label for="project-name">Name *</Label>
        <Input
          id="project-name"
          type="text"
          bind:value={form.name}
          placeholder="z.B. BOE-Neubau"
          required
        />
      </FormGroup>
      <FormGroup>
        <Label for="project-company">Unternehmen *</Label>
        <Input
          id="project-company"
          type="text"
          bind:value={form.company}
          placeholder="z.B. HKS"
          required
        />
      </FormGroup>
      <FormGroup>
        <Label for="project-description">Beschreibung</Label>
        <Input
          id="project-description"
          type="textarea"
          rows={3}
          bind:value={form.description}
        />
      </FormGroup>
    </Form>
  </ModalBody>
  <ModalFooter>
    <Button color="secondary" on:click={() => (modalOpen = false)} disabled={saving}>
      Abbrechen
    </Button>
    <Button
      color="primary"
      on:click={createProject}
      disabled={saving || !form.name.trim() || !form.company.trim()}
    >
      {#if saving}
        <Spinner size="sm" class="me-2" />
      {/if}
      Speichern
    </Button>
  </ModalFooter>
</Modal>
