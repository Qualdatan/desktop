// SPDX-License-Identifier: AGPL-3.0-only
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

/**
 * Stub-View: Export.
 *
 * TODO (Welle 2): `POST /export/qdpx` (Interview) und `POST /export/xlsx`.
 */
export function ExportView() {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Export</CardTitle>
      </CardHeader>
      <CardContent>
        <p className="text-sm text-muted-foreground">
          Platzhalter. QDPX + XLSX-Export folgen in Welle 2.
        </p>
      </CardContent>
    </Card>
  );
}
