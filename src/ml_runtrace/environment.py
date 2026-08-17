"""Capture privacy-conscious Python runtime and platform metadata."""

from __future__ import annotations

import csv
import io
import json
import platform
import re
import subprocess
from dataclasses import dataclass
from importlib import metadata
from urllib.parse import urlsplit, urlunsplit

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
class VcsPackageSourceMetadata:
    """Sanitized PEP 610 metadata for a VCS-installed distribution."""

    url: str
    vcs: str
    commit_id: str
    requested_revision: str | None = None
    subdirectory: str | None = None


@dataclass(frozen=True, slots=True)
class ArchivePackageSourceMetadata:
    """Sanitized PEP 610 metadata for an archive-installed distribution."""

    url: str
    hash: str | None = None
    subdirectory: str | None = None


@dataclass(frozen=True, slots=True)
class DirectoryPackageSourceMetadata:
    """A local installation marker that deliberately omits its absolute path."""

    editable: bool


PackageSourceMetadata = (
    VcsPackageSourceMetadata
    | ArchivePackageSourceMetadata
    | DirectoryPackageSourceMetadata
)


@dataclass(frozen=True, slots=True)
class EnvironmentMetadata:
    """The local runtime, platform, packages, and optional GPU information."""

    runtime: PythonRuntimeMetadata
    platform: PlatformMetadata
    packages: dict[str, str]
    package_sources: dict[str, PackageSourceMetadata]
    gpu: GpuMetadata | None


def collect_environment_metadata() -> EnvironmentMetadata:
    """Collect deterministic environment metadata without sensitive values."""
    packages, package_sources = _collect_installed_distributions()
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
        packages=packages,
        package_sources=package_sources,
        gpu=detect_gpu_metadata(),
    )


def collect_installed_packages() -> dict[str, str]:
    """Return normalized installed distribution names in stable order.

    The package mapping remains the stable name-to-version view used by v0.1.0.
    Privacy-conscious direct origins are collected separately from PEP 610
    metadata by :func:`collect_environment_metadata`.
    """
    packages, _ = _collect_installed_distributions()
    return packages


def _collect_installed_distributions() -> tuple[
    dict[str, str], dict[str, PackageSourceMetadata]
]:
    candidates: dict[str, list[tuple[str, PackageSourceMetadata | None]]] = {}

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

        source = _read_package_source(distribution)
        candidates.setdefault(normalized_name, []).append((normalized_version, source))

    # A malformed environment can expose duplicate metadata directories for
    # one normalized name. Choosing from sorted versions keeps capture stable.
    packages: dict[str, str] = {}
    package_sources: dict[str, PackageSourceMetadata] = {}
    for name, entries in sorted(candidates.items()):
        selected_version = min(version for version, _ in entries)
        packages[name] = selected_version
        sources = [
            source
            for version, source in entries
            if version == selected_version and source is not None
        ]
        if sources:
            package_sources[name] = min(sources, key=repr)

    return packages, package_sources


def _read_package_source(distribution: object) -> PackageSourceMetadata | None:
    read_text = getattr(distribution, "read_text", None)
    if not callable(read_text):
        return None
    try:
        document = read_text("direct_url.json")
    except (OSError, TypeError, UnicodeError, ValueError):
        return None
    if not isinstance(document, str):
        return None
    try:
        direct_url = json.loads(document)
    except (json.JSONDecodeError, TypeError):
        return None
    if not isinstance(direct_url, dict):
        return None

    vcs_info = direct_url.get("vcs_info")
    if isinstance(vcs_info, dict):
        url = _sanitize_remote_url(direct_url.get("url"))
        vcs = _nonempty_string(vcs_info.get("vcs"))
        commit_id = _nonempty_string(vcs_info.get("commit_id"))
        if url is None or vcs is None or commit_id is None:
            return None
        return VcsPackageSourceMetadata(
            url=url,
            vcs=vcs.casefold(),
            commit_id=commit_id,
            requested_revision=_nonempty_string(vcs_info.get("requested_revision")),
            subdirectory=_safe_subdirectory(direct_url.get("subdirectory")),
        )

    archive_info = direct_url.get("archive_info")
    if isinstance(archive_info, dict):
        url = _sanitize_remote_url(direct_url.get("url"))
        if url is None:
            return None
        return ArchivePackageSourceMetadata(
            url=url,
            hash=_archive_hash(archive_info),
            subdirectory=_safe_subdirectory(direct_url.get("subdirectory")),
        )

    directory_info = direct_url.get("dir_info")
    if isinstance(directory_info, dict):
        editable = directory_info.get("editable", False)
        if not isinstance(editable, bool):
            return None
        return DirectoryPackageSourceMetadata(editable=editable)

    return None


def _sanitize_remote_url(value: object) -> str | None:
    url = _nonempty_string(value)
    if url is None:
        return None
    try:
        parsed = urlsplit(url)
        port = parsed.port
    except ValueError:
        return None
    if (
        not parsed.scheme
        or parsed.scheme.casefold() == "file"
        or parsed.hostname is None
    ):
        return None

    hostname = parsed.hostname
    if ":" in hostname and not hostname.startswith("["):
        hostname = f"[{hostname}]"
    netloc = hostname if port is None else f"{hostname}:{port}"
    return urlunsplit((parsed.scheme.casefold(), netloc, parsed.path, "", ""))


def _archive_hash(archive_info: dict[object, object]) -> str | None:
    direct_hash = _nonempty_string(archive_info.get("hash"))
    if direct_hash is not None:
        return direct_hash

    hashes = archive_info.get("hashes")
    if not isinstance(hashes, dict):
        return None
    for algorithm, digest in sorted(hashes.items(), key=lambda item: str(item[0])):
        algorithm_value = _nonempty_string(algorithm)
        digest_value = _nonempty_string(digest)
        if algorithm_value is not None and digest_value is not None:
            return f"{algorithm_value}={digest_value}"
    return None


def _nonempty_string(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    normalized = value.strip()
    return normalized or None


def _safe_subdirectory(value: object) -> str | None:
    subdirectory = _nonempty_string(value)
    if subdirectory is None or "\x00" in subdirectory:
        return None

    normalized = subdirectory.replace("\\", "/")
    if normalized.startswith("/") or re.match(r"^[A-Za-z]:", normalized):
        return None
    parts = [part for part in normalized.split("/") if part not in ("", ".")]
    if not parts or ".." in parts:
        return None
    return "/".join(parts)


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
