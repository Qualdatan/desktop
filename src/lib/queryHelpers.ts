// SPDX-License-Identifier: AGPL-3.0-only
/**
 * Minimaler SWR-Stil Helper auf Basis von Svelte-5-Runes.
 *
 * Benutzung in `+page.svelte`:
 *
 *   <script lang="ts">
 *     import { createResource } from '$lib/queryHelpers';
 *     import { api } from '$lib/sidecar';
 *     const projects = createResource(() => api.get<Project[]>('/projects'));
 *   </script>
 *
 *   {#if projects.loading}...{:else if projects.error}...{:else}
 *     {#each projects.data ?? [] as p}...{/each}
 *   {/if}
 *   <button onclick={projects.refresh}>Reload</button>
 */

export type Resource<T> = {
  readonly data: T | undefined;
  readonly error: unknown;
  readonly loading: boolean;
  refresh: () => Promise<void>;
};

export function createResource<T>(fn: () => Promise<T>): Resource<T> {
  // Svelte-5-Runes: $state() erzeugt tief reaktive Slots.
  let data = $state<T | undefined>(undefined);
  let error = $state<unknown>(undefined);
  let loading = $state(true);

  async function refresh(): Promise<void> {
    loading = true;
    error = undefined;
    try {
      data = await fn();
    } catch (e) {
      error = e;
    } finally {
      loading = false;
    }
  }

  // Initial-Load (feuern, Ergebnis wird reaktiv gesetzt).
  void refresh();

  return {
    get data() {
      return data;
    },
    get error() {
      return error;
    },
    get loading() {
      return loading;
    },
    refresh
  };
}
