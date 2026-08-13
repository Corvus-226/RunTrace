"""Tests for safe, portable experiment configuration capture."""

from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

from ml_runtrace.config import ConfigLoadError, load_yaml_config


def test_loads_yaml_with_relative_path_hash_and_values(tmp_path: Path) -> None:
    project = tmp_path / "project"
    current = project / "experiments"
    config = project / "configs" / "train.yaml"
    current.mkdir(parents=True)
    config.parent.mkdir()
    raw_config = (
        b"model:\n"
        b"  name: resnet18\n"
        b"optimizer:\n"
        b"  learning_rate: 0.001\n"
        b"augmentations:\n"
        b"  - flip\n"
    )
    config.write_bytes(raw_config)

    loaded = load_yaml_config(
        Path("../configs/train.yaml"),
        current_directory=current,
        project_root=project,
    )

    assert loaded.path == "configs/train.yaml"
    assert loaded.sha256 == hashlib.sha256(raw_config).hexdigest()
    assert loaded.values == {
        "model": {"name": "resnet18"},
        "optimizer": {"learning_rate": 0.001},
        "augmentations": ["flip"],
    }


def test_missing_config_error_is_actionable(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()

    with pytest.raises(ConfigLoadError, match="does not exist"):
        load_yaml_config(
            Path("missing.yaml"),
            current_directory=project,
            project_root=project,
        )


@pytest.mark.parametrize(
    "document",
    [
        "model: [unterminated\n",
        "value: !!python/name:builtins.str ''\n",
    ],
)
def test_invalid_or_unsafe_yaml_error_is_actionable(
    tmp_path: Path, document: str
) -> None:
    project = tmp_path / "project"
    project.mkdir()
    config = project / "invalid.yaml"
    config.write_text(document, encoding="utf-8")

    with pytest.raises(ConfigLoadError, match="contains invalid YAML"):
        load_yaml_config(
            config,
            current_directory=project,
            project_root=project,
        )


@pytest.mark.parametrize(
    "document",
    [
        "published: 2026-08-12\n",
        "1: value\n",
        "values: !!set {one: null, two: null}\n",
        "value: .nan\n",
    ],
)
def test_non_json_yaml_structures_are_rejected(tmp_path: Path, document: str) -> None:
    project = tmp_path / "project"
    project.mkdir()
    config = project / "unsupported.yaml"
    config.write_text(document, encoding="utf-8")

    with pytest.raises(ConfigLoadError, match="JSON-compatible YAML structures"):
        load_yaml_config(
            config,
            current_directory=project,
            project_root=project,
        )


def test_config_outside_repository_is_rejected(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()
    config = tmp_path / "outside.yaml"
    config.write_text("safe: true\n", encoding="utf-8")

    with pytest.raises(ConfigLoadError, match="inside the Git repository"):
        load_yaml_config(
            config,
            current_directory=project,
            project_root=project,
        )


def test_config_must_be_utf8(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()
    config = project / "encoded.yaml"
    config.write_bytes(b"name: \xff\xfe\n")

    with pytest.raises(ConfigLoadError, match="UTF-8 encoded YAML"):
        load_yaml_config(
            config,
            current_directory=project,
            project_root=project,
        )
