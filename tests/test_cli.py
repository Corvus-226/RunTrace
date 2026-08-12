"""Tests for the RunTrace command-line interface."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

import pytest
from typer.testing import CliRunner

from runtrace import __version__
from runtrace.cli import app

runner = CliRunner()


def test_help_describes_runtrace() -> None:
    result = runner.invoke(app, ["--help"])

    assert result.exit_code == 0
    assert "Capture and compare" in result.stdout
    assert "init" in result.stdout
    assert "list" in result.stdout
    assert "snapshot" in result.stdout


def test_version_reports_package_version() -> None:
    result = runner.invoke(app, ["--version"])

    assert result.exit_code == 0
    assert result.stdout.strip() == f"runtrace {__version__}"


def test_init_creates_project_files_in_git_root(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repository = _git_repository(tmp_path / "repository")
    nested = repository / "experiments" / "baseline"
    nested.mkdir(parents=True)
    monkeypatch.chdir(nested)

    result = runner.invoke(app, ["init"])

    assert result.exit_code == 0
    assert "Initialized RunTrace in current repository." in result.stdout
    assert f"Project: {repository.resolve()}" in result.stdout
    assert (repository / ".runtrace" / "runs").is_dir()
    assert (repository / "runtrace.toml").read_text(encoding="utf-8") == (
        "# RunTrace project configuration.\n[runtrace]\nschema_version = 1\n"
    )
    assert not (nested / ".runtrace").exists()


def test_repeated_init_preserves_configuration_and_runs(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repository = _git_repository(tmp_path / "repository")
    monkeypatch.chdir(repository)
    first_result = runner.invoke(app, ["init"])
    assert first_result.exit_code == 0

    configuration = repository / "runtrace.toml"
    custom_configuration = "[runtrace]\nschema_version = 1\nname = 'custom'\n"
    configuration.write_text(custom_configuration, encoding="utf-8")
    stored_run = repository / ".runtrace" / "runs" / "existing.yaml"
    stored_run.write_text("existing: true\n", encoding="utf-8")

    second_result = runner.invoke(app, ["init"])

    assert second_result.exit_code == 0
    assert configuration.read_text(encoding="utf-8") == custom_configuration
    assert stored_run.read_text(encoding="utf-8") == "existing: true\n"


def test_init_outside_git_repository_is_actionable(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    directory = tmp_path / "not-a-repository"
    directory.mkdir()
    monkeypatch.chdir(directory)
    monkeypatch.setenv("GIT_CEILING_DIRECTORIES", str(tmp_path))

    result = runner.invoke(app, ["init"])

    assert result.exit_code == 1
    assert "Error: Not a Git repository" in result.output
    assert "initialized Git working tree" in result.output
    assert not (directory / ".runtrace").exists()
    assert not (directory / "runtrace.toml").exists()


def test_init_rejects_metadata_path_that_is_a_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repository = _git_repository(tmp_path / "repository")
    (repository / ".runtrace").write_text("not a directory\n", encoding="utf-8")
    monkeypatch.chdir(repository)

    result = runner.invoke(app, ["init"])

    assert result.exit_code == 1
    assert "metadata directory is not a directory" in result.output
    assert not (repository / "runtrace.toml").exists()


def test_init_rejects_runs_symlink_that_escapes_repository(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repository = _git_repository(tmp_path / "repository")
    metadata = repository / ".runtrace"
    outside = tmp_path / "outside"
    metadata.mkdir()
    outside.mkdir()
    try:
        (metadata / "runs").symlink_to(outside, target_is_directory=True)
    except OSError:
        pytest.skip("directory symlinks are unavailable on this platform")
    monkeypatch.chdir(repository)

    result = runner.invoke(app, ["init"])

    assert result.exit_code == 1
    assert "runs directory escapes its allowed project directory" in result.output
    assert not (repository / "runtrace.toml").exists()


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
