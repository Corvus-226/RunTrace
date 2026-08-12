"""Validated, human-readable models for persisted experiment snapshots."""

from __future__ import annotations

import secrets
from datetime import datetime, timezone
from typing import Annotated, Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    JsonValue,
    StringConstraints,
    field_validator,
)

RunId = Annotated[
    str,
    StringConstraints(pattern=r"^[0-9a-f]{12}$"),
]
RunName = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1, max_length=200),
]


def generate_run_id() -> str:
    """Return a short, collision-resistant identifier for one snapshot."""
    return secrets.token_hex(6)


def utc_now() -> datetime:
    """Return the current time as an aware UTC datetime."""
    return datetime.now(timezone.utc)


class _SnapshotModel(BaseModel):
    """Shared strict configuration for persisted schema components."""

    model_config = ConfigDict(extra="forbid", frozen=True)


class GitSnapshot(_SnapshotModel):
    """Git state that identifies the code used for an experiment."""

    commit: Annotated[str, StringConstraints(min_length=1)]
    branch: str | None
    detached: bool
    dirty: bool


class PlatformSnapshot(_SnapshotModel):
    """Operating-system and machine information."""

    system: str
    release: str
    architecture: str
    machine: str


class RuntimeSnapshot(_SnapshotModel):
    """Python runtime and host platform information."""

    python: Annotated[str, StringConstraints(min_length=1)]
    implementation: Annotated[str, StringConstraints(min_length=1)]
    platform: PlatformSnapshot


class EnvironmentSnapshot(_SnapshotModel):
    """Installed Python distribution versions."""

    packages: dict[str, str]

    @field_validator("packages")
    @classmethod
    def _sort_packages(cls, packages: dict[str, str]) -> dict[str, str]:
        for name, version in packages.items():
            if not name.strip() or not version.strip():
                raise ValueError("package names and versions must not be empty")
        return dict(sorted(packages.items()))


class GpuSnapshot(_SnapshotModel):
    """Optional NVIDIA GPU and CUDA information."""

    devices: tuple[str, ...]
    driver_versions: tuple[str, ...]
    cuda_version: str | None


class HardwareSnapshot(_SnapshotModel):
    """Best-effort hardware metadata for an experiment."""

    gpu: GpuSnapshot | None = None


class ExperimentSnapshot(_SnapshotModel):
    """User-supplied experiment context."""

    command: str | None = None
    config_path: str | None = None
    config_hash: str | None = None
    config: JsonValue | None = None


class Snapshot(_SnapshotModel):
    """The complete versioned record for one experiment run."""

    schema_version: Literal[1] = 1
    run_id: RunId = Field(default_factory=generate_run_id)
    name: RunName | None = None
    timestamp: datetime = Field(default_factory=utc_now)
    git: GitSnapshot
    runtime: RuntimeSnapshot
    environment: EnvironmentSnapshot
    hardware: HardwareSnapshot = Field(default_factory=HardwareSnapshot)
    experiment: ExperimentSnapshot = Field(default_factory=ExperimentSnapshot)

    @field_validator("timestamp")
    @classmethod
    def _normalize_timestamp(cls, timestamp: datetime) -> datetime:
        if timestamp.tzinfo is None or timestamp.utcoffset() is None:
            raise ValueError("timestamp must include a timezone")
        return timestamp.astimezone(timezone.utc)
