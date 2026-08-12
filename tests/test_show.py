"""CLI tests for displaying complete stored snapshots."""

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
    ExperimentSnapshot,
    GitSnapshot,
    GpuSnapshot,
    HardwareSnapshot,
    PlatformSnapshot,
    RuntimeSnapshot,
    Snapshot,
)
from runtrace.storage import SnapshotStore

runner = CliRunner()


def test_full_id_displays_every_captured_section(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repository = _initialized_repository(tmp_path, monkeypatch)
    expected = _full_snapshot()
    SnapshotStore(repository).save(expected)

    result = runner.invoke(app, ["show", expected.run_id])

    assert result.exit_code == 0
    for heading in (
        "Overview",
        "Git",
        "Runtime",
        "Environment",
        "Hardware",
        "Experiment",
    ):
        assert heading in result.stdout
    for value in (
        expected.run_id,
        "baseline",
        "2026-08-13T06:31:00Z",
        "83ab2c1" + "0" * 33,
        "main",
        "3.12.7",
        "CPython",
        "TestOS",
        "2026.1",
        "64bit",
        "test64",
        "alpha-package",
        "1.0",
        "NVIDIA Test",
        "555.42",
        "12.5",
        "python train.py --config configs/train.yaml",
        "configs/train.yaml",
        '"batch_size": 32',
        '"name": "adamw"',
    ):
        assert value in result.stdout
    assert "f" * 64 in "".join(result.stdout.split())


def test_unique_abbreviated_id_loads_snapshot(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repository = _initialized_repository(tmp_path, monkeypatch)
    expected = _full_snapshot()
    SnapshotStore(repository).save(expected)

    result = runner.invoke(app, ["show", "A31F82"])

    assert result.exit_code == 0
    assert expected.run_id in result.stdout
    assert "baseline" in result.stdout


def test_missing_optional_fields_are_clear_and_no_values_are_invented(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repository = _initialized_repository(tmp_path, monkeypatch)
    snapshot = _minimal_snapshot("b91de3000002")
    SnapshotStore(repository).save(snapshot)

    result = runner.invoke(app, ["show", snapshot.run_id])

    assert result.exit_code == 0
    assert "Branch" in result.stdout
    assert "No packages recorded." in result.stdout
    assert "Config values  —" in result.stdout
    assert result.stdout.count("—") >= 7
    assert "NVIDIA" not in result.stdout
    assert "CUDA Version" not in result.stdout


def test_unknown_id_is_actionable(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _initialized_repository(tmp_path, monkeypatch)

    result = runner.invoke(app, ["show", "abcdef"])

    assert result.exit_code == 1
    assert "No snapshot matches run ID abcdef" in result.output
    assert "Traceback" not in result.output


def test_ambiguous_abbreviated_id_is_actionable(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repository = _initialized_repository(tmp_path, monkeypatch)
    store = SnapshotStore(repository)
    store.save(_minimal_snapshot("abc000000001"))
    store.save(_minimal_snapshot("abc000000002"))

    result = runner.invoke(app, ["show", "abc"])

    assert result.exit_code == 1
    assert "Run ID abc is ambiguous" in result.output
    assert "abc000000001, abc000000002" in result.output
    assert "Traceback" not in result.output


def test_stored_markup_like_text_is_rendered_literally(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repository = _initialized_repository(tmp_path, monkeypatch)
    snapshot = _full_snapshot().model_copy(
        update={
            "name": "[bold]literal[/bold]",
            "experiment": ExperimentSnapshot(
                command="python train.py --label '[red]literal[/red]'",
            ),
        }
    )
    SnapshotStore(repository).save(snapshot)

    result = runner.invoke(app, ["show", snapshot.run_id])

    assert result.exit_code == 0
    assert "[bold]literal[/bold]" in result.stdout
    assert "[red]literal[/red]" in result.stdout


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
    monkeypatch.chdir(repository)
    result = runner.invoke(app, ["init"])
    assert result.exit_code == 0
    return repository


def _full_snapshot() -> Snapshot:
    return Snapshot(
        run_id="a31f82000001",
        name="baseline",
        timestamp=datetime(2026, 8, 13, 6, 31, tzinfo=timezone.utc),
        git=GitSnapshot(
            commit="83ab2c1" + "0" * 33,
            branch="main",
            detached=False,
            dirty=False,
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
        environment=EnvironmentSnapshot(
            packages={"zeta-package": "2.0", "alpha-package": "1.0"}
        ),
        hardware=HardwareSnapshot(
            gpu=GpuSnapshot(
                devices=("NVIDIA Test",),
                driver_versions=("555.42",),
                cuda_version="12.5",
            )
        ),
        experiment=ExperimentSnapshot(
            command="python train.py --config configs/train.yaml",
            config_path="configs/train.yaml",
            config_hash="f" * 64,
            config={"batch_size": 32, "optimizer": {"name": "adamw"}},
        ),
    )


def _minimal_snapshot(run_id: str) -> Snapshot:
    return Snapshot(
        run_id=run_id,
        timestamp=datetime(2026, 8, 13, 6, 31, tzinfo=timezone.utc),
        git=GitSnapshot(
            commit="0" * 40,
            branch=None,
            detached=True,
            dirty=False,
        ),
        runtime=RuntimeSnapshot(
            python="3.10.0",
            implementation="CPython",
            platform=PlatformSnapshot(
                system="TestOS",
                release="",
                architecture="",
                machine="",
            ),
        ),
        environment=EnvironmentSnapshot(packages={}),
    )
