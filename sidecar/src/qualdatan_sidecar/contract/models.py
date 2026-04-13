# SPDX-License-Identifier: AGPL-3.0-only
"""Pydantic-Modelle der gefrorenen Sidecar-API.

Alle Typen sind Pydantic v2 ``BaseModel``. Sie definieren ausschliesslich
**Form** (Felder, Typen, Defaults) - keine Businesslogik. Welle 1 darf
Felder ergaenzen, solange die OpenAPI-Signatur rueckwaertskompatibel
bleibt; Breaking-Changes erfordern einen Minor-Bump.

Example:
    >>> from qualdatan_sidecar.contract.models import ProjectCreate
    >>> ProjectCreate(name="HKS", company="HKS").model_dump()
    {'name': 'HKS', 'company': 'HKS', 'description': None}
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

# ---------------------------------------------------------------------------
# Projects
# ---------------------------------------------------------------------------


class ProjectCreate(BaseModel):
    """Anlage eines neuen Analyse-Projekts."""

    model_config = ConfigDict(extra="forbid")

    name: str = Field(..., min_length=1, max_length=200)
    company: str = Field(..., description="Kuerzel, z.B. 'HKS' oder 'PBN'.")
    description: str | None = None


class ProjectOut(BaseModel):
    """Persistierter Projekt-Record."""

    id: str
    name: str
    company: str
    description: str | None = None
    created_at: datetime
    updated_at: datetime


class ProjectPatch(BaseModel):
    """Teil-Update eines Projekts. Nur gesetzte Felder werden geschrieben."""

    model_config = ConfigDict(extra="forbid")

    name: str | None = None
    company: str | None = None
    description: str | None = None


# ---------------------------------------------------------------------------
# Runs
# ---------------------------------------------------------------------------


RunStatus = Literal["pending", "running", "completed", "failed", "cancelled"]
"""Status-Maschine fuer einen Analyse-Run."""


class RunConfig(BaseModel):
    """Laufkonfiguration (Methode, Codebook, LLM-Parameter)."""

    model_config = ConfigDict(extra="forbid")

    method: str = Field(..., description="Pfad/Kuerzel einer Method-Recipe.")
    codebook: str | None = Field(default=None, description="Kuerzel des Codebooks.")
    model: str | None = Field(default=None, description="Claude-Modell-ID.")
    temperature: float | None = Field(default=None, ge=0.0, le=2.0)
    max_tokens: int | None = Field(default=None, gt=0)
    extra: dict[str, Any] = Field(default_factory=dict)


class RunCreate(BaseModel):
    """Request-Body fuer ``POST /projects/{id}/runs``."""

    model_config = ConfigDict(extra="forbid")

    config: RunConfig
    materials: list[str] = Field(
        default_factory=list,
        description="IDs der einzubeziehenden Materialien. Leer = alle.",
    )


class RunOut(BaseModel):
    """Persistierter Run-Record."""

    id: str
    project_id: str
    status: RunStatus
    config: RunConfig
    started_at: datetime | None = None
    finished_at: datetime | None = None
    error: str | None = None


# ---------------------------------------------------------------------------
# Materials
# ---------------------------------------------------------------------------


class MaterialIn(BaseModel):
    """Upload-Metadaten fuer ein neues Material (Datei wird separat hochgeladen)."""

    model_config = ConfigDict(extra="forbid")

    filename: str
    kind: Literal["interview", "document", "plan"]
    mime_type: str | None = None


class MaterialOut(BaseModel):
    """Persistiertes Material."""

    id: str
    project_id: str
    filename: str
    kind: Literal["interview", "document", "plan"]
    mime_type: str | None = None
    size_bytes: int
    created_at: datetime


# ---------------------------------------------------------------------------
# Codebook
# ---------------------------------------------------------------------------


class CodebookEntryOut(BaseModel):
    """Ein Eintrag im Codebook (Kategorie oder Subcode)."""

    code_id: str
    name: str
    description: str | None = None
    parent_id: str | None = None
    color: str | None = Field(default=None, description="Hex-Farbe, z.B. '#ffcc00'.")
    anchors: list[str] = Field(default_factory=list)


class CodeOverridePatch(BaseModel):
    """Override eines Codebook-Eintrags auf Projektebene."""

    model_config = ConfigDict(extra="forbid")

    name: str | None = None
    description: str | None = None
    color: str | None = None
    anchors: list[str] | None = None


# ---------------------------------------------------------------------------
# Plugins / Bundles
# ---------------------------------------------------------------------------


class BundleSummary(BaseModel):
    """Im Desktop installiertes Plugin-Bundle."""

    bundle_id: str
    name: str
    version: str
    description: str | None = None
    enabled_in_projects: list[str] = Field(default_factory=list)


class BundleAvailable(BaseModel):
    """Im Plugin-Server verfuegbares, noch nicht lokal installiertes Bundle."""

    bundle_id: str
    name: str
    version: str
    description: str | None = None
    download_url: str


class BundleInstallRequest(BaseModel):
    """Install-Request fuer ein Bundle aus dem Plugin-Server."""

    model_config = ConfigDict(extra="forbid")

    bundle_id: str
    version: str | None = Field(default=None, description="Leer = latest.")


# ---------------------------------------------------------------------------
# Export
# ---------------------------------------------------------------------------


class ExportRequest(BaseModel):
    """Export-Request fuer QDPX oder XLSX."""

    model_config = ConfigDict(extra="forbid")

    project_id: str
    run_id: str | None = Field(default=None, description="Leer = letzter Run.")
    include_annotations: bool = True


class ExportResult(BaseModel):
    """Ergebnis eines Export-Jobs."""

    path: str = Field(..., description="Absoluter Pfad zur erzeugten Datei.")
    format: Literal["qdpx", "xlsx"]
    size_bytes: int
    created_at: datetime


# ---------------------------------------------------------------------------
# Progress (SSE)
# ---------------------------------------------------------------------------


class ProgressEvent(BaseModel):
    """Payload eines Server-Sent-Event aus ``GET /runs/{id}/stream``."""

    event_type: Literal[
        "started",
        "material_started",
        "material_progress",
        "material_finished",
        "finished",
        "failed",
    ]
    run_id: str
    material: str | None = None
    step: str | None = None
    pct: float | None = Field(default=None, ge=0.0, le=100.0)
    message: str | None = None
