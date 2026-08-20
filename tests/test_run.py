"""End-to-end tests for snapshot-before-execution experiment runs."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest
from typer.testing import CliRunner

import ml_runtrace.snapshot as snapshot_module
from ml_runtrace.cli import app
from ml_runtrace.environment import (
    EnvironmentMetadata,
    PlatformMetadata,
    PythonRuntimeMetadata,
    VcsPackageSourceMetadata,
)
from ml_runtrace.execution import (
    RUN_ID_ENVIRONMENT_VARIABLE,
    build_experiment_environment,
)
from ml_runtrace.storage import SnapshotStore

runner = CliRunner()


def test_run_creates_snapshot_before_preserving_exact_arguments(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repository = _initialized_repository(tmp_path, monkeypatch)
    _use_environment(monkeypatch)
    marker = repository / "experiment-finished.txt"
    script = (
        "from pathlib import Path; import sys; "
        "runs=list(Path('.runtrace/runs').glob('*.yaml')); "
        "sys.exit(23) if len(runs) != 1 else "
        "Path(sys.argv[1]).write_text(sys.argv[2], encoding='utf-8')"
    )
    arguments = (
        sys.executable,
        "-c",
        script,
        str(marker),
        "value with spaces",
    )

    result = runner.invoke(
        app,
        ["run", "--name", "automatic baseline", "--", *arguments],
    )

    assert result.exit_code == 0, result.output
    assert marker.read_text(encoding="utf-8") == "value with spaces"
    snapshots = SnapshotStore(repository).list_snapshots()
    assert len(snapshots) == 1
    snapshot = snapshots[0]
    assert snapshot.name == "automatic baseline"
    assert snapshot.experiment.command_argv == arguments
    assert snapshot.experiment.command is not None
    assert sys.executable in snapshot.experiment.command
    assert snapshot.environment.package_sources["research-package"].kind == "vcs"
    assert "Created snapshot" in result.output
    assert "Experiment command completed successfully." in result.output


def test_run_exposes_saved_run_id_to_child_and_replaces_stale_value(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repository = _initialized_repository(tmp_path, monkeypatch)
    _use_environment(monkeypatch)
    stale_run_id = "000000000000"
    monkeypatch.setenv(RUN_ID_ENVIRONMENT_VARIABLE, stale_run_id)
    marker = repository / "observed-run-id.txt"
    script = (
        "from pathlib import Path; import os, sys; "
        f"run_id=os.environ[{RUN_ID_ENVIRONMENT_VARIABLE!r}]; "
        "snapshot=Path('.runtrace/runs') / f'{run_id}.yaml'; "
        "sys.exit(24) if not snapshot.is_file() else "
        "Path(sys.argv[1]).write_text(run_id, encoding='utf-8')"
    )

    result = runner.invoke(
        app,
        ["run", "--", sys.executable, "-c", script, str(marker)],
    )

    assert result.exit_code == 0, result.output
    observed_run_id = marker.read_text(encoding="utf-8")
    snapshot = SnapshotStore(repository).load(observed_run_id)
    assert observed_run_id == snapshot.run_id
    assert observed_run_id != stale_run_id
    assert os.environ[RUN_ID_ENVIRONMENT_VARIABLE] == stale_run_id
    assert (
        f"Child environment: {RUN_ID_ENVIRONMENT_VARIABLE}={observed_run_id}"
        in result.output
    )


def test_build_experiment_environment_does_not_mutate_inherited_values() -> None:
    inherited = {
        "EXISTING_SETTING": "preserved",
        RUN_ID_ENVIRONMENT_VARIABLE: "111111111111",
    }

    child_environment = build_experiment_environment(
        inherited,
        run_id="222222222222",
    )

    assert child_environment == {
        "EXISTING_SETTING": "preserved",
        RUN_ID_ENVIRONMENT_VARIABLE: "222222222222",
    }
    assert inherited[RUN_ID_ENVIRONMENT_VARIABLE] == "111111111111"


def test_run_does_not_start_command_when_snapshot_capture_fails(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repository = _initialized_repository(tmp_path, monkeypatch)
    marker = repository / "must-not-exist.txt"
    script = "from pathlib import Path; import sys; Path(sys.argv[1]).touch()"

    result = runner.invoke(
        app,
        [
            "run",
            "--config",
            "missing.yaml",
            "--",
            sys.executable,
            "-c",
            script,
            str(marker),
        ],
    )

    assert result.exit_code == 1
    assert "Config file does not exist" in result.output
    assert not marker.exists()
    assert SnapshotStore(repository).list_snapshots() == []


def test_run_keeps_snapshot_and_propagates_failed_command_exit_code(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repository = _initialized_repository(tmp_path, monkeypatch)
    _use_environment(monkeypatch)

    result = runner.invoke(
        app,
        ["run", "--", sys.executable, "-c", "raise SystemExit(7)"],
    )

    assert result.exit_code == 7
    assert "Experiment command exited with code 7." in result.output
    assert len(SnapshotStore(repository).list_snapshots()) == 1


def test_run_keeps_snapshot_when_executable_cannot_start(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    repository = _initialized_repository(tmp_path, monkeypatch)
    _use_environment(monkeypatch)

    result = runner.invoke(
        app,
        ["run", "--", "runtrace-command-that-does-not-exist-4f7f09"],
    )

    assert result.exit_code == 127
    assert "Could not start experiment command" in result.output
    assert len(SnapshotStore(repository).list_snapshots()) == 1


def _initialized_repository(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> Path:
    repository = tmp_path / "repository"
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
    (repository / "train.py").write_text("print('ready')\n", encoding="utf-8")
    monkeypatch.chdir(repository)
    initialized = runner.invoke(app, ["init"])
    assert initialized.exit_code == 0
    _git(repository, "add", "runtrace.toml", "train.py")
    _git(
        repository,
        "-c",
        "user.name=RunTrace Tests",
        "-c",
        "user.email=runtrace-tests@example.invalid",
        "commit",
        "--quiet",
        "-m",
        "initialize test project",
    )
    return repository


def _git(repository: Path, *arguments: str) -> None:
    environment = os.environ.copy()
    environment["GIT_CONFIG_GLOBAL"] = os.devnull
    environment["GIT_CONFIG_NOSYSTEM"] = "1"
    subprocess.run(
        ["git", "-C", str(repository), *arguments],
        check=True,
        capture_output=True,
        text=True,
        env=environment,
    )


def _use_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    metadata = EnvironmentMetadata(
        runtime=PythonRuntimeMetadata(version="3.12.7", implementation="CPython"),
        platform=PlatformMetadata(
            system="TestOS",
            release="2026.1",
            architecture="64bit",
            machine="test64",
        ),
        packages={"research-package": "1.0"},
        package_sources={
            "research-package": VcsPackageSourceMetadata(
                url="https://github.com/example/research-package.git",
                vcs="git",
                commit_id="a" * 40,
                requested_revision="main",
            )
        },
        gpu=None,
    )
    monkeypatch.setattr(
        snapshot_module,
        "collect_environment_metadata",
        lambda: metadata,
    )
