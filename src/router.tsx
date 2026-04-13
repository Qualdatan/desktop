// SPDX-License-Identifier: AGPL-3.0-only
import {
  createRootRoute,
  createRoute,
  createRouter,
  Navigate,
} from "@tanstack/react-router";
import App from "./App";
import { ProjectListView } from "./views/ProjectListView";
import { ProjectDetailView } from "./views/ProjectDetailView";
import { RunWizardView } from "./views/RunWizardView";
import { RunMonitorView } from "./views/RunMonitorView";
import { CodebookEditorView } from "./views/CodebookEditorView";
import { ExportView } from "./views/ExportView";
import { PluginBrowserView } from "./views/PluginBrowserView";
import { SettingsView } from "./views/SettingsView";

const rootRoute = createRootRoute({ component: App });

const indexRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: "/",
  component: () => <Navigate to="/projects" replace />,
});

const projectsRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: "/projects",
  component: ProjectListView,
});

const projectDetailRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: "/projects/$projectId",
  component: ProjectDetailView,
});

const runsRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: "/runs",
  component: RunWizardView,
});

const runMonitorRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: "/runs/$runId",
  component: RunMonitorView,
});

const codebookRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: "/codebook",
  component: CodebookEditorView,
});

const exportRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: "/export",
  component: ExportView,
});

const pluginsRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: "/plugins",
  component: PluginBrowserView,
});

const settingsRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: "/settings",
  component: SettingsView,
});

const routeTree = rootRoute.addChildren([
  indexRoute,
  projectsRoute,
  projectDetailRoute,
  runsRoute,
  runMonitorRoute,
  codebookRoute,
  exportRoute,
  pluginsRoute,
  settingsRoute,
]);

export const router = createRouter({ routeTree });

declare module "@tanstack/react-router" {
  interface Register {
    router: typeof router;
  }
}
