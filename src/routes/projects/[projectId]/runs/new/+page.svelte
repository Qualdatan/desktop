<!-- SPDX-License-Identifier: AGPL-3.0-only -->
<script lang="ts">
  import { page } from '$app/stores';
  import { goto } from '$app/navigation';
  import {
    Card,
    CardBody,
    CardHeader,
    CardFooter,
    Button,
    Form,
    FormGroup,
    Label,
    Input,
    Alert,
    Spinner,
    Badge,
    ButtonGroup
  } from 'sveltestrap';
  import { api } from '$lib/sidecar';

  type RunOut = { id: string };

  let step = $state(1);
  let config = $state({ method: '', model: '', facets: [] as string[] });
  let materialsText = $state('');
  let facetInput = $state('');
  let starting = $state(false);
  let startError = $state<string | null>(null);

  const projectId = $derived($page.params.projectId);

  const materialLines = $derived(
    materialsText
      .split('\n')
      .map((s) => s.trim())
      .filter(Boolean)
  );

  const step1Valid = $derived(config.method.trim().length > 0);
  const step2Valid = $derived(materialLines.length > 0);

  function addFacet() {
    const v = facetInput.trim();
    if (!v) return;
    if (config.facets.includes(v)) {
      facetInput = '';
      return;
    }
    config.facets = [...config.facets, v];
    facetInput = '';
  }

  function removeFacet(f: string) {
    config.facets = config.facets.filter((x) => x !== f);
  }

  function next() {
    if (step === 1 && !step1Valid) return;
    if (step === 2 && !step2Valid) return;
    if (step < 3) step += 1;
  }

  function back() {
    if (step > 1) step -= 1;
  }

  async function submit() {
    if (!step1Valid || !step2Valid) return;
    starting = true;
    startError = null;
    try {
      const payload = {
        config: {
          method: config.method.trim(),
          ...(config.model.trim() ? { model: config.model.trim() } : {}),
          facets: config.facets
        },
        materials: materialLines
      };
      const runOut = await api.post<RunOut>(`/projects/${projectId}/runs`, payload);
      await goto(`/runs/${runOut.id}`);
    } catch (err) {
      startError = err instanceof Error ? err.message : String(err);
      starting = false;
    }
  }
</script>

<Card>
  <CardHeader>
    <div class="d-flex justify-content-between align-items-center">
      <h2 class="h4 mb-0">Neuer Run</h2>
      <ButtonGroup size="sm">
        <Button color={step === 1 ? 'primary' : 'secondary'} outline={step !== 1} on:click={() => (step = 1)}>1 Methode</Button>
        <Button
          color={step === 2 ? 'primary' : 'secondary'}
          outline={step !== 2}
          disabled={!step1Valid}
          on:click={() => step1Valid && (step = 2)}
        >2 Materialien</Button>
        <Button
          color={step === 3 ? 'primary' : 'secondary'}
          outline={step !== 3}
          disabled={!step1Valid || !step2Valid}
          on:click={() => step1Valid && step2Valid && (step = 3)}
        >3 Review</Button>
      </ButtonGroup>
    </div>
  </CardHeader>

  <CardBody>
    {#if startError}
      <Alert color="danger">Run konnte nicht gestartet werden: {startError}</Alert>
    {/if}

    {#if step === 1}
      <Form on:submit={(e) => { e.preventDefault(); next(); }}>
        <FormGroup>
          <Label for="method">Methode</Label>
          <Input
            id="method"
            type="text"
            placeholder="z.B. prozessanalyse"
            bind:value={config.method}
            required
          />
        </FormGroup>
        <FormGroup>
          <Label for="model">Modell (optional)</Label>
          <Input
            id="model"
            type="text"
            placeholder="z.B. claude-sonnet-4"
            bind:value={config.model}
          />
        </FormGroup>
        <FormGroup>
          <Label for="facet">Facets</Label>
          <div class="d-flex gap-2">
            <Input
              id="facet"
              type="text"
              placeholder="Facet-Name eingeben"
              bind:value={facetInput}
              on:keydown={(e: KeyboardEvent) => {
                if (e.key === 'Enter') {
                  e.preventDefault();
                  addFacet();
                }
              }}
            />
            <Button color="secondary" on:click={addFacet} disabled={!facetInput.trim()}>+</Button>
          </div>
          {#if config.facets.length > 0}
            <ul class="list-unstyled mt-2 d-flex flex-wrap gap-2">
              {#each config.facets as f (f)}
                <li>
                  <Badge color="info" class="p-2">
                    {f}
                    <Button close size="sm" class="ms-2" on:click={() => removeFacet(f)} aria-label="Entfernen" />
                  </Badge>
                </li>
              {/each}
            </ul>
          {:else}
            <small class="text-muted">Keine Facets. Optional.</small>
          {/if}
        </FormGroup>
      </Form>
    {:else if step === 2}
      <Form on:submit={(e) => { e.preventDefault(); next(); }}>
        <FormGroup>
          <Label for="materials">Materialien (eine Pfad-Zeile pro Material)</Label>
          <Input
            id="materials"
            type="textarea"
            rows={10}
            placeholder={'input/transcripts/HKS/BOE/interview-01.md\ninput/documents/HKS/BOE/plan.pdf'}
            bind:value={materialsText}
          />
          <small class="text-muted">Erkannt: {materialLines.length} Material(ien).</small>
        </FormGroup>
      </Form>
    {:else}
      <h3 class="h5">Zusammenfassung</h3>
      <dl class="row">
        <dt class="col-sm-3">Projekt</dt>
        <dd class="col-sm-9"><code>{projectId}</code></dd>

        <dt class="col-sm-3">Methode</dt>
        <dd class="col-sm-9">{config.method}</dd>

        <dt class="col-sm-3">Modell</dt>
        <dd class="col-sm-9">{config.model || '(default)'}</dd>

        <dt class="col-sm-3">Facets</dt>
        <dd class="col-sm-9">
          {#if config.facets.length === 0}
            <span class="text-muted">keine</span>
          {:else}
            {#each config.facets as f (f)}
              <Badge color="info" class="me-1">{f}</Badge>
            {/each}
          {/if}
        </dd>

        <dt class="col-sm-3">Materialien</dt>
        <dd class="col-sm-9">
          <ul class="mb-0">
            {#each materialLines as m (m)}
              <li><code>{m}</code></li>
            {/each}
          </ul>
        </dd>
      </dl>
    {/if}
  </CardBody>

  <CardFooter>
    <div class="d-flex justify-content-between">
      <Button color="secondary" outline on:click={back} disabled={step === 1 || starting}>Zurück</Button>
      {#if step < 3}
        <Button
          color="primary"
          on:click={next}
          disabled={(step === 1 && !step1Valid) || (step === 2 && !step2Valid)}
        >Weiter</Button>
      {:else}
        <Button color="success" on:click={submit} disabled={starting || !step1Valid || !step2Valid}>
          {#if starting}
            <Spinner size="sm" /> Starte…
          {:else}
            Run starten
          {/if}
        </Button>
      {/if}
    </div>
  </CardFooter>
</Card>
