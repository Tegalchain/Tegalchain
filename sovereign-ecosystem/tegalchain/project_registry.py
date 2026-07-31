"""Greenledger project registry — opaque project_id ↔ system_type for the oracle.

Registry entries name sustainable verticals for tegalid policy. They do not
embed subsystem architecture (voice stack, Android, meters, etc.).
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from greentelemetry_protocol_spec.models import SystemType

ROOT = Path(__file__).resolve().parent
DEFAULT_PROJECTS_FILE = ROOT / "data" / "greenledger_projects.json"


class ProjectStatus(str, Enum):
    ACTIVE = "active"
    PLANNED = "planned"
    SUSPENDED = "suspended"


class EnvironmentalScope(str, Enum):
    """High-level sustainability classification for Greenledger projects."""

    SUSTAINABLE_DEPIN = "sustainable_depin"
    UTILITY_PROSUMER = "utility_prosumer"
    ENVIRONMENTAL_SUSTAINABILITY = "environmental_sustainability"
    OTHER = "other"


@dataclass(frozen=True, slots=True)
class GreenledgerProject:
    project_id: str
    system_type: SystemType | None
    category: str
    status: ProjectStatus
    description: str
    requires_sip: bool
    environmental_scope: EnvironmentalScope

    @property
    def is_mint_ready(self) -> bool:
        return self.status is ProjectStatus.ACTIVE and self.system_type is not None


class ProjectRegistry:
    """Registered environmentally sustainable / utility projects on the Greenledger."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self._projects: dict[str, GreenledgerProject] = {}
        self._load()

    def _load(self) -> None:
        if not self.path.is_file():
            self._projects = {}
            return
        data = json.loads(self.path.read_text(encoding="utf-8"))
        entries = data.get("projects", [])
        loaded: dict[str, GreenledgerProject] = {}
        for entry in entries:
            raw_type = entry.get("system_type")
            system_type = SystemType(str(raw_type)) if raw_type else None
            scope_raw = str(entry.get("environmental_scope", EnvironmentalScope.OTHER.value))
            try:
                environmental_scope = EnvironmentalScope(scope_raw)
            except ValueError:
                environmental_scope = EnvironmentalScope.OTHER
            project = GreenledgerProject(
                project_id=str(entry["project_id"]),
                system_type=system_type,
                category=str(entry.get("category", "unknown")),
                status=ProjectStatus(str(entry.get("status", "planned"))),
                description=str(entry.get("description", "")),
                requires_sip=bool(entry.get("requires_sip", False)),
                environmental_scope=environmental_scope,
            )
            loaded[project.project_id] = project
        self._projects = loaded

    def reload(self) -> None:
        self._load()

    def get(self, project_id: str) -> GreenledgerProject | None:
        return self._projects.get(project_id)

    def all_projects(self) -> list[GreenledgerProject]:
        return list(self._projects.values())

    def active_projects(self) -> list[GreenledgerProject]:
        return [p for p in self._projects.values() if p.is_mint_ready]


def get_projects_file() -> Path:
    return Path(os.environ.get("TEGALID_PROJECTS_FILE", str(DEFAULT_PROJECTS_FILE)))


def resolve_project_registry() -> ProjectRegistry:
    return ProjectRegistry(get_projects_file())


def assert_project_registered(project_id: str, system_type: SystemType) -> GreenledgerProject:
    registry = resolve_project_registry()
    project = registry.get(project_id)
    if project is None:
        raise ValueError(
            f"project_id {project_id!r} is not registered on the Greenledger project registry"
        )
    if not project.is_mint_ready:
        raise ValueError(
            f"project_id {project_id!r} is not active for mint "
            f"(status={project.status.value})"
        )
    if project.system_type is not system_type:
        raise ValueError(
            f"project_id {project_id!r} is registered for "
            f"{project.system_type.value if project.system_type else 'unknown'}, "
            f"not {system_type.value}"
        )
    return project
