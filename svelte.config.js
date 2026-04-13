// SPDX-License-Identifier: AGPL-3.0-only
import adapter from '@sveltejs/adapter-static';
import { vitePreprocess } from '@sveltejs/vite-plugin-svelte';

/** @type {import('@sveltejs/kit').Config} */
const config = {
  preprocess: vitePreprocess(),
  kit: {
    // Static SPA fuer Tauri: client-only, Fallback auf index.html damit
    // dynamische Routen ([projectId], [runId], ...) clientseitig geroutet werden.
    adapter: adapter({
      pages: 'build',
      assets: 'build',
      fallback: 'index.html',
      precompress: false,
      strict: false
    }),
    alias: {
      $lib: 'src/lib'
    }
  }
};

export default config;
