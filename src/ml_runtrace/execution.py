"""Run opt-in experiment commands after a reproducibility snapshot."""

from __future__ import annotations

import os
import shlex
import subprocess
from collections.abc import Mapping, Sequence
from pathlib import Path

RUN_ID_ENVIRONMENT_VARIABLE = "RUNTRACE_RUN_ID"


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


def build_experiment_environment(
    inherited_environment: Mapping[str, str],
    *,
    run_id: str,
) -> dict[str, str]:
    """Return an isolated child environment carrying the current run ID."""
    environment = dict(inherited_environment)
    environment[RUN_ID_ENVIRONMENT_VARIABLE] = run_id
    return environment


def execute_command(
    arguments: Sequence[str],
    *,
    cwd: Path,
    environment: Mapping[str, str] | None = None,
) -> int:
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
            env=dict(environment) if environment is not None else None,
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
