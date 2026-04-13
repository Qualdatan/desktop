// SPDX-License-Identifier: AGPL-3.0-only
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

/**
 * Stub-View: Einstellungen.
 *
 * TODO (Welle 2): API-Keys (Anthropic/OpenAI), Sidecar-Status, Theme.
 */
export function SettingsView() {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Einstellungen</CardTitle>
      </CardHeader>
      <CardContent>
        <p className="text-sm text-muted-foreground">
          Platzhalter. API-Keys + Sidecar-Status folgen in Welle 2.
        </p>
      </CardContent>
    </Card>
  );
}
