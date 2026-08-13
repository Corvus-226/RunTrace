"""End-to-end CLI tests for experiment snapshot capture."""

from __future__ import annotations

import hashlib
import os
import re
import subprocess
from pathlib import Path

import pytest
from typer.testing import CliRunner

import ml_runtrace.snapshot as snapshot_module
from ml_runtrace.cli import app
from ml_runtrace.environment import (
    EnvironmentMetadata,
    GpuMetadata,
    PlatformMetadata,
    PythonRuntimeMetadata,
)
from ml_runtrace.storage import SnapshotStore

runner = CliRunner()
_RUN_ID_OUTPUT = re.compile(r"Created snapshot ([0-9a-f]{12})\.")


def test_minimal_snapshot_captures_clean_repository_without_gpu(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repository, commit = _initialized_repository(tmp_path, monkeypatch)
    _use_environment(monkeypatch, gpu=None)

    result = runner.invoke(app, ["snapshot"])

    assert result.exit_code == 0
    run_id = _run_id(result.stdout)
    snapshot = SnapshotStore(repository).load(run_id)
    assert snapshot.name is None
    assert snapshot.git.commit == commit
    assert snapshot.git.branch == "main"
    assert snapshot.git.detached is False
    assert snapshot.git.dirty is False
    assert snapshot.runtime.python == "3.12.7"
    assert snapshot.runtime.implementation == "CPython"
    assert snapshot.runtime.platform.system == "TestOS"
    assert snapshot.environment.packages == {
        "alpha-package": "1.0",
        "zeta-package": "2.0",
    }
    assert snapshot.hardware.gpu is None
    assert snapshot.experiment.command is None
    assert snapshot.experiment.config_path is None
    assert snapshot.experiment.config_hash is None
    assert snapshot.experiment.config is None
    assert f"Path: {repository / '.runtrace' / 'runs' / f'{run_id}.yaml'}" in (
        result.stdout
    )


def test_full_snapshot_records_config_command_name_and_gpu(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repository, _ = _initialized_repository(tmp_path, monkeypatch)
    config = repository / "configs" / "train.yaml"
    config.parent.mkdir()
    raw_config = b"batch_size: 32\noptimizer:\n  name: adamw\n"
    config.write_bytes(raw_config)
    _commit(repository, "add training config", "configs/train.yaml")
    _use_environment(
        monkeypatch,
        gpu=GpuMetadata(
            devices=("NVIDIA Test",),
            driver_versions=("555.42",),
            cuda_version="12.5",
        ),
    )

    result = runner.invoke(
        app,
        [
            "snapshot",
            "--name",
            "baseline",
            "--config",
            "configs/train.yaml",
            "--command",
            "python train.py --config configs/train.yaml",
        ],
    )

    assert result.exit_code == 0
    snapshot = SnapshotStore(repository).load(_run_id(result.stdout))
    assert snapshot.name == "baseline"
    assert snapshot.git.dirty is False
    assert snapshot.experiment.command == (
        "python train.py --config configs/train.yaml"
    )
    assert snapshot.experiment.config_path == "configs/train.yaml"
    assert snapshot.experiment.config_hash == hashlib.sha256(raw_config).hexdigest()
    assert snapshot.experiment.config == {
        "batch_size": 32,
        "optimizer": {"name": "adamw"},
    }
    assert snapshot.hardware.gpu is not None
    assert snapshot.hardware.gpu.devices == ("NVIDIA Test",)
    assert snapshot.hardware.gpu.driver_versions == ("555.42",)
    assert snapshot.hardware.gpu.cuda_version == "12.5"


def test_dirty_repository_is_recorded(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repository, _ = _initialized_repository(tmp_path, monkeypatch)
    (repository / "train.py").write_text("print('changed')\n", encoding="utf-8")
    _use_environment(monkeypatch, gpu=None)

    result = runner.invoke(app, ["snapshot"])

    assert result.exit_code == 0
    assert SnapshotStore(repository).load(_run_id(result.stdout)).git.dirty is True


def test_prior_runtrace_data_does_not_make_next_snapshot_dirty(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repository, _ = _initialized_repository(tmp_path, monkeypatch)
    _use_environment(monkeypatch, gpu=None)
    first_result = runner.invoke(app, ["snapshot"])
    assert first_result.exit_code == 0

    second_result = runner.invoke(app, ["snapshot"])

    assert second_result.exit_code == 0
    second = SnapshotStore(repository).load(_run_id(second_result.stdout))
    assert second.git.dirty is False


def test_missing_config_fails_before_snapshot_is_written(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repository, _ = _initialized_repository(tmp_path, monkeypatch)

    def unexpected_capture() -> EnvironmentMetadata:
        raise AssertionError("environment capture must not run for a missing config")

    monkeypatch.setattr(
        snapshot_module,
        "collect_environment_metadata",
        unexpected_capture,
    )

    result = runner.invoke(app, ["snapshot", "--config", "missing.yaml"])

    assert result.exit_code == 1
    assert "Config file does not exist" in result.output
    assert list((repository / ".runtrace" / "runs").glob("*.yaml")) == []


def test_unsupported_config_fails_before_snapshot_is_written(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repository, _ = _initialized_repository(tmp_path, monkeypatch)
    config = repository / "dated.yaml"
    config.write_text("published: 2026-08-12\n", encoding="utf-8")

    result = runner.invoke(app, ["snapshot", "--config", "dated.yaml"])

    assert result.exit_code == 1
    assert "JSON-compatible YAML structures" in result.output
    assert list((repository / ".runtrace" / "runs").glob("*.yaml")) == []


def test_snapshot_requires_initialized_project(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repository = _git_repository(tmp_path / "repository")
    monkeypatch.chdir(repository)

    result = runner.invoke(app, ["snapshot"])

    assert result.exit_code == 1
    assert "Run `ml-runtrace init` first" in result.output
    assert not (repository / ".runtrace").exists()


def test_snapshot_requires_a_git_commit(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repository = _git_repository(tmp_path / "repository")
    monkeypatch.chdir(repository)
    initialized = runner.invoke(app, ["init"])
    assert initialized.exit_code == 0
    _use_environment(monkeypatch, gpu=None)

    result = runner.invoke(app, ["snapshot"])

    assert result.exit_code == 1
    assert "current Git commit" in result.output
    assert "at least one commit" in result.output
    assert list((repository / ".runtrace" / "runs").glob("*.yaml")) == []


def _initialized_repository(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> tuple[Path, str]:
    repository = _git_repository(tmp_path / "repository")
    (repository / "train.py").write_text("print('initial')\n", encoding="utf-8")
    monkeypatch.chdir(repository)
    initialized = runner.invoke(app, ["init"])
    assert initialized.exit_code == 0
    _commit(repository, "initialize test project", "runtrace.toml", "train.py")
    commit = _git(repository, "rev-parse", "HEAD").stdout.strip()
    return repository, commit


def _git_repository(repository: Path) -> Path:
    repository.mkdir()
    _git(repository, "init", "--quiet", "--initial-branch=main")
    return repository


def _commit(repository: Path, message: str, *paths: str) -> None:
    _git(repository, "add", *paths)
    _git(
        repository,
        "-c",
        "user.name=RunTrace Tests",
        "-c",
        "user.email=runtrace-tests@example.invalid",
        "commit",
        "--quiet",
        "-m",
        message,
    )


def _git(repository: Path, *arguments: str) -> subprocess.CompletedProcess[str]:
    environment = os.environ.copy()
    environment["GIT_CONFIG_GLOBAL"] = os.devnull
    environment["GIT_CONFIG_NOSYSTEM"] = "1"
    return subprocess.run(
        ["git", "-C", str(repository), *arguments],
        check=True,
        capture_output=True,
        text=True,
        env=environment,
    )


def _use_environment(
    monkeypatch: pytest.MonkeyPatch,
    *,
    gpu: GpuMetadata | None,
) -> None:
    metadata = EnvironmentMetadata(
        runtime=PythonRuntimeMetadata(version="3.12.7", implementation="CPython"),
        platform=PlatformMetadata(
            system="TestOS",
            release="2026.1",
            architecture="64bit",
            machine="test64",
        ),
        packages={"zeta-package": "2.0", "alpha-package": "1.0"},
        gpu=gpu,
    )
    monkeypatch.setattr(
        snapshot_module,
        "collect_environment_metadata",
        lambda: metadata,
    )


def _run_id(output: str) -> str:
    match = _RUN_ID_OUTPUT.search(output)
    assert match is not None, output
    return match.group(1)
