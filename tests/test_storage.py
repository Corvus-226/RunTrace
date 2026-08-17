"""Tests for validated, atomic local snapshot persistence."""

from __future__ import annotations

import re
from datetime import datetime, timezone
from pathlib import Path

import pytest
import yaml
from pydantic import ValidationError

import ml_runtrace.storage as storage_module
from ml_runtrace.models import (
    EnvironmentSnapshot,
    ExperimentSnapshot,
    GitSnapshot,
    GpuSnapshot,
    HardwareSnapshot,
    PlatformSnapshot,
    RuntimeSnapshot,
    Snapshot,
    VcsPackageSourceSnapshot,
    generate_run_id,
)
from ml_runtrace.storage import (
    SnapshotAmbiguousIdError,
    SnapshotConflictError,
    SnapshotNotFoundError,
    SnapshotStorageError,
    SnapshotStore,
)


def _project(tmp_path: Path) -> Path:
    project = tmp_path / "project"
    (project / ".runtrace").mkdir(parents=True)
    return project


def _snapshot(
    run_id: str = "a31f82000001",
    *,
    timestamp: datetime | None = None,
    name: str = "baseline",
) -> Snapshot:
    return Snapshot(
        run_id=run_id,
        name=name,
        timestamp=timestamp or datetime(2026, 8, 13, 6, 31, tzinfo=timezone.utc),
        git=GitSnapshot(
            commit="83ab2c1" * 5 + "83ab2",
            branch="main",
            detached=False,
            dirty=False,
        ),
        runtime=RuntimeSnapshot(
            python="3.12.7",
            implementation="CPython",
            platform=PlatformSnapshot(
                system="Windows",
                release="11",
                architecture="64bit",
                machine="AMD64",
            ),
        ),
        environment=EnvironmentSnapshot(
            packages={"zeta-package": "2.0", "alpha-package": "1.0"}
        ),
        hardware=HardwareSnapshot(
            gpu=GpuSnapshot(
                devices=("NVIDIA Test GPU",),
                driver_versions=("555.42",),
                cuda_version="12.5",
            )
        ),
        experiment=ExperimentSnapshot(
            command="python train.py --config configs/train.yaml",
            config_path="configs/train.yaml",
            config_hash="f" * 64,
            config={"batch_size": 32, "optimizer": {"name": "adamw"}},
        ),
    )


def test_generated_run_ids_are_short_hex_and_collision_resistant() -> None:
    generated = {generate_run_id() for _ in range(1_000)}

    assert len(generated) == 1_000
    assert all(re.fullmatch(r"[0-9a-f]{12}", run_id) for run_id in generated)


def test_snapshot_defaults_to_an_aware_utc_timestamp() -> None:
    template = _snapshot()
    snapshot = Snapshot(
        git=template.git,
        runtime=template.runtime,
        environment=template.environment,
        hardware=template.hardware,
        experiment=template.experiment,
    )

    assert re.fullmatch(r"[0-9a-f]{12}", snapshot.run_id)
    assert snapshot.timestamp.tzinfo is not None
    assert snapshot.timestamp.utcoffset() == timezone.utc.utcoffset(snapshot.timestamp)


def test_naive_timestamp_is_rejected() -> None:
    with pytest.raises(ValidationError, match="timestamp must include a timezone"):
        _snapshot(timestamp=datetime(2026, 8, 13, 6, 31))


def test_save_and_load_round_trip_without_data_loss(tmp_path: Path) -> None:
    store = SnapshotStore(_project(tmp_path))
    expected = _snapshot()

    path = store.save(expected)
    loaded = store.load(expected.run_id)

    assert path == (
        tmp_path / "project" / ".runtrace" / "runs" / f"{expected.run_id}.yaml"
    )
    assert loaded == expected
    document = path.read_text(encoding="utf-8")
    assert document.startswith("schema_version: 1\nrun_id: a31f82000001\n")
    assert "command: python train.py" in document
    assert yaml.safe_load(document)["environment"]["packages"] == {
        "alpha-package": "1.0",
        "zeta-package": "2.0",
    }


def test_schema_v1_snapshots_without_additive_fields_still_load(
    tmp_path: Path,
) -> None:
    project = _project(tmp_path)
    runs = project / ".runtrace" / "runs"
    runs.mkdir()
    expected = _snapshot()
    document = expected.model_dump(mode="json")
    document["environment"].pop("package_sources")
    document["experiment"].pop("command_argv")
    path = runs / f"{expected.run_id}.yaml"
    path.write_text(
        yaml.safe_dump(document, sort_keys=False),
        encoding="utf-8",
    )

    loaded = SnapshotStore(project).load(expected.run_id)

    assert loaded.environment.package_sources == {}
    assert loaded.experiment.command_argv is None


def test_package_source_requires_a_matching_distribution() -> None:
    with pytest.raises(ValidationError, match="matching packages"):
        EnvironmentSnapshot(
            packages={},
            package_sources={
                "missing-package": VcsPackageSourceSnapshot(
                    url="https://github.com/example/missing-package.git",
                    vcs="git",
                    commit_id="a" * 40,
                )
            },
        )


def test_duplicate_run_id_never_overwrites_existing_snapshot(tmp_path: Path) -> None:
    store = SnapshotStore(_project(tmp_path))
    original = _snapshot(name="original")
    destination = store.save(original)

    with pytest.raises(SnapshotConflictError, match="already exists"):
        store.save(_snapshot(name="replacement"))

    assert store.load(original.run_id).name == "original"
    assert destination.read_text(encoding="utf-8").count("original") == 1


