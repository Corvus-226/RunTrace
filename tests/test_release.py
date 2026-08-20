"""Release metadata and candidate-workflow guardrails."""

from __future__ import annotations

import re
import struct
from pathlib import Path

import yaml

from ml_runtrace import __version__

_ROOT = Path(__file__).resolve().parents[1]
_PINNED_ACTION = re.compile(r"^[^\s@]+@[0-9a-f]{40}$")
_UPLOAD_ARTIFACT = (
    "actions/upload-artifact@043fb46d1a93c77aae656e7c1c64a875d1fc6a0a # v7.0.1"
)
_DOWNLOAD_ARTIFACT = (
    "actions/download-artifact@3e5f45b2cfb9172054b4087a40e8e0b5a5461e7c # v8.0.1"
)


def test_build_backend_emits_twine_compatible_metadata() -> None:
    pyproject = (_ROOT / "pyproject.toml").read_text(encoding="utf-8")

    assert 'requires = ["hatchling>=1.27,<1.30"]' in pyproject
    assert '"/docs/assets/runtrace-overview.png"' in pyproject
    assert '"/docs/RunTrace_v0.1.0_release_progress_guide_2026-08-13.md"' in pyproject
    assert '"/docs/codex_for_oss_runtrace_plan_2026-08-12.md"' in pyproject


def test_readme_brand_hero_is_present_and_publishable() -> None:
    readme = (_ROOT / "README.md").read_text(encoding="utf-8")
    image_path = _ROOT / "docs" / "assets" / "runtrace-overview.png"
    image_url = (
        "https://raw.githubusercontent.com/Corvus-226/RunTrace/"
        "main/docs/assets/runtrace-overview.png"
    )

    assert image_url in readme
    assert (
        "![RunTrace — Know exactly what changed. An experiment fingerprint "
        "formed by overlapping version traces]" in readme
    )
    assert "*The local workflow is init → snapshot → list/show → diff." not in readme
    header = image_path.read_bytes()[:24]
    assert header[:8] == b"\x89PNG\r\n\x1a\n"
    width, height = struct.unpack(">II", header[16:24])
    assert width >= 1200
    assert height >= 675
    assert abs((width / height) - 2.0) < 0.02


def test_public_names_are_collision_free() -> None:
    pyproject = (_ROOT / "pyproject.toml").read_text(encoding="utf-8")

    assert 'ml-runtrace = "ml_runtrace.cli:main"' in pyproject
    assert 'packages = ["src/ml_runtrace"]' in pyproject
    assert 'runtrace = "runtrace.cli:main"' not in pyproject
    assert 'packages = ["src/runtrace"]' not in pyproject
    assert (_ROOT / "src" / "ml_runtrace" / "__main__.py").is_file()
    assert not (_ROOT / "src" / "runtrace").exists()
    assert (_ROOT / "scripts" / "check_public_name_coexistence.py").is_file()

    for relative_path in (
        "README.md",
        "docs/getting-started.md",
        "docs/releases/v0.1.0.md",
        "docs/releases/v0.2.0.md",
        "docs/releases/v0.3.0.md",
        "docs/run-correlation.md",
    ):
        contents = (_ROOT / relative_path).read_text(encoding="utf-8")
        assert re.search(r"(?m)^(?:uv run )?runtrace(?:\s|$)", contents) is None


