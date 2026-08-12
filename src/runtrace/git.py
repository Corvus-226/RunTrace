"""Capture the local Git state associated with an experiment."""

from __future__ import annotations

import os
import subprocess
from dataclasses import dataclass
from pathlib import Path

_GIT_TIMEOUT_SECONDS = 10


class GitMetadataError(RuntimeError):
    """Raised when Git metadata cannot be collected safely."""


@dataclass(frozen=True, slots=True)
class GitMetadata:
    """The minimal Git state needed to identify experiment code."""

    commit: str
    branch: str | None
    detached: bool
    dirty: bool


def find_git_root(path: Path) -> Path:
    """Return the work-tree root containing ``path``, including empty repos."""
    repository = Path(path).expanduser()
    if not repository.exists():
        raise GitMetadataError(f"Git repository path does not exist: {repository}")
    if not repository.is_dir():
        raise GitMetadataError(f"Git repository path is not a directory: {repository}")

    root_result = _run_git(repository, "rev-parse", "--show-toplevel")
    root_text = root_result.stdout.strip()
    if root_result.returncode != 0 or not root_text:
        raise GitMetadataError(
            f"Not a Git repository: {repository}. "
            "Run this command inside an initialized Git working tree."
        )

    root = Path(root_text)
    try:
        resolved_root = root.resolve(strict=True)
    except OSError as error:
        raise GitMetadataError(
            f"Could not resolve the Git repository root {root}: {error}"
        ) from error
    if not resolved_root.is_dir():
        raise GitMetadataError(
            f"Git repository root is not a directory: {resolved_root}"
        )
    return resolved_root


def collect_git_metadata(path: Path) -> GitMetadata:
    """Collect commit, branch, detached-HEAD, and dirty-tree information.

    The implementation invokes the Git CLI without a shell. It deliberately
    does not inspect remotes, patches, source contents, or Git credentials.
    """
    repository = Path(path).expanduser()
    if not repository.exists():
        raise GitMetadataError(f"Git repository path does not exist: {repository}")
    if not repository.is_dir():
        raise GitMetadataError(f"Git repository path is not a directory: {repository}")

    work_tree = _run_git(repository, "rev-parse", "--is-inside-work-tree")
    if work_tree.returncode != 0 or work_tree.stdout.strip() != "true":
        raise GitMetadataError(
            f"Not a Git repository: {repository}. "
            "Run this command inside an initialized Git working tree."
        )

    commit_result = _run_git(repository, "rev-parse", "--verify", "HEAD")
    commit = commit_result.stdout.strip()
    if commit_result.returncode != 0 or not commit:
        raise GitMetadataError(
            f"Could not read the current Git commit in {repository}. "
            "Ensure the repository has at least one commit."
        )

    branch_result = _run_git(
        repository,
        "symbolic-ref",
        "--quiet",
        "--short",
        "HEAD",
    )
    if branch_result.returncode == 0:
        branch = branch_result.stdout.strip()
        if not branch:
            raise GitMetadataError(
                f"Could not determine the current Git branch in {repository}."
            )
        detached = False
    elif branch_result.returncode == 1:
        branch = None
        detached = True
    else:
        raise GitMetadataError(
            f"Could not determine the current Git branch in {repository}."
        )

    status_result = _run_git(
        repository,
        "status",
        "--porcelain=v1",
        "--untracked-files=normal",
    )
    if status_result.returncode != 0:
        raise GitMetadataError(
            f"Could not inspect the Git working-tree status in {repository}."
        )

    return GitMetadata(
        commit=commit,
        branch=branch,
        detached=detached,
        dirty=bool(status_result.stdout),
    )


def _run_git(repository: Path, *arguments: str) -> subprocess.CompletedProcess[str]:
    environment = os.environ.copy()
    environment["GIT_OPTIONAL_LOCKS"] = "0"
    environment["GIT_TERMINAL_PROMPT"] = "0"

    try:
        return subprocess.run(
            ["git", "-C", str(repository), *arguments],
            check=False,
            capture_output=True,
            encoding="utf-8",
            errors="replace",
            env=environment,
            stdin=subprocess.DEVNULL,
            timeout=_GIT_TIMEOUT_SECONDS,
        )
    except FileNotFoundError as error:
        raise GitMetadataError(
            "Git executable was not found. Install Git and ensure it is available "
            "on PATH."
        ) from error
    except subprocess.TimeoutExpired as error:
        raise GitMetadataError(
            f"Git timed out while inspecting the repository at {repository}."
        ) from error
    except OSError as error:
        raise GitMetadataError(
            f"Git could not inspect the repository at {repository}: {error}"
        ) from error
