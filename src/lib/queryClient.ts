// SPDX-License-Identifier: AGPL-3.0-only
import { QueryClient } from "@tanstack/react-query";

/**
 * Zentrale TanStack-Query-Instanz fuer die gesamte Desktop-App.
 *
 * Defaults:
 * - `staleTime: 30s` — Sidecar-Daten aendern sich selten.
 * - `retry: 1` — Sidecar laeuft lokal, Retries sind selten hilfreich.
 */
export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 30_000,
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
});
