// SPDX-License-Identifier: AGPL-3.0-only
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

/**
 * Stub-View: Run-Monitor.
 *
 * TODO (Welle 2): SSE/WebSocket-Stream `GET /runs/{id}/stream`, Log-Tail,
 * Abbrechen-Button.
 */
export function RunMonitorView() {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Run-Monitor</CardTitle>
      </CardHeader>
      <CardContent>
        <p className="text-sm text-muted-foreground">
          Platzhalter. Wird in Welle 2 mit `GET /runs/{`{run_id}`}/stream`
          verdrahtet.
        </p>
      </CardContent>
    </Card>
  );
}
