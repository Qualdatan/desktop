// SPDX-License-Identifier: AGPL-3.0-only
/**
 * Placeholder fuer die generierten Sidecar-Typen.
 *
 * Diese Datei wird durch `pnpm gen:sidecar` aus
 * `sidecar/contract/openapi.json` via `openapi-typescript` ueberschrieben.
 * Der Platzhalter existiert, damit `tsc --noEmit` im frisch geklonten Repo
 * nicht scheitert, solange `pnpm install && pnpm gen:sidecar` noch nicht
 * gelaufen ist.
 */
/* eslint-disable @typescript-eslint/no-empty-object-type */
export interface paths {
  [path: string]: never;
}
export interface components {
  schemas: Record<string, never>;
}
export type operations = Record<string, never>;
