"""Release metadata and candidate-workflow guardrails."""

from __future__ import annotations

import re
from pathlib import Path

import yaml

from ml_runtrace import __version__

_ROOT = Path(__file__).resolve().parents[1]
_PINNED_ACTION = re.compile(r"^[^\s@]+@[0-9a-f]{40}$")
_UPLOAD_ARTIFACT_V5 = (
    "actions/upload-artifact@330a01c490aca151604b8cf639adc76d48f6c5d4 # v5"
)


def test_build_backend_emits_twine_compatible_metadata() -> None:
    pyproject = (_ROOT / "pyproject.toml").read_text(encoding="utf-8")

    assert 'requires = ["hatchling>=1.27,<1.30"]' in pyproject
    assert '"/docs/RunTrace_v0.1.0_release_progress_guide_2026-08-13.md"' in pyproject
    assert '"/docs/codex_for_oss_runtrace_plan_2026-08-12.md"' in pyproject


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
    ):
        contents = (_ROOT / relative_path).read_text(encoding="utf-8")
        assert re.search(r"(?m)^(?:uv run )?runtrace(?:\s|$)", contents) is None


def test_release_documents_match_package_version() -> None:
    assert __version__ == "0.1.0"

    changelog = (_ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    readme = (_ROOT / "README.md").read_text(encoding="utf-8")
    release_notes = _ROOT / "docs" / "releases" / f"v{__version__}.md"

    assert f"## [{__version__}] - Unreleased" in changelog
    assert f"Project status:** v{__version__} release candidate." in readme
    assert "It has not been published to\n> PyPI." in readme
    assert "python -m pip install ." in readme
    assert "python -m pip install ml-runtrace" not in readme
    assert release_notes.is_file()
    assert f"# RunTrace v{__version__}" in release_notes.read_text(encoding="utf-8")


def test_release_workflow_builds_candidates_without_publishing() -> None:
    workflow_path = _ROOT / ".github" / "workflows" / "release.yml"
    workflow = workflow_path.read_text(encoding="utf-8")

    assert yaml.safe_load(workflow) is not None
    assert "workflow_dispatch:" in workflow
    assert "contents: read" in workflow
    assert "id-token: write" not in workflow
    assert "gh-action-pypi-publish" not in workflow
    assert "gh release create" not in workflow
    assert "scripts/check_public_name_coexistence.py --dist-dir dist" in workflow
    assert _UPLOAD_ARTIFACT_V5 in workflow

    action_references = re.findall(
        r"^\s*uses:\s*(\S+)\s*(?:#.*)?$", workflow, re.MULTILINE
    )
    assert action_references
    assert all(_PINNED_ACTION.fullmatch(reference) for reference in action_references)


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
    assert _UPLOAD_ARTIFACT_V5 in workflow

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
