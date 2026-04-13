// SPDX-License-Identifier: AGPL-3.0-only
import { Link, Outlet } from "@tanstack/react-router";

/**
 * Root-Shell der Desktop-App.
 *
 * Rendert eine Sidebar mit Links zu den acht MVP-Views (Welle 2) und einen
 * {@link Outlet} fuer die Kind-Routen.
 */
export default function App() {
  return (
    <div className="flex min-h-screen">
      <aside className="w-56 border-r bg-muted/30 p-4">
        <h1 className="mb-4 text-lg font-semibold">Qualdatan</h1>
        <nav className="flex flex-col gap-1 text-sm">
          <Link to="/projects" className="[&.active]:font-semibold">
            Projekte
          </Link>
          <Link to="/runs" className="[&.active]:font-semibold">
            Runs
          </Link>
          <Link to="/codebook" className="[&.active]:font-semibold">
            Codebook
          </Link>
          <Link to="/export" className="[&.active]:font-semibold">
            Export
          </Link>
          <Link to="/plugins" className="[&.active]:font-semibold">
            Plugins
          </Link>
          <Link to="/settings" className="[&.active]:font-semibold">
            Einstellungen
          </Link>
        </nav>
      </aside>
      <main className="flex-1 p-6">
        <Outlet />
      </main>
    </div>
  );
}
