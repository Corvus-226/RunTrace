"""Tests for deterministic experiment snapshot differences."""

from __future__ import annotations

import os
import subprocess
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest
from typer.testing import CliRunner

from runtrace.cli import app
from runtrace.diff import DifferenceKind, DifferenceSection, compare_snapshots
from runtrace.models import (
    EnvironmentSnapshot,
    ExperimentSnapshot,
    GitSnapshot,
    PlatformSnapshot,
    RuntimeSnapshot,
    Snapshot,
)
from runtrace.storage import SnapshotStore

runner = CliRunner()


def test_nested_config_diff_has_stable_paths_and_change_kinds() -> None:
    before = _snapshot(
        "100000000001",
        config={
            "batch_size": 8,
            "model.name": "small",
            "optimizer": {
                "learning_rate": 0.001,
                "weight_decay": 0.01,
            },
            "remove_me": True,
        },
        config_hash="a" * 64,
    )
    after = _snapshot(
        "200000000002",
        config={
            "added": "value",
            "batch_size": 16,
            "model.name": "large",
            "optimizer": {
                "learning_rate": 0.0005,
                "momentum": 0.9,
            },
        },
        config_hash="b" * 64,
    )

    comparison = compare_snapshots(before, after)
    config_changes = [
        difference
        for difference in comparison.differences
        if difference.section is DifferenceSection.CONFIGURATION
    ]

    assert [(change.path, change.kind) for change in config_changes] == [
        ("config.sha256", DifferenceKind.CHANGED),
        ("config.values.added", DifferenceKind.ADDED),
        ("config.values.batch_size", DifferenceKind.CHANGED),
        ('config.values["model.name"]', DifferenceKind.CHANGED),
        ("config.values.optimizer.learning_rate", DifferenceKind.CHANGED),
        ("config.values.optimizer.momentum", DifferenceKind.ADDED),
        ("config.values.optimizer.weight_decay", DifferenceKind.REMOVED),
        ("config.values.remove_me", DifferenceKind.REMOVED),
    ]
    assert config_changes[1].before is None
    assert config_changes[1].after == "value"
    assert config_changes[-1].before is True
    assert config_changes[-1].after is None


def test_config_command_path_and_explicit_null_are_compared() -> None:
    before = _snapshot(
        "100000000001",
        command=None,
        config=None,
        config_path=None,
        config_hash=None,
    )
    after = _snapshot(
        "200000000002",
        command="python train.py",
        config=None,
        config_path="configs/null.yaml",
        config_hash="f" * 64,
    )

    changes = compare_snapshots(before, after).differences

    assert [(change.path, change.kind) for change in changes] == [
        ("command", DifferenceKind.CHANGED),
        ("config.path", DifferenceKind.CHANGED),
        ("config.sha256", DifferenceKind.CHANGED),
        ("config.values", DifferenceKind.ADDED),
    ]
    assert changes[-1].after is None


def test_nested_config_lists_use_stable_index_paths() -> None:
    before = _snapshot(
        "100000000001",
        config={
            "layers": [{"width": 128}, "dropout"],
            "remove": ["old"],
        },
    )
    after = _snapshot(
        "200000000002",
        config={
            "layers": [{"width": 256}, "dropout", {"width": 64}],
            "new": ["value"],
        },
    )

    changes = [
        change
        for change in compare_snapshots(before, after).differences
        if change.path.startswith("config.values")
    ]

    assert [(change.path, change.kind) for change in changes] == [
        ("config.values.layers[0].width", DifferenceKind.CHANGED),
        ("config.values.layers[2].width", DifferenceKind.ADDED),
        ("config.values.new[0]", DifferenceKind.ADDED),
        ("config.values.remove[0]", DifferenceKind.REMOVED),
    ]


