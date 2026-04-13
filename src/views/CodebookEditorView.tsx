// SPDX-License-Identifier: AGPL-3.0-only
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

/**
 * Stub-View: Codebook-Editor.
 *
 * TODO (Welle 2): `GET /codebook/{project_id}`, Patch-Overrides via
 * `PATCH /codebook/{project_id}/codes/{code_id}`.
 */
export function CodebookEditorView() {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Codebook-Editor</CardTitle>
      </CardHeader>
      <CardContent>
        <p className="text-sm text-muted-foreground">
          Platzhalter. Wird in Welle 2 mit Codebook-Endpunkten verdrahtet.
        </p>
      </CardContent>
    </Card>
  );
}
