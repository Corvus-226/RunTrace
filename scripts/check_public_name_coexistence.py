"""Verify that the release wheel can coexist with the public ``runtrace`` name.

The audit is deliberately network-free. It builds a minimal local wheel that
owns the ``runtrace`` import and console command, then installs that fixture and
the real RunTrace candidate in both orders. Each order also uninstalls one
distribution and verifies that the other remains intact.
"""

from __future__ import annotations

import argparse
import base64
import csv
import hashlib
import io
import os
import subprocess
import sys
import tempfile
import textwrap
import venv
import zipfile
from pathlib import Path

_CANDIDATE_DISTRIBUTION = "ml-runtrace"
_CANDIDATE_IMPORT = "ml_runtrace"
_CANDIDATE_SCRIPT = "ml-runtrace"
_FIXTURE_DISTRIBUTION = "runtrace"
_FIXTURE_IMPORT = "runtrace"
_FIXTURE_SCRIPT = "runtrace"
_FIXTURE_VERSION = "999.0"


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run the offline public-name coexistence audit."
    )
    parser.add_argument(
        "--dist-dir",
        type=Path,
        default=Path("dist"),
        help="Directory containing exactly one ml_runtrace wheel (default: dist).",
    )
    parser.add_argument(
        "--runtrace-wheel",
        type=Path,
        help=(
            "Optional real runtrace wheel to audit instead of the generated "
            "offline fixture."
        ),
    )
    arguments = parser.parse_args()

    candidate_wheel = _find_candidate_wheel(arguments.dist_dir)
    _check_candidate_archive(candidate_wheel)

    with tempfile.TemporaryDirectory(prefix="runtrace-public-name-") as temporary:
        audit_root = Path(temporary)
        fixture_wheel = (
            _validate_fixture_wheel(arguments.runtrace_wheel)
            if arguments.runtrace_wheel is not None
            else _build_fixture_wheel(audit_root)
        )

        _audit_install_order(
            audit_root / "existing-first",
            first=fixture_wheel,
            second=candidate_wheel,
            remove_distribution=_FIXTURE_DISTRIBUTION,
            remaining_distribution=_CANDIDATE_DISTRIBUTION,
            remaining_import=_CANDIDATE_IMPORT,
            remaining_script=_CANDIDATE_SCRIPT,
            removed_import=_FIXTURE_IMPORT,
            removed_script=_FIXTURE_SCRIPT,
        )
        _audit_install_order(
            audit_root / "candidate-first",
            first=candidate_wheel,
            second=fixture_wheel,
            remove_distribution=_CANDIDATE_DISTRIBUTION,
            remaining_distribution=_FIXTURE_DISTRIBUTION,
            remaining_import=_FIXTURE_IMPORT,
            remaining_script=_FIXTURE_SCRIPT,
            removed_import=_CANDIDATE_IMPORT,
            removed_script=_CANDIDATE_SCRIPT,
        )

    print(
        "Public-name coexistence audit passed: the ml-runtrace distribution "
        "(ml_runtrace import, ml-runtrace command) remains independent from "
        "the runtrace distribution (runtrace import and command)."
    )
    return 0


def _find_candidate_wheel(dist_dir: Path) -> Path:
    wheels = sorted(dist_dir.resolve().glob("ml_runtrace-*.whl"))
    if len(wheels) != 1:
        raise RuntimeError(
            f"Expected exactly one ml_runtrace wheel in {dist_dir.resolve()}, "
            f"found {len(wheels)}."
        )
    return wheels[0]


def _check_candidate_archive(candidate_wheel: Path) -> None:
    with zipfile.ZipFile(candidate_wheel) as archive:
        names = {name.casefold() for name in archive.namelist()}

    if "ml_runtrace/__init__.py" not in names:
        raise RuntimeError("Candidate wheel does not contain ml_runtrace/__init__.py.")
    forbidden = sorted(name for name in names if name.startswith("runtrace/"))
    if forbidden:
        raise RuntimeError(
            "Candidate wheel still owns the forbidden runtrace import namespace: "
            + ", ".join(forbidden)
        )


