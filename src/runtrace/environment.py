"""Capture privacy-conscious Python runtime and platform metadata."""

from __future__ import annotations

import csv
import io
import platform
import re
import subprocess
from dataclasses import dataclass
from importlib import metadata

_DISTRIBUTION_SEPARATOR = re.compile(r"[-_.]+")
_CUDA_VERSION = re.compile(r"\bCUDA Version:\s*([0-9][0-9.]*)")
_NVIDIA_SMI_TIMEOUT_SECONDS = 5


@dataclass(frozen=True, slots=True)
class PythonRuntimeMetadata:
    """Python interpreter details relevant to reproducibility."""

    version: str
    implementation: str


@dataclass(frozen=True, slots=True)
class PlatformMetadata:
    """Local operating-system and machine details."""

    system: str
    release: str
    architecture: str
    machine: str


@dataclass(frozen=True, slots=True)
class GpuMetadata:
    """Best-effort NVIDIA GPU information."""

    devices: tuple[str, ...]
    driver_versions: tuple[str, ...]
    cuda_version: str | None


@dataclass(frozen=True, slots=True)
class EnvironmentMetadata:
    """The local runtime, platform, packages, and optional GPU information."""

    runtime: PythonRuntimeMetadata
    platform: PlatformMetadata
    packages: dict[str, str]
    gpu: GpuMetadata | None


def collect_environment_metadata() -> EnvironmentMetadata:
    """Collect deterministic environment metadata without sensitive values."""
    return EnvironmentMetadata(
        runtime=PythonRuntimeMetadata(
            version=platform.python_version(),
            implementation=platform.python_implementation(),
        ),
        platform=PlatformMetadata(
            system=platform.system(),
            release=platform.release(),
            architecture=platform.architecture()[0],
            machine=platform.machine(),
        ),
        packages=collect_installed_packages(),
        gpu=detect_gpu_metadata(),
    )


def collect_installed_packages() -> dict[str, str]:
    """Return normalized installed distribution names in stable order.

    Only the standard ``Name`` and ``Version`` metadata fields are read. Direct
    URLs, installer details, environment variables, and package contents are
    deliberately excluded.
    """
    candidates: dict[str, set[str]] = {}

    for distribution in metadata.distributions():
        try:
            name = distribution.metadata.get("Name")
            version = distribution.version
        except (KeyError, OSError, TypeError, ValueError):
            continue

        if not isinstance(name, str) or not isinstance(version, str):
            continue

        normalized_name = _normalize_distribution_name(name)
        normalized_version = version.strip()
        if not normalized_name or not normalized_version:
            continue

        candidates.setdefault(normalized_name, set()).add(normalized_version)

    # A malformed environment can expose duplicate metadata directories for
    # one normalized name. Choosing from sorted versions keeps capture stable.
    return {name: sorted(versions)[0] for name, versions in sorted(candidates.items())}


def detect_gpu_metadata() -> GpuMetadata | None:
    """Return best-effort NVIDIA GPU metadata, or ``None`` when unavailable."""
    query = _run_nvidia_smi(
        "--query-gpu=name,driver_version",
        "--format=csv,noheader,nounits",
    )
    if query is None or query.returncode != 0:
        return None

    devices: list[str] = []
    driver_versions: set[str] = set()
    for row in csv.reader(io.StringIO(query.stdout)):
        if not row:
            continue

        device = row[0].strip()
        if not device:
            continue

        devices.append(device)
        if len(row) > 1:
            driver_version = row[1].strip()
            if driver_version:
                driver_versions.add(driver_version)

    if not devices:
        return None

    cuda_version = None
    summary = _run_nvidia_smi()
    if summary is not None and summary.returncode == 0:
        match = _CUDA_VERSION.search(summary.stdout)
        if match is not None:
            cuda_version = match.group(1)

    return GpuMetadata(
        devices=tuple(sorted(devices, key=str.casefold)),
        driver_versions=tuple(sorted(driver_versions)),
        cuda_version=cuda_version,
    )


def _normalize_distribution_name(name: str) -> str:
    return _DISTRIBUTION_SEPARATOR.sub("-", name.strip()).casefold()


def _run_nvidia_smi(
    *arguments: str,
) -> subprocess.CompletedProcess[str] | None:
    try:
        return subprocess.run(
            ["nvidia-smi", *arguments],
            check=False,
            capture_output=True,
            encoding="utf-8",
            errors="replace",
            stdin=subprocess.DEVNULL,
            timeout=_NVIDIA_SMI_TIMEOUT_SECONDS,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
