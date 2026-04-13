// SPDX-License-Identifier: AGPL-3.0-only
import { sveltekit } from '@sveltejs/kit/vite';
import { defineConfig } from 'vite';

// Tauri-Konvention: Feste Port-Nummer 1420 auf 127.0.0.1, damit der
// Rust-Shell (src-tauri/tauri.conf.json -> devUrl) den Dev-Server findet.
export default defineConfig({
  plugins: [sveltekit()],
  clearScreen: false,
  server: {
    port: 1420,
    strictPort: true,
    host: '127.0.0.1'
  },
  // VITE_* fuer Browser-Fallback (Sidecar-Port/Token ausserhalb Tauri),
  // TAURI_* fuer Tauri-2-Build-Infos.
  envPrefix: ['VITE_', 'TAURI_']
});
