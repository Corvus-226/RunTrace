"""Capture and persist one experiment's reproducibility snapshot."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from pydantic import ValidationError

from ml_runtrace.config import load_yaml_config
from ml_runtrace.environment import (
    ArchivePackageSourceMetadata,
    DirectoryPackageSourceMetadata,
    GpuMetadata,
    PackageSourceMetadata,
    VcsPackageSourceMetadata,
    collect_environment_metadata,
)
from ml_runtrace.git import collect_git_metadata
from ml_runtrace.models import (
    ArchivePackageSourceSnapshot,
    DirectoryPackageSourceSnapshot,
    EnvironmentSnapshot,
    ExperimentSnapshot,
    GitSnapshot,
    GpuSnapshot,
    HardwareSnapshot,
    PackageSourceSnapshot,
    PlatformSnapshot,
    RuntimeSnapshot,
    Snapshot,
    VcsPackageSourceSnapshot,
)
from ml_runtrace.project import require_initialized_project
from ml_runtrace.storage import SnapshotStore


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
    command_argv: tuple[str, ...] | None = None,
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
                package_sources={
                    name: _package_source_snapshot(source)
                    for name, source in environment_metadata.package_sources.items()
                },
            ),
            hardware=HardwareSnapshot(
                gpu=_gpu_snapshot(environment_metadata.gpu),
            ),
            experiment=ExperimentSnapshot(
                command=command,
                command_argv=command_argv,
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


def _package_source_snapshot(
    source: PackageSourceMetadata,
) -> PackageSourceSnapshot:
    if isinstance(source, VcsPackageSourceMetadata):
        return VcsPackageSourceSnapshot(
            url=source.url,
            vcs=source.vcs,
            commit_id=source.commit_id,
            requested_revision=source.requested_revision,
            subdirectory=source.subdirectory,
        )
    if isinstance(source, ArchivePackageSourceMetadata):
        return ArchivePackageSourceSnapshot(
            url=source.url,
            hash=source.hash,
            subdirectory=source.subdirectory,
        )
    if isinstance(source, DirectoryPackageSourceMetadata):
        return DirectoryPackageSourceSnapshot(editable=source.editable)
    raise TypeError(f"Unsupported package source metadata: {type(source).__name__}")
