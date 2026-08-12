"""CLI tests for compact local snapshot listings."""

from __future__ import annotations

import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path

import pytest
from typer.testing import CliRunner

from runtrace.cli import app
from runtrace.models import (
    EnvironmentSnapshot,
    GitSnapshot,
    PlatformSnapshot,
    RuntimeSnapshot,
    Snapshot,
)
from runtrace.storage import SnapshotStore

runner = CliRunner()


def test_empty_storage_prints_friendly_message(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _initialized_repository(tmp_path, monkeypatch)

    result = runner.invoke(app, ["list"])

    assert result.exit_code == 0
    assert "No snapshots recorded yet" in result.stdout
    assert "runtrace snapshot" in result.stdout


def test_single_run_displays_clear_optional_values(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repository = _initialized_repository(tmp_path, monkeypatch)
    SnapshotStore(repository).save(
        _snapshot(
            "a31f82000001",
            name=None,
            commit="83ab2c1" + "0" * 33,
            dirty=False,
            timestamp=datetime(2026, 8, 13, 6, 31, tzinfo=timezone.utc),
        )
    )

    result = runner.invoke(app, ["list"])

    assert result.exit_code == 0
    assert "RUN ID" in result.stdout
    assert "NAME" in result.stdout
    assert "COMMIT" in result.stdout
    assert "DIRTY" in result.stdout
    assert "CREATED" in result.stdout
    assert "a31f82000001" in result.stdout
    assert "—" in result.stdout
    assert "83ab2c1" in result.stdout
    assert "no" in result.stdout
    assert "2026-08-13 06:31 UTC" in result.stdout


def test_multiple_runs_are_newest_first_and_names_are_literal(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repository = _initialized_repository(tmp_path, monkeypatch)
    store = SnapshotStore(repository)
    store.save(
        _snapshot(
            "100000000001",
            name="older",
            commit="1111111" + "0" * 33,
            dirty=False,
            timestamp=datetime(2026, 8, 13, 1, tzinfo=timezone.utc),
        )
    )
    store.save(
        _snapshot(
            "300000000003",
            name="[bold]newest[/bold]\nrun",
            commit="3333333" + "0" * 33,
            dirty=True,
            timestamp=datetime(2026, 8, 13, 3, tzinfo=timezone.utc),
        )
    )
    store.save(
        _snapshot(
            "200000000002",
            name="middle",
            commit="2222222" + "0" * 33,
            dirty=False,
            timestamp=datetime(2026, 8, 13, 2, tzinfo=timezone.utc),
        )
    )

    result = runner.invoke(app, ["list"])

    assert result.exit_code == 0
    assert result.stdout.index("300000000003") < result.stdout.index("200000000002")
    assert result.stdout.index("200000000002") < result.stdout.index("100000000001")
    assert "[bold]newest[/bold] run" in result.stdout
    assert "3333333" in result.stdout
    assert "yes" in result.stdout


def test_corrupt_snapshot_produces_actionable_error_without_traceback(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repository = _initialized_repository(tmp_path, monkeypatch)
    corrupt = repository / ".runtrace" / "runs" / "a31f82000001.yaml"
    corrupt.write_text("git: [unterminated\n", encoding="utf-8")

    result = runner.invoke(app, ["list"])

    assert result.exit_code == 1
    assert "a31f82000001.yaml contains invalid YAML" in result.output
    assert "repair or remove it" in result.output
    assert "Traceback" not in result.output


def test_list_requires_initialized_project(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repository = _git_repository(tmp_path / "repository")
    monkeypatch.chdir(repository)

    result = runner.invoke(app, ["list"])

    assert result.exit_code == 1
    assert "Run `runtrace init` first" in result.output


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
    name: str | None,
    commit: str,
    dirty: bool,
    timestamp: datetime,
) -> Snapshot:
    return Snapshot(
        run_id=run_id,
        name=name,
        timestamp=timestamp,
        git=GitSnapshot(
            commit=commit,
            branch="main",
            detached=False,
            dirty=dirty,
        ),
        runtime=RuntimeSnapshot(
            python="3.12.7",
            implementation="CPython",
            platform=PlatformSnapshot(
                system="TestOS",
                release="2026.1",
                architecture="64bit",
                machine="test64",
            ),
        ),
        environment=EnvironmentSnapshot(packages={"example": "1.0"}),
    )
