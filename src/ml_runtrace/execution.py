"""Run opt-in experiment commands after a reproducibility snapshot."""

from __future__ import annotations

import os
import shlex
import subprocess
from collections.abc import Sequence
from pathlib import Path


class ExperimentExecutionError(RuntimeError):
    """Raised when an experiment command cannot be started."""


def format_command(arguments: Sequence[str]) -> str:
    """Return a readable platform-aware representation of an argument vector."""
    if not arguments or not arguments[0].strip():
        raise ExperimentExecutionError(
            "An experiment command and executable are required after `--`."
        )
    values = list(arguments)
    if os.name == "nt":
        return subprocess.list2cmdline(values)
    return shlex.join(values)


def execute_command(arguments: Sequence[str], *, cwd: Path) -> int:
    """Execute an argument vector without a shell and return its process code."""
    if not arguments or not arguments[0].strip():
        raise ExperimentExecutionError(
            "An experiment command and executable are required after `--`."
        )
    try:
        completed = subprocess.run(
            list(arguments),
            cwd=cwd,
            check=False,
            shell=False,
        )
    except (OSError, ValueError) as error:
        detail = error.strerror if isinstance(error, OSError) else str(error)
        detail = detail or str(error)
        raise ExperimentExecutionError(
            f"Could not start experiment command `{arguments[0]}`: {detail}."
        ) from error
    return completed.returncode


def normalize_exit_code(returncode: int) -> int:
    """Map platform process status values to a portable CLI exit code."""
    if 0 <= returncode <= 255:
        return returncode
    if returncode < 0:
        return min(128 + abs(returncode), 255)
    return 1