def test_failed_atomic_replace_leaves_no_partial_snapshot(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    store = SnapshotStore(_project(tmp_path))

    def failed_replace(source: Path, destination: Path) -> None:
        raise OSError("simulated replace failure")

    monkeypatch.setattr(storage_module.os, "replace", failed_replace)

    with pytest.raises(SnapshotStorageError, match="simulated replace failure"):
        store.save(_snapshot())

    runs = tmp_path / "project" / ".runtrace" / "runs"
    assert list(runs.iterdir()) == []


def test_existing_save_lock_reports_a_conflict(tmp_path: Path) -> None:
    store = SnapshotStore(_project(tmp_path))
    runs = tmp_path / "project" / ".runtrace" / "runs"
    runs.mkdir()
    lock = runs / ".a31f82000001.lock"
    lock.write_text("", encoding="utf-8")

    with pytest.raises(SnapshotConflictError, match="already being saved"):
        store.save(_snapshot())

    assert lock.exists()
    assert not (runs / "a31f82000001.yaml").exists()


def test_snapshots_are_listed_newest_first(tmp_path: Path) -> None:
    store = SnapshotStore(_project(tmp_path))
    old = _snapshot(
        "100000000001",
        timestamp=datetime(2026, 8, 13, 1, tzinfo=timezone.utc),
    )
    newest = _snapshot(
        "300000000003",
        timestamp=datetime(2026, 8, 13, 3, tzinfo=timezone.utc),
    )
    middle = _snapshot(
        "200000000002",
        timestamp=datetime(2026, 8, 13, 2, tzinfo=timezone.utc),
    )
    for snapshot in (old, newest, middle):
        store.save(snapshot)

    assert [snapshot.run_id for snapshot in store.list_snapshots()] == [
        newest.run_id,
        middle.run_id,
        old.run_id,
    ]


def test_full_and_unique_abbreviated_ids_resolve(tmp_path: Path) -> None:
    store = SnapshotStore(_project(tmp_path))
    expected = _snapshot("a31f82000001")
    store.save(expected)
    store.save(_snapshot("b91de3000002"))

    assert store.resolve_run_id(expected.run_id) == expected.run_id
    assert store.resolve_run_id("A31F82") == expected.run_id
    assert store.load("a31f82") == expected


def test_ambiguous_abbreviated_id_is_actionable(tmp_path: Path) -> None:
    store = SnapshotStore(_project(tmp_path))
    store.save(_snapshot("abc000000001"))
    store.save(_snapshot("abc000000002"))

    with pytest.raises(SnapshotAmbiguousIdError, match="is ambiguous"):
        store.load("abc")


def test_missing_and_malformed_ids_are_actionable(tmp_path: Path) -> None:
    store = SnapshotStore(_project(tmp_path))

    with pytest.raises(SnapshotNotFoundError, match="No snapshot matches"):
        store.load("abcdef")
    with pytest.raises(SnapshotNotFoundError, match="hexadecimal"):
        store.load("../../secret")


def test_invalid_yaml_reports_the_snapshot_filename(tmp_path: Path) -> None:
    project = _project(tmp_path)
    runs = project / ".runtrace" / "runs"
    runs.mkdir()
    path = runs / "a31f82000001.yaml"
    path.write_text("git: [unterminated\n", encoding="utf-8")

    with pytest.raises(
        SnapshotStorageError,
        match=r"a31f82000001\.yaml contains invalid YAML",
    ):
        SnapshotStore(project).load("a31f82")


def test_invalid_schema_reports_actionable_error(tmp_path: Path) -> None:
    project = _project(tmp_path)
    runs = project / ".runtrace" / "runs"
    runs.mkdir()
    path = runs / "a31f82000001.yaml"
    path.write_text("schema_version: 1\nrun_id: a31f82000001\n", encoding="utf-8")

    with pytest.raises(SnapshotStorageError, match="does not match schema version 1"):
        SnapshotStore(project).load("a31f82")


def test_filename_and_declared_run_id_must_match(tmp_path: Path) -> None:
    project = _project(tmp_path)
    store = SnapshotStore(project)
    source = store.save(_snapshot("a31f82000001"))
    destination = source.with_name("b91de3000002.yaml")
    source.rename(destination)

    with pytest.raises(SnapshotStorageError, match="declares run ID"):
        store.load("b91de3")


def test_uninitialized_project_is_rejected_without_creating_files(
    tmp_path: Path,
) -> None:
    project = tmp_path / "project"
    project.mkdir()
    store = SnapshotStore(project)

    with pytest.raises(SnapshotStorageError, match="not initialized"):
        store.save(_snapshot())

    assert list(project.iterdir()) == []


def test_run_id_validation_prevents_path_traversal() -> None:
    with pytest.raises(ValidationError, match="run_id"):
        _snapshot("../../outside")


def test_metadata_symlink_cannot_escape_project(tmp_path: Path) -> None:
    project = tmp_path / "project"
    outside = tmp_path / "outside"
    project.mkdir()
    outside.mkdir()
    try:
        (project / ".runtrace").symlink_to(outside, target_is_directory=True)
    except OSError:
        pytest.skip("directory symlinks are unavailable on this platform")

    with pytest.raises(SnapshotStorageError, match="escapes the project root"):
        SnapshotStore(project).list_snapshots()
