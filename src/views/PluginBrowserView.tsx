// SPDX-License-Identifier: AGPL-3.0-only
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

/**
 * Stub-View: Plugin-Browser.
 *
 * TODO (Welle 2): `GET /plugins/available`, Install via `POST
 * /plugins/install`, Enable/Disable pro Projekt.
 */
export function PluginBrowserView() {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Plugin-Browser</CardTitle>
      </CardHeader>
      <CardContent>
        <p className="text-sm text-muted-foreground">
          Platzhalter. Wird in Welle 2 mit Plugin-Endpunkten verdrahtet.
        </p>
      </CardContent>
    </Card>
  );
}
