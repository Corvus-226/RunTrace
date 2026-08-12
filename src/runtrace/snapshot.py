"""Capture and persist one experiment's reproducibility snapshot."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from pydantic import ValidationError

from runtrace.config import load_yaml_config
from runtrace.environment import GpuMetadata, collect_environment_metadata
from runtrace.git import collect_git_metadata
from runtrace.models import (
    EnvironmentSnapshot,
    ExperimentSnapshot,
    GitSnapshot,
    GpuSnapshot,
    HardwareSnapshot,
    PlatformSnapshot,
    RuntimeSnapshot,
    Snapshot,
)
from runtrace.project import require_initialized_project
from runtrace.storage import SnapshotStore


class SnapshotCaptureError(RuntimeError):
    """Raised when captured values cannot form a valid snapshot."""


@dataclass(frozen=True, slots=True)
class SavedSnapshot:
    """A validated snapshot and the path where it was persisted."""

    snapshot: Snapshot
    path: Path


def create_snapshot(
    current_directory: Path,
    *,
    name: str | None = None,
    config_path: Path | None = None,
    command: str | None = None,
) -> SavedSnapshot:
    """Capture local metadata, validate it, and persist one snapshot."""
    project_root = require_initialized_project(current_directory)
    loaded_config = None
    if config_path is not None:
        loaded_config = load_yaml_config(
            config_path,
            current_directory=current_directory,
            project_root=project_root,
        )

    git_metadata = collect_git_metadata(
        project_root,
        exclude_runtrace_data=True,
    )
    environment_metadata = collect_environment_metadata()

    try:
        snapshot = Snapshot(
            name=name,
            git=GitSnapshot(
                commit=git_metadata.commit,
                branch=git_metadata.branch,
                detached=git_metadata.detached,
                dirty=git_metadata.dirty,
            ),
            runtime=RuntimeSnapshot(
                python=environment_metadata.runtime.version,
                implementation=environment_metadata.runtime.implementation,
                platform=PlatformSnapshot(
                    system=environment_metadata.platform.system,
                    release=environment_metadata.platform.release,
                    architecture=environment_metadata.platform.architecture,
                    machine=environment_metadata.platform.machine,
                ),
            ),
            environment=EnvironmentSnapshot(
                packages=environment_metadata.packages,
            ),
            hardware=HardwareSnapshot(
                gpu=_gpu_snapshot(environment_metadata.gpu),
            ),
            experiment=ExperimentSnapshot(
                command=command,
                config_path=loaded_config.path if loaded_config is not None else None,
                config_hash=(
                    loaded_config.sha256 if loaded_config is not None else None
                ),
                config=loaded_config.values if loaded_config is not None else None,
            ),
        )
    except ValidationError as error:
        raise SnapshotCaptureError(
            f"Captured snapshot metadata is invalid ({error.error_count()} errors). "
            "Check the run name and configuration values."
        ) from error

    path = SnapshotStore(project_root).save(snapshot)
    return SavedSnapshot(snapshot=snapshot, path=path)


def _gpu_snapshot(gpu: GpuMetadata | None) -> GpuSnapshot | None:
    if gpu is None:
        return None
    return GpuSnapshot(
        devices=gpu.devices,
        driver_versions=gpu.driver_versions,
        cuda_version=gpu.cuda_version,
    )
