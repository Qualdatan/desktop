// SPDX-License-Identifier: AGPL-3.0-only
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

/**
 * Stub-View: Projekt-Detail.
 *
 * TODO (Welle 2): `GET /projects/{id}` + Tabs (Dateien, Runs, Plugins,
 * Codebook-Overrides).
 */
export function ProjectDetailView() {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Projekt-Detail</CardTitle>
      </CardHeader>
      <CardContent>
        <p className="text-sm text-muted-foreground">
          Platzhalter. Wird in Welle 2 mit `GET /projects/{`{project_id}`}`
          befuellt.
        </p>
      </CardContent>
    </Card>
  );
}
