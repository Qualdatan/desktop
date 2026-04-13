<!-- SPDX-License-Identifier: AGPL-3.0-only -->
<script lang="ts">
  import { page } from '$app/stores';
  import {
    Card,
    CardBody,
    CardHeader,
    Table,
    Button,
    Input,
    Modal,
    ModalHeader,
    ModalBody,
    ModalFooter,
    FormGroup,
    Label,
    Alert,
    Spinner,
    Badge
  } from '@sveltestrap/sveltestrap';
  import { api } from '$lib/sidecar';
  import { createResource } from '$lib/queryHelpers';

  type CodebookEntryOut = {
    code_id: string;
    name: string;
    description?: string | null;
    parent_id?: string | null;
    color: string;
    anchors: string[];
  };

  const projectId = $derived($page.params.projectId);

  const codebook = createResource(() =>
    api.get<CodebookEntryOut[]>(`/codebook/${projectId}`)
  );

  // Debounce-Timer pro code_id (name/color Inline-Edits).
  let timers = new Map<string, number>();
  function debouncedPatch(code_id: string, patch: object) {
    clearTimeout(timers.get(code_id));
    timers.set(
      code_id,
      window.setTimeout(async () => {
        try {
          await api.patch(`/codebook/${projectId}/codes/${code_id}`, patch);
          await codebook.refresh();
        } catch (e) {
          console.error('Codebook-PATCH fehlgeschlagen', e);
        }
      }, 500)
    );
  }

  // Modal-State fuer Description / Anchors.
  let editingDesc = $state<{ code_id: string; value: string } | null>(null);
  let editingAnchors = $state<{ code_id: string; lines: string } | null>(null);
  let savingModal = $state(false);

  function openDesc(entry: CodebookEntryOut) {
    editingDesc = { code_id: entry.code_id, value: entry.description ?? '' };
  }
  function openAnchors(entry: CodebookEntryOut) {
    editingAnchors = {
      code_id: entry.code_id,
      lines: (entry.anchors ?? []).join('\n')
    };
  }

  async function saveDesc() {
    if (!editingDesc) return;
    savingModal = true;
    try {
      await api.patch(`/codebook/${projectId}/codes/${editingDesc.code_id}`, {
        description: editingDesc.value
      });
      await codebook.refresh();
      editingDesc = null;
    } catch (e) {
      console.error(e);
    } finally {
      savingModal = false;
    }
  }

  async function saveAnchors() {
    if (!editingAnchors) return;
    savingModal = true;
    try {
      const anchors = editingAnchors.lines
        .split('\n')
        .map((l) => l.trim())
        .filter((l) => l.length > 0);
      await api.patch(`/codebook/${projectId}/codes/${editingAnchors.code_id}`, {
        anchors
      });
      await codebook.refresh();
      editingAnchors = null;
    } catch (e) {
      console.error(e);
    } finally {
      savingModal = false;
    }
  }

  async function resetCode(code_id: string) {
    try {
      await api.delete(`/codebook/${projectId}/codes/${code_id}`);
      await codebook.refresh();
    } catch (e) {
      console.error(e);
    }
  }
</script>

<Card class="mb-3">
  <CardHeader>
    <h2 class="h4 mb-0">Codebook-Editor</h2>
  </CardHeader>
  <CardBody>
    <p class="mb-0">
      Projekt <code>{projectId}</code>. Aenderungen ueberschreiben
      Bundle-Defaults; <strong>Zuruecksetzen</strong> stellt den Default wieder
      her.
    </p>
  </CardBody>
</Card>

