"""Tests for local Git metadata capture."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

import pytest

import ml_runtrace.git as git_module
from ml_runtrace.git import GitMetadataError, collect_git_metadata, find_git_root


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


def _committed_repository(repository: Path) -> tuple[Path, str]:
    repository.mkdir()
    _git(repository, "init", "--quiet", "--initial-branch=main")
    (repository / "tracked.txt").write_text("initial\n", encoding="utf-8")
    _git(repository, "add", "tracked.txt")
    _git(
        repository,
        "-c",
        "user.name=RunTrace Tests",
        "-c",
        "user.email=runtrace-tests@example.invalid",
        "commit",
        "--quiet",
        "-m",
        "initial commit",
    )
    commit = _git(repository, "rev-parse", "HEAD").stdout.strip()
    return repository, commit


def test_finds_root_from_nested_directory_in_empty_repository(tmp_path: Path) -> None:
    repository = tmp_path / "repository"
    nested = repository / "experiments" / "baseline"
    repository.mkdir()
    _git(repository, "init", "--quiet", "--initial-branch=main")
    nested.mkdir(parents=True)

    assert find_git_root(nested) == repository.resolve()


def test_collects_clean_branch_metadata_from_path_with_spaces(tmp_path: Path) -> None:
    repository, commit = _committed_repository(tmp_path / "repository with spaces")

    metadata = collect_git_metadata(repository)

    assert metadata.commit == commit
    assert metadata.branch == "main"
    assert metadata.detached is False
    assert metadata.dirty is False


def test_tracked_change_marks_repository_dirty(tmp_path: Path) -> None:
    repository, _ = _committed_repository(tmp_path / "repository")
    (repository / "tracked.txt").write_text("changed\n", encoding="utf-8")

    metadata = collect_git_metadata(repository)

    assert metadata.dirty is True


def test_untracked_file_marks_repository_dirty(tmp_path: Path) -> None:
    repository, _ = _committed_repository(tmp_path / "repository")
    (repository / "untracked.txt").write_text("new\n", encoding="utf-8")

    metadata = collect_git_metadata(repository)

    assert metadata.dirty is True


def test_runtrace_data_can_be_excluded_without_hiding_other_changes(
    tmp_path: Path,
) -> None:
    repository, _ = _committed_repository(tmp_path / "repository")
    runs = repository / ".runtrace" / "runs"
    runs.mkdir(parents=True)
    (runs / "snapshot.yaml").write_text("run_id: test\n", encoding="utf-8")

    assert collect_git_metadata(repository).dirty is True
    assert collect_git_metadata(repository, exclude_runtrace_data=True).dirty is False

    (repository / "other.txt").write_text("still dirty\n", encoding="utf-8")

    assert collect_git_metadata(repository, exclude_runtrace_data=True).dirty is True


def test_detached_head_is_represented_explicitly(tmp_path: Path) -> None:
    repository, commit = _committed_repository(tmp_path / "repository")
    _git(repository, "checkout", "--quiet", "--detach", commit)

    metadata = collect_git_metadata(repository)

    assert metadata.commit == commit
    assert metadata.branch is None
    assert metadata.detached is True
    assert metadata.dirty is False


def test_non_repository_error_is_actionable(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    directory = tmp_path / "not-a-repository"
    directory.mkdir()
    monkeypatch.setenv("GIT_CEILING_DIRECTORIES", str(tmp_path))

    with pytest.raises(GitMetadataError, match="Not a Git repository"):
        collect_git_metadata(directory)


def test_missing_repository_path_error_is_actionable(tmp_path: Path) -> None:
    missing = tmp_path / "missing"

    with pytest.raises(GitMetadataError, match="path does not exist"):
        collect_git_metadata(missing)


def test_missing_git_executable_error_is_actionable(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def missing_git(*args: object, **kwargs: object) -> None:
        raise FileNotFoundError

    monkeypatch.setattr(git_module.subprocess, "run", missing_git)

    with pytest.raises(GitMetadataError, match="Git executable was not found"):
        collect_git_metadata(tmp_path)


def test_commit_command_failure_error_is_actionable(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    responses = iter(
        [
            subprocess.CompletedProcess([], 0, stdout="true\n", stderr=""),
            subprocess.CompletedProcess([], 128, stdout="", stderr="failure"),
        ]
    )

    def command_result(
        *args: object, **kwargs: object
    ) -> subprocess.CompletedProcess[str]:
        return next(responses)

    monkeypatch.setattr(git_module.subprocess, "run", command_result)

    with pytest.raises(GitMetadataError, match="current Git commit"):
        collect_git_metadata(tmp_path)
