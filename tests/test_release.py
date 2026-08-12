"""Release metadata and candidate-workflow guardrails."""

from __future__ import annotations

import re
from pathlib import Path

import yaml

from runtrace import __version__

_ROOT = Path(__file__).resolve().parents[1]
_PINNED_ACTION = re.compile(r"^[^\s@]+@[0-9a-f]{40}$")


def test_build_backend_emits_twine_compatible_metadata() -> None:
    pyproject = (_ROOT / "pyproject.toml").read_text(encoding="utf-8")

    assert 'requires = ["hatchling>=1.27,<1.30"]' in pyproject
    assert '"/docs/RunTrace_v0.1.0_release_progress_guide_2026-08-13.md"' in pyproject
    assert '"/docs/codex_for_oss_runtrace_plan_2026-08-12.md"' in pyproject


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

    action_references = re.findall(
        r"^\s*uses:\s*(\S+)\s*(?:#.*)?$", workflow, re.MULTILINE
    )
    assert action_references
    assert all(_PINNED_ACTION.fullmatch(reference) for reference in action_references)
