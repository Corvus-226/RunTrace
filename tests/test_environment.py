"""Tests for deterministic, privacy-conscious environment capture."""

from __future__ import annotations

import subprocess
from dataclasses import asdict, dataclass

import pytest

import runtrace.environment as environment_module
from runtrace.environment import (
    collect_environment_metadata,
    collect_installed_packages,
    detect_gpu_metadata,
)


@dataclass
class _Distribution:
    name: str | None
    version: str
    source_url: str = "https://packages.example.invalid/private"

    @property
    def metadata(self) -> dict[str, str]:
        values = {
            "Home-page": self.source_url,
            "Download-URL": self.source_url,
        }
        if self.name is not None:
            values["Name"] = self.name
        return values


def test_collects_runtime_and_platform_without_gpu(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(environment_module.platform, "python_version", lambda: "3.12.7")
    monkeypatch.setattr(
        environment_module.platform,
        "python_implementation",
        lambda: "CPython",
    )
    monkeypatch.setattr(environment_module.platform, "system", lambda: "TestOS")
    monkeypatch.setattr(environment_module.platform, "release", lambda: "2026.1")
    monkeypatch.setattr(
        environment_module.platform,
        "architecture",
        lambda: ("64bit", "test"),
    )
    monkeypatch.setattr(environment_module.platform, "machine", lambda: "test64")
    monkeypatch.setattr(
        environment_module.metadata,
        "distributions",
        lambda: [_Distribution("Example_Package", "1.2.3")],
    )
    monkeypatch.setattr(environment_module, "detect_gpu_metadata", lambda: None)

    captured = collect_environment_metadata()

    assert captured.runtime.version == "3.12.7"
    assert captured.runtime.implementation == "CPython"
    assert captured.platform.system == "TestOS"
    assert captured.platform.release == "2026.1"
    assert captured.platform.architecture == "64bit"
    assert captured.platform.machine == "test64"
    assert captured.packages == {"example-package": "1.2.3"}
    assert captured.gpu is None


def test_packages_are_normalized_deduplicated_and_sorted(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    distributions = [
        _Distribution("Zeta_Pkg", "3.0"),
        _Distribution("alpha.pkg", "2.0"),
        _Distribution("Alpha-Pkg", "1.0"),
        _Distribution(None, "9.9"),
        _Distribution("empty-version", "  "),
    ]
    monkeypatch.setattr(
        environment_module.metadata,
        "distributions",
        lambda: distributions,
    )

    packages = collect_installed_packages()

    assert packages == {"alpha-pkg": "1.0", "zeta-pkg": "3.0"}
    assert list(packages) == sorted(packages)


def test_package_source_urls_are_not_captured(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source_url = "https://packages.example.invalid/secret-token"
    monkeypatch.setattr(
        environment_module.metadata,
        "distributions",
        lambda: [_Distribution("safe-package", "4.2", source_url)],
    )
    monkeypatch.setattr(environment_module, "detect_gpu_metadata", lambda: None)

    captured = collect_environment_metadata()

    assert captured.packages == {"safe-package": "4.2"}
    assert source_url not in repr(asdict(captured))


def test_missing_nvidia_smi_returns_no_gpu(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def missing_command(*args: object, **kwargs: object) -> None:
        raise FileNotFoundError

    monkeypatch.setattr(environment_module.subprocess, "run", missing_command)

    assert detect_gpu_metadata() is None


def test_environment_capture_continues_without_nvidia_smi(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def missing_command(*args: object, **kwargs: object) -> None:
        raise FileNotFoundError

    monkeypatch.setattr(environment_module.subprocess, "run", missing_command)
    monkeypatch.setattr(
        environment_module.metadata,
        "distributions",
        lambda: [_Distribution("available-package", "1.0")],
    )

    captured = collect_environment_metadata()

    assert captured.packages == {"available-package": "1.0"}
    assert captured.gpu is None


def test_nvidia_smi_timeout_returns_no_gpu(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def timed_out(*args: object, **kwargs: object) -> None:
        raise subprocess.TimeoutExpired(cmd="nvidia-smi", timeout=5)

    monkeypatch.setattr(environment_module.subprocess, "run", timed_out)

    assert detect_gpu_metadata() is None


def test_nonzero_nvidia_smi_returns_no_gpu(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def failed_command(
        command: list[str], **kwargs: object
    ) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(command, 1, stdout="", stderr="failure")

    monkeypatch.setattr(environment_module.subprocess, "run", failed_command)

    assert detect_gpu_metadata() is None


def test_gpu_and_cuda_metadata_are_parsed_deterministically(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def successful_command(
        command: list[str], **kwargs: object
    ) -> subprocess.CompletedProcess[str]:
        if len(command) > 1:
            stdout = "NVIDIA Zeta, 555.42\nNVIDIA Alpha, 555.42\n"
        else:
            stdout = "NVIDIA-SMI 555.42    CUDA Version: 12.5\n"
        return subprocess.CompletedProcess(command, 0, stdout=stdout, stderr="")

    monkeypatch.setattr(environment_module.subprocess, "run", successful_command)

    captured = detect_gpu_metadata()

    assert captured is not None
    assert captured.devices == ("NVIDIA Alpha", "NVIDIA Zeta")
    assert captured.driver_versions == ("555.42",)
    assert captured.cuda_version == "12.5"


def test_cuda_probe_failure_preserves_detected_gpu(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls = 0

    def partly_successful_command(
        command: list[str], **kwargs: object
    ) -> subprocess.CompletedProcess[str]:
        nonlocal calls
        calls += 1
        if calls == 1:
            return subprocess.CompletedProcess(
                command,
                0,
                stdout="NVIDIA Test, 550.1\n",
                stderr="",
            )
        return subprocess.CompletedProcess(command, 1, stdout="", stderr="failure")

    monkeypatch.setattr(
        environment_module.subprocess,
        "run",
        partly_successful_command,
    )

    captured = detect_gpu_metadata()

    assert captured is not None
    assert captured.devices == ("NVIDIA Test",)
    assert captured.driver_versions == ("550.1",)
    assert captured.cuda_version is None
