"""Deterministic, structured differences between experiment snapshots."""

from __future__ import annotations

import json
from dataclasses import dataclass
from enum import Enum

from ml_runtrace.models import Snapshot

_MISSING = object()


class DifferenceSection(str, Enum):
    """Stable output groups for reproducibility differences."""

    CONFIGURATION = "Configuration"
    GIT = "Git"
    RUNTIME = "Runtime"
    ENVIRONMENT = "Environment"


class DifferenceKind(str, Enum):
    """How one value differs from the first snapshot to the second."""

    ADDED = "added"
    REMOVED = "removed"
    CHANGED = "changed"


@dataclass(frozen=True, slots=True)
class SnapshotDifference:
    """One deterministic change between two snapshot fields."""

    section: DifferenceSection
    path: str
    kind: DifferenceKind
    before: object | None
    after: object | None


@dataclass(frozen=True, slots=True)
class SnapshotComparison:
    """All relevant differences from one snapshot to another."""

    before_run_id: str
    after_run_id: str
    differences: tuple[SnapshotDifference, ...]


def compare_snapshots(before: Snapshot, after: Snapshot) -> SnapshotComparison:
    """Compare reproducibility-relevant values in stable section/path order."""
    differences: list[SnapshotDifference] = []

    _compare_field(
        differences,
        DifferenceSection.CONFIGURATION,
        "command",
        before.experiment.command,
        after.experiment.command,
    )
    before_argv = (
        _MISSING
        if before.experiment.command_argv is None
        else list(before.experiment.command_argv)
    )
    after_argv = (
        _MISSING
        if after.experiment.command_argv is None
        else list(after.experiment.command_argv)
    )
    _compare_nested(
        differences,
        DifferenceSection.CONFIGURATION,
        "command.argv",
        before_argv,
        after_argv,
    )
    _compare_field(
        differences,
        DifferenceSection.CONFIGURATION,
        "config.path",
        before.experiment.config_path,
        after.experiment.config_path,
    )
    _compare_field(
        differences,
        DifferenceSection.CONFIGURATION,
        "config.sha256",
        before.experiment.config_hash,
        after.experiment.config_hash,
    )
    before_config = (
        _MISSING if before.experiment.config_path is None else before.experiment.config
    )
    after_config = (
        _MISSING if after.experiment.config_path is None else after.experiment.config
    )
    _compare_nested(
        differences,
        DifferenceSection.CONFIGURATION,
        "config.values",
        before_config,
        after_config,
    )

    for path, before_value, after_value in (
        ("commit", before.git.commit, after.git.commit),
        ("branch", before.git.branch, after.git.branch),
        ("detached", before.git.detached, after.git.detached),
        ("dirty", before.git.dirty, after.git.dirty),
    ):
        _compare_field(
            differences,
            DifferenceSection.GIT,
            path,
            before_value,
            after_value,
        )

    for path, before_value, after_value in (
        ("python", before.runtime.python, after.runtime.python),
        (
            "implementation",
            before.runtime.implementation,
            after.runtime.implementation,
        ),
        (
            "platform.system",
            before.runtime.platform.system,
            after.runtime.platform.system,
        ),
        (
            "platform.release",
            before.runtime.platform.release,
            after.runtime.platform.release,
        ),
        (
            "platform.architecture",
            before.runtime.platform.architecture,
            after.runtime.platform.architecture,
        ),
        (
            "platform.machine",
            before.runtime.platform.machine,
            after.runtime.platform.machine,
        ),
    ):
        _compare_field(
            differences,
            DifferenceSection.RUNTIME,
            path,
            before_value,
            after_value,
        )

    package_names = sorted(
        before.environment.packages.keys() | after.environment.packages.keys()
    )
    for package_name in package_names:
        _compare_field(
            differences,
            DifferenceSection.ENVIRONMENT,
            package_name,
            before.environment.packages.get(package_name, _MISSING),
            after.environment.packages.get(package_name, _MISSING),
        )

    before_sources = {
        name: source.model_dump(mode="json", exclude_none=True)
        for name, source in before.environment.package_sources.items()
    }
    after_sources = {
        name: source.model_dump(mode="json", exclude_none=True)
        for name, source in after.environment.package_sources.items()
    }
    _compare_nested(
        differences,
        DifferenceSection.ENVIRONMENT,
        "sources",
        before_sources,
        after_sources,
    )

    return SnapshotComparison(
        before_run_id=before.run_id,
        after_run_id=after.run_id,
        differences=tuple(differences),
    )


def _compare_nested(
    differences: list[SnapshotDifference],
    section: DifferenceSection,
    path: str,
    before: object,
    after: object,
) -> None:
    if isinstance(before, dict) and isinstance(after, dict):
        keys = sorted(before.keys() | after.keys())
        for key in keys:
            _compare_nested(
                differences,
                section,
                _nested_path(path, key),
                before.get(key, _MISSING),
                after.get(key, _MISSING),
            )
        return

    if isinstance(before, list) and isinstance(after, list):
        for index in range(max(len(before), len(after))):
            _compare_nested(
                differences,
                section,
                f"{path}[{index}]",
                before[index] if index < len(before) else _MISSING,
                after[index] if index < len(after) else _MISSING,
            )
        return

    if before is _MISSING and isinstance(after, dict) and after:
        for key in sorted(after):
            _compare_nested(
                differences,
                section,
                _nested_path(path, key),
                _MISSING,
                after[key],
            )
        return

    if after is _MISSING and isinstance(before, dict) and before:
        for key in sorted(before):
            _compare_nested(
                differences,
                section,
                _nested_path(path, key),
                before[key],
                _MISSING,
            )
        return

    if before is _MISSING and isinstance(after, list) and after:
        for index, value in enumerate(after):
            _compare_nested(
                differences,
                section,
                f"{path}[{index}]",
                _MISSING,
                value,
            )
        return

    if after is _MISSING and isinstance(before, list) and before:
        for index, value in enumerate(before):
            _compare_nested(
                differences,
                section,
                f"{path}[{index}]",
                value,
                _MISSING,
            )
        return

    _compare_field(differences, section, path, before, after)


def _compare_field(
    differences: list[SnapshotDifference],
    section: DifferenceSection,
    path: str,
    before: object,
    after: object,
) -> None:
    if before == after:
        return
    if before is _MISSING:
        kind = DifferenceKind.ADDED
        before_value = None
        after_value = after
    elif after is _MISSING:
        kind = DifferenceKind.REMOVED
        before_value = before
        after_value = None
    else:
        kind = DifferenceKind.CHANGED
        before_value = before
        after_value = after
    differences.append(
        SnapshotDifference(
            section=section,
            path=path,
            kind=kind,
            before=before_value,
            after=after_value,
        )
    )


def _nested_path(parent: str, key: str) -> str:
    if key.isidentifier():
        return f"{parent}.{key}"
    encoded_key = json.dumps(key, ensure_ascii=False)
    return f"{parent}[{encoded_key}]"
