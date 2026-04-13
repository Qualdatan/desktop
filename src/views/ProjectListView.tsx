// SPDX-License-Identifier: AGPL-3.0-only
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

/**
 * Stub-View: Projekt-Liste.
 *
 * TODO (Welle 2): `GET /projects` via `sidecar` + Tabelle, "Neu"-Dialog.
 */
export function ProjectListView() {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Projekte</CardTitle>
      </CardHeader>
      <CardContent>
        <p className="text-sm text-muted-foreground">
          Platzhalter. Wird in Welle 2 mit `GET /projects` befuellt.
        </p>
      </CardContent>
    </Card>
  );
}