def test_git_and_runtime_changes_are_grouped_deterministically() -> None:
    before = _snapshot(
        "100000000001",
        commit="1" * 40,
        branch="main",
        detached=False,
        dirty=False,
        python="3.10.0",
        implementation="CPython",
        system="Linux",
        release="6.8",
        architecture="64bit",
        machine="x86_64",
    )
    after = _snapshot(
        "200000000002",
        commit="2" * 40,
        branch=None,
        detached=True,
        dirty=True,
        python="3.12.7",
        implementation="PyPy",
        system="Windows",
        release="11",
        architecture="ARM64",
        machine="arm64",
    )

    changes = compare_snapshots(before, after).differences

    assert [
        change.path for change in changes if change.section is DifferenceSection.GIT
    ] == [
        "commit",
        "branch",
        "detached",
        "dirty",
    ]
    assert [
        change.path for change in changes if change.section is DifferenceSection.RUNTIME
    ] == [
        "python",
        "implementation",
        "platform.system",
        "platform.release",
        "platform.architecture",
        "platform.machine",
    ]


def test_dependency_add_remove_and_change_are_distinguished() -> None:
    before = _snapshot(
        "100000000001",
        packages={"changed": "1.0", "removed": "2.0", "same": "3.0"},
    )
    after = _snapshot(
        "200000000002",
        packages={"added": "4.0", "changed": "1.1", "same": "3.0"},
    )

    changes = [
        change
        for change in compare_snapshots(before, after).differences
        if change.section is DifferenceSection.ENVIRONMENT
    ]

    assert [(change.path, change.kind) for change in changes] == [
        ("added", DifferenceKind.ADDED),
        ("changed", DifferenceKind.CHANGED),
        ("removed", DifferenceKind.REMOVED),
    ]
    assert (changes[0].before, changes[0].after) == (None, "4.0")
    assert (changes[2].before, changes[2].after) == ("2.0", None)


def test_identical_relevant_values_ignore_run_identity_and_name() -> None:
    before = _snapshot("100000000001", name="first")
    after = _snapshot("200000000002", name="second").model_copy(
        update={"timestamp": before.timestamp + timedelta(hours=1)}
    )

    comparison = compare_snapshots(before, after)

    assert comparison.before_run_id == before.run_id
    assert comparison.after_run_id == after.run_id
    assert comparison.differences == ()


