// SPDX-License-Identifier: AGPL-3.0-only
/**
 * Typed Sidecar-Client.
 *
 * - Basiert auf {@link ./sidecar.gen.ts | sidecar.gen.ts}, erzeugt aus
 *   `sidecar/contract/openapi.json` via `openapi-typescript` (siehe
 *   `pnpm gen:sidecar`).
 * - Liest Port + Token beim ersten Aufruf via Tauri-Commands
 *   `get_sidecar_port` und `get_sidecar_token` und injiziert
 *   `X-Sidecar-Token` in jeden Request.
 *
 * Nutzung:
 * ```ts
 * import { sidecar } from "@/lib/sidecar";
 * const { data, error } = await sidecar.GET("/projects", {});
 * ```
 */
import createClient, { type Middleware } from "openapi-fetch";
import { invoke } from "@tauri-apps/api/core";
import type { paths } from "./sidecar.gen";

interface SidecarHandshake {
  port: number;
  token: string;
}

let handshakeCache: SidecarHandshake | null = null;

async function getHandshake(): Promise<SidecarHandshake> {
  if (handshakeCache) return handshakeCache;
  const [port, token] = await Promise.all([
    invoke<number>("get_sidecar_port"),
    invoke<string>("get_sidecar_token"),
  ]);
  handshakeCache = { port, token };
  return handshakeCache;
}

/** Override fuer Tests / Browser-Preview ausserhalb von Tauri. */
export function setSidecarHandshake(hs: SidecarHandshake): void {
  handshakeCache = hs;
}

const authMiddleware: Middleware = {
  async onRequest({ request }) {
    const { token } = await getHandshake();
    request.headers.set("X-Sidecar-Token", token);
    request.headers.set("Accept", "application/json");
    return request;
  },
};

/**
 * Factory fuer den typed Client. Port wird lazy beim ersten Request geholt
 * ueber einen `fetch`-Wrapper, weil `baseUrl` sonst zum Import-Zeitpunkt
 * feststehen muesste (Sidecar-Port ist aber dynamisch).
 */
function createSidecarClient() {
  const dynamicFetch: typeof fetch = async (input, init) => {
    const { port } = await getHandshake();
    const base = `http://127.0.0.1:${port}`;
    const url =
      typeof input === "string"
        ? new URL(input, base).toString()
        : input instanceof URL
          ? input.toString()
          : new URL((input as Request).url, base).toString();
    return fetch(url, init);
  };

  const client = createClient<paths>({
    baseUrl: "http://127.0.0.1",
    fetch: dynamicFetch,
  });
  client.use(authMiddleware);
  return client;
}

export const sidecar = createSidecarClient();
export type { paths, components } from "./sidecar.gen";
