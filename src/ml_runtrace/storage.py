"""Atomic local YAML persistence for RunTrace snapshots."""

from __future__ import annotations

import os
import re
import tempfile
from pathlib import Path

import yaml
from pydantic import ValidationError

from ml_runtrace.models import Snapshot

_FULL_RUN_ID = re.compile(r"^[0-9a-f]{12}$")
_RUN_ID_REFERENCE = re.compile(r"^[0-9a-f]{1,12}$")


class SnapshotStorageError(RuntimeError):
    """Base error for snapshot storage failures."""


class SnapshotConflictError(SnapshotStorageError):
    """Raised when a save would replace an existing snapshot."""


class SnapshotNotFoundError(SnapshotStorageError):
    """Raised when no snapshot matches a run ID reference."""


class SnapshotAmbiguousIdError(SnapshotStorageError):
    """Raised when an abbreviated run ID matches multiple snapshots."""


class SnapshotStore:
    """Persist snapshots beneath an initialized project's ``.runtrace`` path."""

    def __init__(self, project_root: Path) -> None:
        candidate = Path(project_root).expanduser()
        if not candidate.exists():
            raise SnapshotStorageError(f"Project path does not exist: {candidate}.")
        if not candidate.is_dir():
            raise SnapshotStorageError(f"Project path is not a directory: {candidate}.")
        try:
            self._project_root = candidate.resolve(strict=True)
        except OSError as error:
            raise SnapshotStorageError(
                f"Could not resolve project path {candidate}: {error}"
            ) from error

    @property
    def project_root(self) -> Path:
        """Return the resolved project root used by this store."""
        return self._project_root

    def save(self, snapshot: Snapshot) -> Path:
        """Atomically save a snapshot without replacing an existing run ID."""
        runs_directory = self._runs_directory(create=True)
        assert runs_directory is not None

        destination = runs_directory / f"{snapshot.run_id}.yaml"
        lock_path = runs_directory / f".{snapshot.run_id}.lock"
        temporary_path: Path | None = None
        lock_descriptor: int | None = None
        lock_acquired = False

        try:
            try:
                lock_descriptor = os.open(
                    lock_path,
                    os.O_CREAT | os.O_EXCL | os.O_WRONLY,
                    0o600,
                )
                lock_acquired = True
            except FileExistsError as error:
                raise SnapshotConflictError(
                    f"Snapshot {snapshot.run_id} is already being saved. "
                    f"Remove {lock_path.name} only if no RunTrace process is active."
                ) from error

            os.close(lock_descriptor)
            lock_descriptor = None

            if destination.exists() or destination.is_symlink():
                raise SnapshotConflictError(
                    f"Snapshot {snapshot.run_id} already exists; it was not replaced."
                )

            try:
                document = yaml.safe_dump(
                    snapshot.model_dump(mode="json"),
                    allow_unicode=True,
                    sort_keys=False,
                )
            except yaml.YAMLError as error:
                raise SnapshotStorageError(
                    f"Could not serialize snapshot {snapshot.run_id} as YAML."
                ) from error

            descriptor, temporary_name = tempfile.mkstemp(
                dir=runs_directory,
                prefix=f".{snapshot.run_id}.",
                suffix=".tmp",
            )
            temporary_path = Path(temporary_name)
            with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as stream:
                stream.write(document)
                stream.flush()
                os.fsync(stream.fileno())

            os.replace(temporary_path, destination)
            temporary_path = None
            return destination
        except SnapshotStorageError:
            raise
        except OSError as error:
            raise SnapshotStorageError(
                f"Could not save snapshot {snapshot.run_id}: {error}"
            ) from error
        finally:
            if lock_descriptor is not None:
                os.close(lock_descriptor)
            if temporary_path is not None:
                temporary_path.unlink(missing_ok=True)
            if lock_acquired:
                lock_path.unlink(missing_ok=True)

    def load(self, run_id: str) -> Snapshot:
        """Load and validate a snapshot by full or unique abbreviated run ID."""
        resolved_id = self.resolve_run_id(run_id)
        runs_directory = self._runs_directory(create=False)
        assert runs_directory is not None
        return self._load_path(runs_directory / f"{resolved_id}.yaml", runs_directory)

    def list_snapshots(self) -> list[Snapshot]:
        """Return validated snapshots from newest to oldest."""
        runs_directory = self._runs_directory(create=False)
        if runs_directory is None:
            return []

        snapshots = [
            self._load_path(path, runs_directory)
            for path in self._snapshot_files(runs_directory)
        ]
        return sorted(
            snapshots,
            key=lambda snapshot: (snapshot.timestamp, snapshot.run_id),
            reverse=True,
        )

    def resolve_run_id(self, run_id: str) -> str:
        """Resolve a full or unique abbreviated run ID to its canonical ID."""
        reference = run_id.strip().casefold()
        if _RUN_ID_REFERENCE.fullmatch(reference) is None:
            raise SnapshotNotFoundError(
                "Run ID must contain between 1 and 12 hexadecimal characters."
            )

        runs_directory = self._runs_directory(create=False)
        if runs_directory is None:
            raise SnapshotNotFoundError(f"No snapshot matches run ID {reference}.")

        available_ids = [path.stem for path in self._snapshot_files(runs_directory)]
        matches = sorted(
            candidate for candidate in available_ids if candidate.startswith(reference)
        )
        if not matches:
            raise SnapshotNotFoundError(f"No snapshot matches run ID {reference}.")
        if len(matches) > 1:
            choices = ", ".join(matches)
            raise SnapshotAmbiguousIdError(
                f"Run ID {reference} is ambiguous; matches: {choices}."
            )
        return matches[0]

    def _runs_directory(self, *, create: bool) -> Path | None:
        metadata_candidate = self._project_root / ".runtrace"
        if not metadata_candidate.exists() and not metadata_candidate.is_symlink():
            raise SnapshotStorageError(
                f"RunTrace is not initialized in {self._project_root}. "
                "Run `ml-runtrace init` first."
            )

        metadata_directory = self._resolve_directory(
            metadata_candidate,
            label="RunTrace metadata directory",
        )
        self._ensure_within_project(metadata_directory)

        runs_candidate = metadata_directory / "runs"
        if not runs_candidate.exists() and not runs_candidate.is_symlink():
            if not create:
                return None
            try:
                runs_candidate.mkdir()
            except OSError as error:
                raise SnapshotStorageError(
                    f"Could not create snapshot directory {runs_candidate}: {error}"
                ) from error

        runs_directory = self._resolve_directory(
            runs_candidate,
            label="Snapshot directory",
        )
        self._ensure_within_project(runs_directory)
        try:
            runs_directory.relative_to(metadata_directory)
        except ValueError as error:
            raise SnapshotStorageError(
                f"Snapshot directory escapes .runtrace: {runs_candidate}."
            ) from error
        return runs_directory

    def _snapshot_files(self, runs_directory: Path) -> list[Path]:
        try:
            candidates = list(runs_directory.glob("*.yaml"))
        except OSError as error:
            raise SnapshotStorageError(
                f"Could not list snapshots in {runs_directory}: {error}"
            ) from error

        paths: list[Path] = []
        for candidate in candidates:
            if _FULL_RUN_ID.fullmatch(candidate.stem) is None:
                raise SnapshotStorageError(
                    f"Unexpected snapshot filename {candidate.name}; "
                    "expected <12-character-run-id>.yaml."
                )
            resolved = self._resolve_file(candidate, runs_directory)
            paths.append(resolved)
        return sorted(paths, key=lambda path: path.name)

    def _load_path(self, path: Path, runs_directory: Path) -> Snapshot:
        resolved_path = self._resolve_file(path, runs_directory)
        try:
            document = resolved_path.read_text(encoding="utf-8")
        except OSError as error:
            raise SnapshotStorageError(
                f"Could not read snapshot file {resolved_path.name}: {error}"
            ) from error

        try:
            raw_snapshot = yaml.safe_load(document)
        except yaml.YAMLError as error:
            raise SnapshotStorageError(
                f"Snapshot file {resolved_path.name} contains invalid YAML; "
                "repair or remove it."
            ) from error

        try:
            snapshot = Snapshot.model_validate(raw_snapshot)
        except ValidationError as error:
            raise SnapshotStorageError(
                f"Snapshot file {resolved_path.name} does not match schema version 1 "
                f"({error.error_count()} validation errors); repair or remove it."
            ) from error

        if snapshot.run_id != resolved_path.stem:
            raise SnapshotStorageError(
                f"Snapshot file {resolved_path.name} declares run ID "
                f"{snapshot.run_id}; rename or repair the file."
            )
        return snapshot

    def _resolve_directory(self, path: Path, *, label: str) -> Path:
        try:
            resolved = path.resolve(strict=True)
        except OSError as error:
            raise SnapshotStorageError(
                f"Could not resolve {label} {path}: {error}"
            ) from error
        if not resolved.is_dir():
            raise SnapshotStorageError(f"{label} is not a directory: {path}.")
        return resolved

    def _resolve_file(self, path: Path, parent: Path) -> Path:
        try:
            resolved = path.resolve(strict=True)
        except OSError as error:
            raise SnapshotStorageError(
                f"Could not resolve snapshot file {path.name}: {error}"
            ) from error
        if not resolved.is_file():
            raise SnapshotStorageError(f"Snapshot path is not a file: {path}.")
        try:
            resolved.relative_to(parent)
        except ValueError as error:
            raise SnapshotStorageError(
                f"Snapshot file escapes the snapshot directory: {path.name}."
            ) from error
        return resolved

    def _ensure_within_project(self, path: Path) -> None:
        try:
            path.relative_to(self._project_root)
        except ValueError as error:
            raise SnapshotStorageError(
                f"Storage path escapes the project root: {path}."
            ) from error
