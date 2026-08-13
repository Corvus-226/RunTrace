"""Initialize and locate local RunTrace project state."""

from __future__ import annotations

import os
from pathlib import Path

from ml_runtrace.git import GitMetadataError, find_git_root

_DEFAULT_CONFIG = """# RunTrace project configuration.
[runtrace]
schema_version = 1
"""


class ProjectInitializationError(RuntimeError):
    """Raised when a RunTrace project cannot be initialized safely."""


def require_initialized_project(path: Path) -> Path:
    """Return the containing RunTrace project or raise an actionable error."""
    try:
        project_root = find_git_root(path)
    except GitMetadataError as error:
        raise ProjectInitializationError(str(error)) from error

    configuration = project_root / "runtrace.toml"
    metadata_candidate = project_root / ".runtrace"
    runs_candidate = metadata_candidate / "runs"
    if any(
        not candidate.exists() and not candidate.is_symlink()
        for candidate in (configuration, metadata_candidate, runs_candidate)
    ):
        raise ProjectInitializationError(
            f"RunTrace is not initialized in {project_root}. "
            "Run `ml-runtrace init` first."
        )

    _validate_file(configuration, project_root, label="RunTrace configuration")
    metadata_directory = _validate_directory(
        metadata_candidate,
        project_root,
        label="RunTrace metadata directory",
    )
    _validate_directory(
        metadata_directory / "runs",
        metadata_directory,
        label="RunTrace runs directory",
    )
    return project_root


def initialize_project(path: Path) -> Path:
    """Initialize RunTrace at the Git root containing ``path``.

    Existing configuration, run directories, and stored files are preserved.
    The returned path is the resolved Git work-tree root.
    """
    try:
        project_root = find_git_root(path)
    except GitMetadataError as error:
        raise ProjectInitializationError(str(error)) from error

    configuration = project_root / "runtrace.toml"
    if configuration.exists() or configuration.is_symlink():
        _validate_file(configuration, project_root, label="RunTrace configuration")

    metadata_directory = _ensure_directory(
        project_root / ".runtrace",
        project_root,
        label="RunTrace metadata directory",
    )
    _ensure_directory(
        metadata_directory / "runs",
        metadata_directory,
        label="RunTrace runs directory",
    )

    if not configuration.exists() and not configuration.is_symlink():
        _create_configuration(configuration, project_root)

    return project_root


def _ensure_directory(path: Path, parent: Path, *, label: str) -> Path:
    if not path.exists() and not path.is_symlink():
        try:
            path.mkdir()
        except FileExistsError:
            pass
        except OSError as error:
            raise ProjectInitializationError(
                f"Could not create {label} {path}: {error}"
            ) from error

    return _validate_directory(path, parent, label=label)


def _validate_directory(path: Path, parent: Path, *, label: str) -> Path:
    try:
        resolved = path.resolve(strict=True)
    except OSError as error:
        raise ProjectInitializationError(
            f"Could not resolve {label} {path}: {error}"
        ) from error
    if not resolved.is_dir():
        raise ProjectInitializationError(f"{label} is not a directory: {path}.")
    _ensure_within(resolved, parent, label=label)
    return resolved


def _validate_file(path: Path, parent: Path, *, label: str) -> Path:
    try:
        resolved = path.resolve(strict=True)
    except OSError as error:
        raise ProjectInitializationError(
            f"Could not resolve {label} {path}: {error}"
        ) from error
    if not resolved.is_file():
        raise ProjectInitializationError(f"{label} is not a file: {path}.")
    _ensure_within(resolved, parent, label=label)
    return resolved


def _ensure_within(path: Path, parent: Path, *, label: str) -> None:
    try:
        path.relative_to(parent)
    except ValueError as error:
        raise ProjectInitializationError(
            f"{label} escapes its allowed project directory: {path}."
        ) from error


def _create_configuration(path: Path, project_root: Path) -> None:
    try:
        with path.open("x", encoding="utf-8", newline="\n") as stream:
            stream.write(_DEFAULT_CONFIG)
            stream.flush()
            os.fsync(stream.fileno())
    except FileExistsError:
        _validate_file(path, project_root, label="RunTrace configuration")
    except OSError as error:
        raise ProjectInitializationError(
            f"Could not create RunTrace configuration {path}: {error}"
        ) from error
