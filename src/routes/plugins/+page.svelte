<!-- SPDX-License-Identifier: AGPL-3.0-only -->
<script lang="ts">
  import {
    Card,
    CardBody,
    CardHeader,
    Nav,
    NavItem,
    NavLink,
    TabContent,
    TabPane,
    Table,
    Button,
    Alert,
    Spinner,
    Badge,
    Modal,
    ModalHeader,
    ModalBody,
    ModalFooter,
    Form,
    FormGroup,
    Label,
    Input
  } from '@sveltestrap/sveltestrap';
  import { api } from '$lib/sidecar';
  import { createResource } from '$lib/queryHelpers';

  type BundleSummary = {
    bundle_id: string;
    name: string;
    version: string;
    description?: string;
    enabled_in_projects: string[];
  };

  type BundleAvailable = {
    bundle_id: string;
    name: string;
    version: string;
    description?: string;
    source: string;
  };

  const installed = createResource(() => api.get<BundleSummary[]>('/plugins'));
  const available = createResource(() => api.get<BundleAvailable[]>('/plugins/available'));

  let activeTab = $state<'installed' | 'discover'>('installed');

  // Install-Modal-State
  let installModalOpen = $state(false);
  let installTarget = $state<BundleAvailable | null>(null);
  let installVersion = $state('');
  let installBusy = $state(false);
  let installError = $state<string | null>(null);

  function openInstallModal(b: BundleAvailable): void {
    installTarget = b;
    installVersion = b.version;
    installError = null;
    installModalOpen = true;
  }

  function closeInstallModal(): void {
    if (installBusy) return;
    installModalOpen = false;
    installTarget = null;
    installError = null;
  }

  async function confirmInstall(): Promise<void> {
    if (!installTarget) return;
    installBusy = true;
    installError = null;
    try {
      const body: { bundle_id: string; version?: string } = {
        bundle_id: installTarget.bundle_id
      };
      const v = installVersion.trim();
      if (v && v !== installTarget.version) body.version = v;
      else if (v) body.version = v;
      await api.post<BundleSummary>('/plugins/install', body);
      installModalOpen = false;
      installTarget = null;
      await Promise.all([installed.refresh(), available.refresh()]);
    } catch (e) {
      installError = e instanceof Error ? e.message : String(e);
    } finally {
      installBusy = false;
    }
  }

  async function uninstall(b: BundleSummary): Promise<void> {
    const ok = confirm(
      `Plugin "${b.name}" (${b.bundle_id} @ ${b.version}) wirklich deinstallieren?`
    );
    if (!ok) return;
    try {
      await api.post(`/plugins/${encodeURIComponent(b.bundle_id)}/uninstall`);
      await Promise.all([installed.refresh(), available.refresh()]);
    } catch (e) {
      alert(`Deinstallation fehlgeschlagen: ${e instanceof Error ? e.message : String(e)}`);
    }
  }

  function errMsg(e: unknown): string {
    return e instanceof Error ? e.message : String(e);
  }
</script>

