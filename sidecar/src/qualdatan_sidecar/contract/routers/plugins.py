# SPDX-License-Identifier: AGPL-3.0-only
"""Plugins-Router - Welle 1 Implementierung.

Bindet die Sidecar-API gegen :class:`qualdatan_plugins.manager.PluginManager`.
Die HTTP-Endpunkte sind duenne Wrapper: Installation/Deinstallation,
Aktivierung pro Projekt und Discovery gegen den Plugin-Server (Tap-Index).

Mapping zur ``PluginManager``-API:
    * ``GET /plugins`` -> :meth:`PluginManager.list_installed`
    * ``POST /plugins/install`` -> :meth:`PluginManager.install_from_git`
    * ``POST /plugins/{bundle_id}/uninstall`` -> :meth:`PluginManager.uninstall`
    * ``POST /projects/{project_id}/plugins/{bundle_id}/enable``
      -> :meth:`PluginManager.activate`
    * ``POST /projects/{project_id}/plugins/{bundle_id}/disable``
      -> :meth:`PluginManager.deactivate`
    * ``GET /plugins/available`` -> :class:`qualdatan_plugins.server_client.PluginServerClient.search`

Hinweis:
    Das :class:`~qualdatan_sidecar.contract.models.BundleInstallRequest`
    Modell kennt nur ``bundle_id`` und optional ``version``. Der Manager
    braucht zum ``install_from_git`` eine Git-URL. Wir loesen die URL ueber
    den Plugin-Server auf (``get_tap``), fallen bei lokaler Installation
    nicht zurueck - wenn der Index nicht erreichbar ist, liefert der
    Endpoint ``502``.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status

from qualdatan_plugins.manager import PluginManager, PluginManagerError
from qualdatan_plugins.server_client import (
    PluginServerClient,
    PluginServerError,
)

from ...deps import get_plugin_manager
from ..models import BundleAvailable, BundleInstallRequest, BundleSummary

plugins_router = APIRouter(tags=["plugins"])


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _summary_from_installed(ib, *, enabled_in: list[str] | None = None) -> BundleSummary:
    """Baut ein :class:`BundleSummary` aus einem :class:`InstalledBundle`."""

    manifest = ib.manifest
    return BundleSummary(
        bundle_id=ib.id,
        name=manifest.label or manifest.name,
        version=ib.version,
        description=manifest.description or None,
        enabled_in_projects=list(enabled_in or []),
    )


def _projects_for_bundle(manager: PluginManager, bundle_id: str) -> list[str]:
    """Alle Projekt-Ids, in denen ``bundle_id`` aktuell aktiv ist.

    Nutzt die SQLite-Registry direkt (keine Manager-Methode vorhanden).
    """

    cur = manager.registry._conn.execute(  # noqa: SLF001 - Registry exposes no public list-all
        "SELECT project_id FROM active WHERE bundle_id=? ORDER BY project_id",
        (bundle_id,),
    )
    return [row[0] for row in cur.fetchall()]


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@plugins_router.get("/plugins", response_model=list[BundleSummary])
async def list_plugins(
    manager: PluginManager = Depends(get_plugin_manager),
) -> list[BundleSummary]:
    """Listet lokal installierte Plugin-Bundles."""

    out: list[BundleSummary] = []
    for ib in manager.list_installed():
        out.append(
            _summary_from_installed(
                ib, enabled_in=_projects_for_bundle(manager, ib.id)
            )
        )
    return out


@plugins_router.post(
    "/plugins/install",
    response_model=BundleSummary,
    status_code=status.HTTP_201_CREATED,
)
async def install_plugin(
    body: BundleInstallRequest,
    manager: PluginManager = Depends(get_plugin_manager),
) -> BundleSummary:
    """Installiert ein Bundle aus dem Plugin-Server."""

    namespace, _, name = body.bundle_id.partition("/")
    if not namespace or not name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"invalid bundle_id '{body.bundle_id}', expected 'namespace/name'",
        )

    # Tap-Index abfragen -> repo_url + Version.
    try:
        with PluginServerClient() as client:
            entry, versions = client.get_tap(namespace, name)
    except PluginServerError as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"plugin-server unreachable: {e}",
        ) from e

    target_version = body.version or entry.latest_version
    commit_sha = ""
    for v in versions:
        if v.version == target_version:
            commit_sha = v.commit_sha
            break

    if not target_version:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"no version found for {body.bundle_id}",
        )

    try:
        result = manager.install_from_git(
            entry.repo_url, target_version, commit_sha=commit_sha
        )
    except PluginManagerError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        ) from e

    return _summary_from_installed(
        result.bundle, enabled_in=_projects_for_bundle(manager, result.bundle.id)
    )


@plugins_router.post(
    "/plugins/{bundle_id}/uninstall",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def uninstall_plugin(
    bundle_id: str,
    manager: PluginManager = Depends(get_plugin_manager),
) -> None:
    """Deinstalliert ein lokal installiertes Bundle."""

    try:
        manager.uninstall(bundle_id)
    except PluginManagerError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e


@plugins_router.post(
    "/projects/{project_id}/plugins/{bundle_id}/enable",
    response_model=BundleSummary,
)
async def enable_plugin_for_project(
    project_id: str,
    bundle_id: str,
    manager: PluginManager = Depends(get_plugin_manager),
) -> BundleSummary:
    """Aktiviert ein Bundle fuer ein Projekt."""

    try:
        ib = manager.activate(bundle_id, project_id=project_id)
    except PluginManagerError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e
    return _summary_from_installed(
        ib, enabled_in=_projects_for_bundle(manager, bundle_id)
    )


@plugins_router.post(
    "/projects/{project_id}/plugins/{bundle_id}/disable",
    response_model=BundleSummary,
)
async def disable_plugin_for_project(
    project_id: str,
    bundle_id: str,
    manager: PluginManager = Depends(get_plugin_manager),
) -> BundleSummary:
    """Deaktiviert ein Bundle fuer ein Projekt."""

    manager.deactivate(bundle_id, project_id=project_id)
    ib = manager.registry.get_installed(bundle_id)
    if ib is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"bundle '{bundle_id}' is not installed",
        )
    return _summary_from_installed(
        ib, enabled_in=_projects_for_bundle(manager, bundle_id)
    )


@plugins_router.get("/plugins/available", response_model=list[BundleAvailable])
async def list_available_plugins() -> list[BundleAvailable]:
    """Listet im Plugin-Server verfuegbare (noch nicht installierte) Bundles."""

    try:
        with PluginServerClient() as client:
            results = client.search("")
    except PluginServerError:
        return []

    return [
        BundleAvailable(
            bundle_id=entry.id,
            name=entry.label or entry.name,
            version=entry.latest_version,
            description=entry.description or None,
            download_url=entry.repo_url,
        )
        for entry in results
    ]


__all__ = ["plugins_router"]