def _build_fixture_wheel(destination: Path) -> Path:
    wheel_path = destination / f"runtrace-{_FIXTURE_VERSION}-py3-none-any.whl"
    dist_info = f"runtrace-{_FIXTURE_VERSION}.dist-info"
    files = {
        "runtrace/__init__.py": (f'__version__ = "{_FIXTURE_VERSION}"\n'.encode()),
        "runtrace/cli.py": (
            b'def main():\n    print("synthetic public runtrace fixture")\n'
        ),
        f"{dist_info}/METADATA": textwrap.dedent(
            f"""\
            Metadata-Version: 2.1
            Name: {_FIXTURE_DISTRIBUTION}
            Version: {_FIXTURE_VERSION}
            Requires-Python: >=3.10

            Synthetic offline fixture for RunTrace public-name auditing.
            """
        ).encode(),
        f"{dist_info}/WHEEL": textwrap.dedent(
            """\
            Wheel-Version: 1.0
            Generator: RunTrace offline coexistence audit
            Root-Is-Purelib: true
            Tag: py3-none-any
            """
        ).encode(),
        f"{dist_info}/entry_points.txt": (
            b"[console_scripts]\nruntrace = runtrace.cli:main\n"
        ),
    }
    files[f"{dist_info}/RECORD"] = _record_contents(files, dist_info)

    with zipfile.ZipFile(wheel_path, "w", compression=zipfile.ZIP_DEFLATED) as wheel:
        for name, contents in files.items():
            wheel.writestr(name, contents)
    return wheel_path


def _validate_fixture_wheel(wheel_path: Path) -> Path:
    resolved = wheel_path.resolve()
    if not resolved.is_file() or not resolved.name.casefold().startswith("runtrace-"):
        raise RuntimeError(f"Expected a runtrace wheel, got {resolved}.")
    with zipfile.ZipFile(resolved) as archive:
        names = {name.casefold() for name in archive.namelist()}
    if "runtrace/__init__.py" not in names:
        raise RuntimeError(f"Wheel does not contain runtrace/__init__.py: {resolved}")
    return resolved


def _record_contents(files: dict[str, bytes], dist_info: str) -> bytes:
    output = io.StringIO(newline="")
    writer = csv.writer(output, lineterminator="\n")
    for name, contents in files.items():
        digest = base64.urlsafe_b64encode(hashlib.sha256(contents).digest()).rstrip(
            b"="
        )
        writer.writerow((name, f"sha256={digest.decode()}", len(contents)))
    writer.writerow((f"{dist_info}/RECORD", "", ""))
    return output.getvalue().encode()


def _audit_install_order(
    environment_root: Path,
    *,
    first: Path,
    second: Path,
    remove_distribution: str,
    remaining_distribution: str,
    remaining_import: str,
    remaining_script: str,
    removed_import: str,
    removed_script: str,
) -> None:
    venv.EnvBuilder(with_pip=True).create(environment_root)
    python = _environment_python(environment_root)
    scripts = python.parent
    pip_environment = os.environ.copy()
    pip_environment.update(
        {
            "PIP_DISABLE_PIP_VERSION_CHECK": "1",
            "PIP_NO_INDEX": "1",
            "PIP_NO_PYTHON_VERSION_WARNING": "1",
        }
    )

    for wheel in (first, second):
        _run(
            python,
            "-m",
            "pip",
            "install",
            "--no-deps",
            "--no-index",
            str(wheel),
            environment=pip_environment,
        )

    _run(python, "-c", _both_installed_check())
    _assert_script_state(scripts, _FIXTURE_SCRIPT, present=True)
    _assert_script_state(scripts, _CANDIDATE_SCRIPT, present=True)

    _run(
        python,
        "-m",
        "pip",
        "uninstall",
        "--yes",
        remove_distribution,
        environment=pip_environment,
    )
    _run(
        python,
        "-c",
        _post_uninstall_check(
            remaining_distribution=remaining_distribution,
            remaining_import=remaining_import,
            removed_distribution=remove_distribution,
            removed_import=removed_import,
        ),
    )
    _assert_script_state(scripts, remaining_script, present=True)
    _assert_script_state(scripts, removed_script, present=False)