<Card>
  <CardHeader>
    <h2 class="mb-0"><i class="bi bi-plug-fill me-2"></i>Plugins</h2>
  </CardHeader>
  <CardBody>
    <Nav tabs>
      <NavItem>
        <NavLink
          href="#"
          active={activeTab === 'installed'}
          onclick={(e: Event) => {
            e.preventDefault();
            activeTab = 'installed';
          }}
        >
          Installiert
        </NavLink>
      </NavItem>
      <NavItem>
        <NavLink
          href="#"
          active={activeTab === 'discover'}
          onclick={(e: Event) => {
            e.preventDefault();
            activeTab = 'discover';
          }}
        >
          Entdecken
        </NavLink>
      </NavItem>
    </Nav>

    <TabContent activeTab={activeTab} class="pt-3">
      <TabPane tabId="installed" active={activeTab === 'installed'}>
        {#if installed.loading}
          <div class="text-center p-3"><Spinner /> <span class="ms-2">Lade installierte Plugins...</span></div>
        {:else if installed.error}
          <Alert color="danger">
            Fehler beim Laden der installierten Plugins: {errMsg(installed.error)}
            <Button size="sm" color="secondary" class="ms-2" onclick={() => installed.refresh()}>
              Erneut versuchen
            </Button>
          </Alert>
        {:else if !installed.data || installed.data.length === 0}
          <Alert color="info">Keine Plugins installiert.</Alert>
        {:else}
          <Table striped responsive>
            <thead>
              <tr>
                <th>Name</th>
                <th>Version</th>
                <th>Bundle-ID</th>
                <th>Aktivierung</th>
                <th class="text-end">Aktionen</th>
              </tr>
            </thead>
            <tbody>
              {#each installed.data as b (b.bundle_id)}
                <tr>
                  <td>
                    <strong>{b.name}</strong>
                    {#if b.description}
                      <div class="text-muted small">{b.description}</div>
                    {/if}
                  </td>
                  <td><code>{b.version}</code></td>
                  <td><code>{b.bundle_id}</code></td>
                  <td>
                    <Badge color={b.enabled_in_projects.length > 0 ? 'success' : 'secondary'}>
                      aktiv in {b.enabled_in_projects.length} Projekten
                    </Badge>
                  </td>
                  <td class="text-end">
                    <Button color="danger" size="sm" onclick={() => uninstall(b)}>
                      <i class="bi bi-trash me-1"></i>Deinstallieren
                    </Button>
                  </td>
                </tr>
              {/each}
            </tbody>
          </Table>
        {/if}
      </TabPane>

      <TabPane tabId="discover" active={activeTab === 'discover'}>
        {#if available.loading}
          <div class="text-center p-3"><Spinner /> <span class="ms-2">Lade verfuegbare Plugins...</span></div>
        {:else if available.error}
          <Alert color="danger">
            Fehler beim Laden der verfuegbaren Plugins: {errMsg(available.error)}
            <Button size="sm" color="secondary" class="ms-2" onclick={() => available.refresh()}>
              Erneut versuchen
            </Button>
          </Alert>
        {:else if !available.data || available.data.length === 0}
          <Alert color="info">Plugin-Server nicht erreichbar oder keine Bundles verfuegbar.</Alert>
        {:else}
          <Table striped responsive>
            <thead>
              <tr>
                <th>Name</th>
                <th>Version</th>
                <th>Bundle-ID</th>
                <th>Quelle</th>
                <th class="text-end">Aktionen</th>
              </tr>
            </thead>
            <tbody>
              {#each available.data as b (b.bundle_id + '@' + b.version)}
                <tr>
                  <td>
                    <strong>{b.name}</strong>
                    {#if b.description}
                      <div class="text-muted small">{b.description}</div>
                    {/if}
                  </td>
                  <td><code>{b.version}</code></td>
                  <td><code>{b.bundle_id}</code></td>
                  <td><span class="text-muted small">{b.source}</span></td>
                  <td class="text-end">
                    <Button color="primary" size="sm" onclick={() => openInstallModal(b)}>
                      <i class="bi bi-download me-1"></i>Installieren
                    </Button>
                  </td>
                </tr>
              {/each}
            </tbody>
          </Table>
        {/if}
      </TabPane>
    </TabContent>
  </CardBody>
</Card>

<Modal isOpen={installModalOpen} toggle={closeInstallModal}>
  <ModalHeader toggle={closeInstallModal}>
    Plugin installieren
  </ModalHeader>
  <ModalBody>
    {#if installTarget}
      <p>
        <strong>{installTarget.name}</strong>
        <span class="text-muted">({installTarget.bundle_id})</span>
      </p>
      {#if installTarget.description}
        <p class="text-muted small">{installTarget.description}</p>
      {/if}
      <Form onsubmit={(e: Event) => { e.preventDefault(); void confirmInstall(); }}>
        <FormGroup>
          <Label for="installVersion">Version (optional)</Label>
          <Input
            id="installVersion"
            type="text"
            bind:value={installVersion}
            placeholder={installTarget.version}
            disabled={installBusy}
          />
          <small class="text-muted">
            Standard: {installTarget.version}. Leer lassen oder anpassen, um eine andere Version zu erzwingen.
          </small>
        </FormGroup>
      </Form>
      {#if installError}
        <Alert color="danger" class="mt-2">{installError}</Alert>
      {/if}
    {/if}
  </ModalBody>
  <ModalFooter>
    <Button color="secondary" onclick={closeInstallModal} disabled={installBusy}>
      Abbrechen
    </Button>
    <Button color="primary" onclick={confirmInstall} disabled={installBusy || !installTarget}>
      {#if installBusy}<Spinner size="sm" class="me-1" />{/if}
      Installieren
    </Button>
  </ModalFooter>
</Modal>