def test_cli_supports_full_and_unique_abbreviated_ids(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repository = _initialized_repository(tmp_path, monkeypatch)
    before = _snapshot(
        "a31f82000001",
        commit="1" * 40,
        packages={"torch": "2.4.0", "removed": "1.0"},
        config={"optimizer": {"learning_rate": 0.001}},
        config_hash="a" * 64,
    )
    after = _snapshot(
        "b91de3000002",
        commit="2" * 40,
        dirty=True,
        python="3.12.8",
        packages={"torch": "2.5.0", "added": "1.0"},
        config={"optimizer": {"learning_rate": 0.0005}},
        config_hash="b" * 64,
    )
    store = SnapshotStore(repository)
    store.save(before)
    store.save(after)

    result = runner.invoke(app, ["diff", before.run_id, "B91DE3"])

    assert result.exit_code == 0
    assert f"Comparing {before.run_id} -> {after.run_id}" in result.stdout
    for section in ("Configuration", "Git", "Runtime", "Environment"):
        assert section in result.stdout
    for kind in ("added", "removed", "changed"):
        assert kind in result.stdout
    assert "config.values.optimizer.learning_rate" in "".join(result.stdout.split())
    assert "torch" in result.stdout
    assert "2.4.0" in result.stdout
    assert "2.5.0" in result.stdout


def test_cli_identical_runs_report_no_relevant_differences(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repository = _initialized_repository(tmp_path, monkeypatch)
    snapshot = _snapshot("a31f82000001")
    SnapshotStore(repository).save(snapshot)

    result = runner.invoke(app, ["diff", snapshot.run_id, snapshot.run_id])

    assert result.exit_code == 0
    assert "No relevant differences found." in result.stdout


def test_cli_missing_and_ambiguous_ids_are_actionable(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repository = _initialized_repository(tmp_path, monkeypatch)
    store = SnapshotStore(repository)
    store.save(_snapshot("abc000000001"))
    store.save(_snapshot("abc000000002"))

    missing = runner.invoke(app, ["diff", "fff", "abc000000001"])
    ambiguous = runner.invoke(app, ["diff", "abc", "abc000000001"])

    assert missing.exit_code == 1
    assert "No snapshot matches run ID fff" in missing.output
    assert ambiguous.exit_code == 1
    assert "Run ID abc is ambiguous" in ambiguous.output
    assert "Traceback" not in missing.output + ambiguous.output


def test_cli_corrupt_snapshot_is_actionable(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repository = _initialized_repository(tmp_path, monkeypatch)
    corrupt = repository / ".runtrace" / "runs" / "a31f82000001.yaml"
    corrupt.write_text("git: [unterminated\n", encoding="utf-8")

    result = runner.invoke(app, ["diff", "a31f82000001", "a31f82000001"])

    assert result.exit_code == 1
    assert "a31f82000001.yaml contains invalid YAML" in result.output
    assert "repair or remove it" in result.output
    assert "Traceback" not in result.output


def test_cli_requires_initialized_project(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repository = _git_repository(tmp_path / "repository")
    monkeypatch.chdir(repository)

    result = runner.invoke(app, ["diff", "a31f82", "b91de3"])

    assert result.exit_code == 1
    assert "Run `runtrace init` first" in result.output
    assert "Traceback" not in result.output


def test_cli_renders_stored_values_literally(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repository = _initialized_repository(tmp_path, monkeypatch)
    before = _snapshot("a31f82000001", command="[red]before[/red]")
    after = _snapshot("b91de3000002", command="[green]after[/green]")
    store = SnapshotStore(repository)
    store.save(before)
    store.save(after)

    result = runner.invoke(app, ["diff", "a31f82", "b91de3"])

    assert result.exit_code == 0
    assert "[red]before[/red]" in result.stdout
    assert "[green]after[/green]" in result.stdout


def _initialized_repository(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> Path:
    repository = _git_repository(tmp_path / "repository")
    monkeypatch.chdir(repository)
    result = runner.invoke(app, ["init"])
    assert result.exit_code == 0
    return repository


def _git_repository(repository: Path) -> Path:
    repository.mkdir()
    environment = os.environ.copy()
    environment["GIT_CONFIG_GLOBAL"] = os.devnull
    environment["GIT_CONFIG_NOSYSTEM"] = "1"
    subprocess.run(
        ["git", "-C", str(repository), "init", "--quiet", "--initial-branch=main"],
        check=True,
        capture_output=True,
        text=True,
        env=environment,
    )
    return repository


def _snapshot(
    run_id: str,
    *,
    name: str | None = None,
    commit: str = "1" * 40,
    branch: str | None = "main",
    detached: bool = False,
    dirty: bool = False,
    python: str = "3.12.7",
    implementation: str = "CPython",
    system: str = "TestOS",
    release: str = "2026.1",
    architecture: str = "64bit",
    machine: str = "test64",
    packages: dict[str, str] | None = None,
    command: str | None = "python train.py",
    config: object = None,
    config_path: str | None = "configs/train.yaml",
    config_hash: str | None = "f" * 64,
) -> Snapshot:
    return Snapshot(
        run_id=run_id,
        name=name,
        timestamp=datetime(2026, 8, 13, 6, 31, tzinfo=timezone.utc),
        git=GitSnapshot(
            commit=commit,
            branch=branch,
            detached=detached,
            dirty=dirty,
        ),
        runtime=RuntimeSnapshot(
            python=python,
            implementation=implementation,
            platform=PlatformSnapshot(
                system=system,
                release=release,
                architecture=architecture,
                machine=machine,
            ),
        ),
        environment=EnvironmentSnapshot(packages=packages or {}),
        experiment=ExperimentSnapshot(
            command=command,
            config_path=config_path,
            config_hash=config_hash,
            config=config,
        ),
    )
