// SPDX-License-Identifier: AGPL-3.0-only
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

/**
 * Stub-View: Run-Wizard.
 *
 * TODO (Welle 2): Schrittweiser Dialog — Projekt, Methode, Dateien,
 * Plugin-Auswahl — dann `POST /runs`.
 */
export function RunWizardView() {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Neuen Run starten</CardTitle>
      </CardHeader>
      <CardContent>
        <p className="text-sm text-muted-foreground">
          Platzhalter. Wird in Welle 2 zum Multi-Step-Wizard.
        </p>
      </CardContent>
    </Card>
  );
}