{#if codebook.loading}
  <div class="d-flex align-items-center gap-2">
    <Spinner size="sm" /> <span>Lade Codebook&hellip;</span>
  </div>
{:else if codebook.error}
  <Alert color="danger">
    Fehler beim Laden des Codebooks: {String(codebook.error)}
  </Alert>
{:else if !codebook.data || codebook.data.length === 0}
  <Alert color="info">Keine Eintraege im Codebook.</Alert>
{:else}
  <Card>
    <CardBody class="p-0">
      <Table responsive hover class="mb-0 align-middle">
        <thead>
          <tr>
            <th style="width: 12rem;">Code-ID</th>
            <th>Name</th>
            <th style="width: 6rem;">Farbe</th>
            <th style="width: 14rem;">Beschreibung</th>
            <th style="width: 14rem;">Ankerbeispiele</th>
            <th style="width: 10rem;">Aktion</th>
          </tr>
        </thead>
        <tbody>
          {#each codebook.data as entry (entry.code_id)}
            <tr>
              <td>
                <code>{entry.code_id}</code>
                {#if entry.parent_id}
                  <br /><Badge color="secondary">&uarr; {entry.parent_id}</Badge>
                {/if}
              </td>
              <td>
                <Input
                  type="text"
                  value={entry.name}
                  on:input={(e) =>
                    debouncedPatch(entry.code_id, {
                      name: (e.target as HTMLInputElement).value
                    })}
                />
              </td>
              <td>
                <input
                  type="color"
                  class="form-control form-control-color"
                  value={entry.color}
                  on:input={(e) =>
                    debouncedPatch(entry.code_id, {
                      color: (e.target as HTMLInputElement).value
                    })}
                  aria-label="Farbe fuer {entry.code_id}"
                />
              </td>
              <td>
                <Badge color="light" class="text-dark me-2">
                  {(entry.description ?? '').length} Zeichen
                </Badge>
                <Button size="sm" color="secondary" on:click={() => openDesc(entry)}>
                  Bearbeiten
                </Button>
              </td>
              <td>
                <Badge color="light" class="text-dark me-2">
                  {entry.anchors?.length ?? 0} Anker
                </Badge>
                <Button size="sm" color="secondary" on:click={() => openAnchors(entry)}>
                  Bearbeiten
                </Button>
              </td>
              <td>
                <Button
                  size="sm"
                  color="outline-danger"
                  on:click={() => resetCode(entry.code_id)}
                >
                  Zuruecksetzen
                </Button>
              </td>
            </tr>
          {/each}
        </tbody>
      </Table>
    </CardBody>
  </Card>
{/if}

<!-- Description-Modal -->
<Modal isOpen={editingDesc !== null} toggle={() => (editingDesc = null)} size="lg">
  <ModalHeader toggle={() => (editingDesc = null)}>
    Beschreibung bearbeiten{editingDesc ? ` — ${editingDesc.code_id}` : ''}
  </ModalHeader>
  <ModalBody>
    {#if editingDesc}
      <FormGroup>
        <Label for="desc-textarea">Beschreibung (Markdown/Plaintext)</Label>
        <textarea
          id="desc-textarea"
          class="form-control"
          rows="10"
          bind:value={editingDesc.value}
        ></textarea>
      </FormGroup>
    {/if}
  </ModalBody>
  <ModalFooter>
    <Button color="secondary" on:click={() => (editingDesc = null)} disabled={savingModal}>
      Abbrechen
    </Button>
    <Button color="primary" on:click={saveDesc} disabled={savingModal}>
      {#if savingModal}<Spinner size="sm" />{/if} Speichern
    </Button>
  </ModalFooter>
</Modal>

<!-- Anchors-Modal -->
<Modal
  isOpen={editingAnchors !== null}
  toggle={() => (editingAnchors = null)}
  size="lg"
>
  <ModalHeader toggle={() => (editingAnchors = null)}>
    Ankerbeispiele bearbeiten{editingAnchors ? ` — ${editingAnchors.code_id}` : ''}
  </ModalHeader>
  <ModalBody>
    {#if editingAnchors}
      <FormGroup>
        <Label for="anchors-textarea">Ein Ankerbeispiel pro Zeile</Label>
        <textarea
          id="anchors-textarea"
          class="form-control font-monospace"
          rows="12"
          bind:value={editingAnchors.lines}
        ></textarea>
        <small class="text-muted">
          Leere Zeilen werden ignoriert; Whitespace wird getrimmt.
        </small>
      </FormGroup>
    {/if}
  </ModalBody>
  <ModalFooter>
    <Button
      color="secondary"
      on:click={() => (editingAnchors = null)}
      disabled={savingModal}
    >
      Abbrechen
    </Button>
    <Button color="primary" on:click={saveAnchors} disabled={savingModal}>
      {#if savingModal}<Spinner size="sm" />{/if} Speichern
    </Button>
  </ModalFooter>
</Modal>