def _environment_python(environment_root: Path) -> Path:
    if os.name == "nt":
        return environment_root / "Scripts" / "python.exe"
    return environment_root / "bin" / "python"


def _both_installed_check() -> str:
    return textwrap.dedent(
        f"""\
        import importlib.metadata as metadata
        import {_CANDIDATE_IMPORT} as candidate
        import {_FIXTURE_IMPORT} as fixture

        assert metadata.version({_CANDIDATE_DISTRIBUTION!r}) == candidate.__version__
        assert fixture.__version__ == metadata.version({_FIXTURE_DISTRIBUTION!r})

        candidate_distribution = metadata.distribution({_CANDIDATE_DISTRIBUTION!r})
        fixture_distribution = metadata.distribution({_FIXTURE_DISTRIBUTION!r})
        candidate_scripts = {{
            entry.name: entry.value
            for entry in candidate_distribution.entry_points
            if entry.group == "console_scripts"
        }}
        fixture_scripts = {{
            entry.name: entry.value
            for entry in fixture_distribution.entry_points
            if entry.group == "console_scripts"
        }}
        assert candidate_scripts == {{
            {_CANDIDATE_SCRIPT!r}: "ml_runtrace.cli:main"
        }}, candidate_scripts
        assert {_FIXTURE_SCRIPT!r} in fixture_scripts, fixture_scripts

        normalize = lambda path: str(path).replace("\\\\", "/").casefold()
        candidate_files = {{
            normalize(path)
            for path in candidate_distribution.files or ()
        }}
        fixture_files = {{
            normalize(path)
            for path in fixture_distribution.files or ()
        }}
        assert not candidate_files.intersection(fixture_files)
        assert "ml_runtrace/__init__.py" in candidate_files
        assert "runtrace/__init__.py" in fixture_files
        assert not any(path.startswith("runtrace/") for path in candidate_files)
        """
    )


def _post_uninstall_check(
    *,
    remaining_distribution: str,
    remaining_import: str,
    removed_distribution: str,
    removed_import: str,
) -> str:
    return textwrap.dedent(
        f"""\
        import importlib
        import importlib.metadata as metadata
        import importlib.util

        remaining = importlib.import_module({remaining_import!r})
        assert remaining.__version__ == metadata.version({remaining_distribution!r})
        assert importlib.util.find_spec({removed_import!r}) is None
        try:
            metadata.version({removed_distribution!r})
        except metadata.PackageNotFoundError:
            pass
        else:
            raise AssertionError(
                {removed_distribution!r} + " metadata remains installed"
            )
        """
    )


def _assert_script_state(scripts: Path, command: str, *, present: bool) -> None:
    matches = [path for path in scripts.glob(f"{command}*") if path.is_file()]
    if bool(matches) is not present:
        expectation = "exist" if present else "be absent"
        raise RuntimeError(
            f"Expected {command!r} console script to {expectation} in {scripts}; "
            f"found {[path.name for path in matches]}."
        )


def _run(
    python: Path,
    *arguments: str,
    environment: dict[str, str] | None = None,
) -> None:
    result = subprocess.run(
        [str(python), *arguments],
        check=False,
        capture_output=True,
        text=True,
        env=environment,
    )
    if result.returncode != 0:
        command = subprocess.list2cmdline([str(python), *arguments])
        raise RuntimeError(
            f"Command failed ({result.returncode}): {command}\n"
            f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
        )


if __name__ == "__main__":
    sys.exit(main())