def test_release_documents_match_package_version() -> None:
    assert __version__ == "0.3.0"

    changelog = (_ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    readme = (_ROOT / "README.md").read_text(encoding="utf-8")
    release_notes = _ROOT / "docs" / "releases" / f"v{__version__}.md"

    assert f"## [{__version__}] - 2026-08-20" in changelog
    assert f"v{__version__}" in readme
    assert "distribution metadata target v0.3.0" in readme
    assert "python -m pip install ml-runtrace" in readme
    assert "python -m pip install ." not in readme
    assert release_notes.is_file()
    release_notes_text = release_notes.read_text(encoding="utf-8")
    assert f"# RunTrace v{__version__}" in release_notes_text
    assert "Draft release notes" not in release_notes_text
    assert f"ml-runtrace=={__version__}" in release_notes_text


def test_run_id_correlation_contract_is_documented_without_a_dependency() -> None:
    pyproject = (_ROOT / "pyproject.toml").read_text(encoding="utf-8")
    execution = (_ROOT / "src" / "ml_runtrace" / "execution.py").read_text(
        encoding="utf-8"
    )

    assert 'RUN_ID_ENVIRONMENT_VARIABLE = "RUNTRACE_RUN_ID"' in execution
    assert "opentelemetry" not in pyproject.casefold()
    for relative_path in (
        "README.md",
        "docs/getting-started.md",
        "docs/run-correlation.md",
        "docs/releases/v0.3.0.md",
    ):
        contents = (_ROOT / relative_path).read_text(encoding="utf-8")
        assert "RUNTRACE_RUN_ID" in contents
        assert "runtrace.run.id" in contents


def test_release_workflow_builds_candidates_without_publishing() -> None:
    workflow_path = _ROOT / ".github" / "workflows" / "release.yml"
    workflow = workflow_path.read_text(encoding="utf-8")

    assert yaml.safe_load(workflow) is not None
    assert "workflow_dispatch:" in workflow
    assert "default: 0.3.0" in workflow
    assert "contents: read" in workflow
    assert "id-token: write" not in workflow
    assert "gh-action-pypi-publish" not in workflow
    assert "gh release create" not in workflow
    assert "scripts/check_public_name_coexistence.py --dist-dir dist" in workflow
    assert _UPLOAD_ARTIFACT in workflow

    action_references = re.findall(
        r"^\s*uses:\s*(\S+)\s*(?:#.*)?$", workflow, re.MULTILINE
    )
    assert action_references
    assert all(_PINNED_ACTION.fullmatch(reference) for reference in action_references)


def test_ci_clean_wheel_uses_the_package_version() -> None:
    workflow_path = _ROOT / ".github" / "workflows" / "ci.yml"
    workflow = workflow_path.read_text(encoding="utf-8")

    assert yaml.safe_load(workflow) is not None
    assert 'expected_version="$(uv run python -c' in workflow
    assert '"ml-runtrace ${expected_version}"' in workflow
    assert '"ml-runtrace 0.1.0"' not in workflow


def test_publish_workflow_uses_least_privilege_trusted_publishing() -> None:
    workflow_path = _ROOT / ".github" / "workflows" / "publish.yml"
    workflow = workflow_path.read_text(encoding="utf-8")
    parsed = yaml.safe_load(workflow)

    assert parsed is not None
    assert 'tags:\n      - "v*.*.*"' in workflow
    assert "workflow_dispatch:" not in workflow
    assert "pull_request:" not in workflow
    assert workflow.count("id-token: write") == 1
    assert "environment:\n      name: pypi" in workflow
    assert "url: https://pypi.org/p/ml-runtrace" in workflow
    assert "username:" not in workflow
    assert "password:" not in workflow
    assert "secrets." not in workflow
    assert "scripts/check_public_name_coexistence.py --dist-dir dist" in workflow
    assert "sha256sum --check SHA256SUMS" in workflow
    assert _UPLOAD_ARTIFACT in workflow
    assert _DOWNLOAD_ARTIFACT in workflow

    jobs = parsed["jobs"]
    build = jobs["build"]
    publish = jobs["publish"]
    assert build.get("permissions") is None
    assert publish["needs"] == "build"
    assert publish["permissions"] == {"contents": "read", "id-token": "write"}

    build_steps = "\n".join(str(step) for step in build["steps"])
    publish_steps = "\n".join(str(step) for step in publish["steps"])
    assert "uv build" in build_steps
    assert "actions/upload-artifact@" in build_steps
    assert "actions/download-artifact@" in publish_steps
    assert "pypa/gh-action-pypi-publish@" in publish_steps
    assert "actions/checkout@" not in publish_steps
    assert "uv " not in publish_steps
    assert "pip " not in publish_steps

    action_references = re.findall(
        r"^\s*uses:\s*(\S+)\s*(?:#.*)?$", workflow, re.MULTILINE
    )
    assert action_references
    assert all(_PINNED_ACTION.fullmatch(reference) for reference in action_references)
