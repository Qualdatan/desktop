# SPDX-License-Identifier: AGPL-3.0-only
"""Geteilte FastAPI-Dependencies fuer Sidecar-Router.

Welle 1 erweitert dies bei Bedarf (z.B. PluginManager-Singleton).

Exports:
    * :func:`get_app_db` - Singleton-``AppDB``-Dependency fuer Projekte/Runs/Codebook.
    * :func:`get_plugin_manager` - Singleton-:class:`PluginManager`-Dependency
      fuer den Plugins-Router. Der Registry-Pfad wird aus der Env-Variable
      ``QUALDATAN_SIDECAR_PLUGIN_REGISTRY`` gelesen (Fallback: platformdirs-Default).
"""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

from qualdatan_core.app_db import AppDB, open_app_db
from qualdatan_plugins.manager import PluginManager
from qualdatan_plugins.registry import PluginRegistry


@lru_cache(maxsize=1)
def get_app_db() -> AppDB:
    """Singleton-AppDB. Pfad aus ``QUALDATAN_SIDECAR_APP_DB`` env oder Default."""

    path = os.environ.get("QUALDATAN_SIDECAR_APP_DB")
    return open_app_db(path)


@lru_cache(maxsize=1)
def get_plugin_manager() -> PluginManager:
    """Singleton-PluginManager.

    Honoriert ``QUALDATAN_SIDECAR_PLUGIN_REGISTRY`` fuer den Registry-DB-Pfad
    (nuetzlich fuer Tests und portable Builds); sonst greift der Default der
    :class:`PluginRegistry` (``QUALDATAN_PLUGIN_REGISTRY`` env oder platformdirs).
    """

    registry_path = os.environ.get("QUALDATAN_SIDECAR_PLUGIN_REGISTRY")
    if registry_path:
        registry = PluginRegistry(Path(registry_path))
        return PluginManager(registry=registry)
    return PluginManager()


def reset_app_db_singleton() -> None:
    """Test-Hilfe: setzt das LRU-cached :func:`get_app_db` zurueck."""

    get_app_db.cache_clear()


def reset_plugin_manager_singleton() -> None:
    """Test-Hilfe: setzt das LRU-cached :func:`get_plugin_manager` zurueck."""

    get_plugin_manager.cache_clear()


__all__ = [
    "get_app_db",
    "get_plugin_manager",
    "reset_app_db_singleton",
    "reset_plugin_manager_singleton",
]
