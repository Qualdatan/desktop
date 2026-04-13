// SPDX-License-Identifier: AGPL-3.0-only
/**
 * Typisiertes Fetch-Wrapper um die FastAPI-Sidecar-REST-API.
 *
 * Im Tauri-Kontext werden Port und Token lazily ueber die Rust-Commands
 * `get_sidecar_port` / `get_sidecar_token` geholt und anschliessend gecached.
 * Ausserhalb Tauris (z.B. `pnpm dev` im Browser) fallen wir auf die
 * Env-Variablen `VITE_SIDECAR_PORT` und `VITE_SIDECAR_TOKEN` zurueck.
 */

type SidecarInfo = {
  port: number;
  token: string;
};

let cached: SidecarInfo | null = null;
let inflight: Promise<SidecarInfo> | null = null;

function isTauri(): boolean {
  // Tauri 2: window.__TAURI_INTERNALS__ wird vom Rust-Host injiziert.
  return typeof window !== 'undefined' && '__TAURI_INTERNALS__' in window;
}

async function loadSidecarInfo(): Promise<SidecarInfo> {
  if (cached) return cached;
  if (inflight) return inflight;

  inflight = (async () => {
    if (isTauri()) {
      const { invoke } = await import('@tauri-apps/api/core');
      const [port, token] = await Promise.all([
        invoke<number>('get_sidecar_port'),
        invoke<string>('get_sidecar_token')
      ]);
      cached = { port, token };
    } else {
      const env = import.meta.env as Record<string, string | undefined>;
      const portStr = env.VITE_SIDECAR_PORT;
      const token = env.VITE_SIDECAR_TOKEN;
      if (!portStr || !token) {
        throw new Error(
          'Sidecar-Info nicht verfuegbar: weder Tauri-Context noch VITE_SIDECAR_PORT/TOKEN gesetzt.'
        );
      }
      cached = { port: Number(portStr), token };
    }
    return cached;
  })();

  try {
    return await inflight;
  } finally {
    inflight = null;
  }
}

/** Basis-URL `http://127.0.0.1:<port>` fuer raw-fetch / EventSource. */
export async function apiBase(): Promise<string> {
  const { port } = await loadSidecarInfo();
  return `http://127.0.0.1:${port}`;
}

/** Auth-Token (View-Code sollte `api.*` nutzen, dies nur fuer EventSource). */
export async function apiToken(): Promise<string> {
  const { token } = await loadSidecarInfo();
  return token;
}

async function request<T>(
  method: string,
  path: string,
  body?: unknown,
  init?: RequestInit
): Promise<T> {
  const { port, token } = await loadSidecarInfo();
  const url = `http://127.0.0.1:${port}${path.startsWith('/') ? path : `/${path}`}`;
  const headers = new Headers(init?.headers ?? {});
  headers.set('X-Sidecar-Token', token);
  if (body !== undefined && !headers.has('Content-Type')) {
    headers.set('Content-Type', 'application/json');
  }
  const res = await fetch(url, {
    ...init,
    method,
    headers,
    body: body !== undefined ? JSON.stringify(body) : init?.body
  });
  if (!res.ok) {
    const text = await res.text().catch(() => '');
    throw new Error(`Sidecar ${method} ${path} -> ${res.status}: ${text}`);
  }
  if (res.status === 204) return undefined as T;
  const ct = res.headers.get('Content-Type') ?? '';
  if (ct.includes('application/json')) return (await res.json()) as T;
  return (await res.text()) as unknown as T;
}

export const api = {
  get: <T>(path: string, init?: RequestInit) => request<T>('GET', path, undefined, init),
  post: <T>(path: string, body?: unknown, init?: RequestInit) =>
    request<T>('POST', path, body, init),
  patch: <T>(path: string, body?: unknown, init?: RequestInit) =>
    request<T>('PATCH', path, body, init),
  delete: <T>(path: string, init?: RequestInit) => request<T>('DELETE', path, undefined, init)
};
