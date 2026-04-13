// SPDX-License-Identifier: AGPL-3.0-only
// Voll-SPA-Modus: Kein SSR, kein Prerender. SvelteKit liefert nur das
// Client-Bundle aus, das der Tauri-Shell (oder Browser-Fallback) laedt.
export const ssr = false;
export const prerender = false;
