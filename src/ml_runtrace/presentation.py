"""Rich terminal presentation for RunTrace snapshot data."""

from __future__ import annotations

import json
import re
from collections.abc import Sequence
from datetime import timezone

from rich import box
from rich.console import Console
from rich.rule import Rule
from rich.syntax import Syntax
from rich.table import Table
from rich.text import Text

from ml_runtrace.diff import (
    DifferenceKind,
    DifferenceSection,
    SnapshotComparison,
    SnapshotDifference,
)
from ml_runtrace.models import Snapshot

_WHITESPACE = re.compile(r"\s+")


def print_snapshot_list(snapshots: Sequence[Snapshot], console: Console) -> None:
    """Print a compact newest-first summary of persisted snapshots."""
    if not snapshots:
        console.print(
            "No snapshots recorded yet. Run `ml-runtrace snapshot` to create one."
        )
        return

    table = Table(
        box=box.SIMPLE_HEAD,
        expand=False,
        pad_edge=False,
        show_edge=False,
    )
    table.add_column("RUN ID", no_wrap=True)
    table.add_column("NAME", max_width=24, overflow="ellipsis", no_wrap=True)
    table.add_column("COMMIT", no_wrap=True)
    table.add_column("DIRTY", no_wrap=True)
    table.add_column("CREATED", no_wrap=True)

    for snapshot in snapshots:
        table.add_row(
            Text(snapshot.run_id),
            Text(_display_name(snapshot.name)),
            Text(snapshot.git.commit[:7] if snapshot.git.commit else "—"),
            "yes" if snapshot.git.dirty else "no",
            snapshot.timestamp.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        )

    console.print(table)


def print_snapshot(snapshot: Snapshot, console: Console) -> None:
    """Print every value stored in one snapshot using labeled sections."""
    created = snapshot.timestamp.astimezone(timezone.utc).isoformat()
    created = created.replace("+00:00", "Z")
    _print_fields(
        console,
        "Overview",
        (
            ("Run ID", snapshot.run_id),
            ("Name", snapshot.name),
            ("Created", created),
            ("Schema", str(snapshot.schema_version)),
        ),
    )
    _print_fields(
        console,
        "Git",
        (
            ("Commit", snapshot.git.commit),
            ("Branch", snapshot.git.branch),
            ("Detached", _yes_no(snapshot.git.detached)),
            ("Dirty", _yes_no(snapshot.git.dirty)),
        ),
    )
    _print_fields(
        console,
        "Runtime",
        (
            ("Python", snapshot.runtime.python),
            ("Implementation", snapshot.runtime.implementation),
            ("System", snapshot.runtime.platform.system),
            ("Release", snapshot.runtime.platform.release),
            ("Architecture", snapshot.runtime.platform.architecture),
            ("Machine", snapshot.runtime.platform.machine),
        ),
    )
    _print_packages(snapshot, console)
    _print_hardware(snapshot, console)
    _print_experiment(snapshot, console)


def print_snapshot_comparison(
    comparison: SnapshotComparison,
    console: Console,
) -> None:
    """Print deterministic, sectioned changes between two snapshots."""
    console.print(
        Text(
            f"Comparing {comparison.before_run_id} -> {comparison.after_run_id}",
        )
    )
    if not comparison.differences:
        console.print("No relevant differences found.")
        return

    for section in DifferenceSection:
        section_differences = [
            difference
            for difference in comparison.differences
            if difference.section is section
        ]
        if not section_differences:
            continue
        console.print(Rule(section.value, align="left"))
        for difference in section_differences:
            console.print(
                Text(f"{difference.kind.value}  {difference.path}"),
            )
            values = Table.grid(padding=(0, 2))
            values.add_column(style="bold", no_wrap=True)
            values.add_column(overflow="fold")
            values.add_row(
                "before",
                Text(_difference_value(difference, before=True)),
            )
            values.add_row(
                "after",
                Text(_difference_value(difference, before=False)),
            )
            console.print(values)


def _print_fields(
    console: Console,
    heading: str,
    fields: Sequence[tuple[str, str | None]],
) -> None:
    console.print(Rule(heading, align="left"))
    table = Table.grid(padding=(0, 2))
    table.add_column(style="bold", no_wrap=True)
    table.add_column(overflow="fold")
    for label, value in fields:
        table.add_row(label, Text(value if value is not None else "—"))
    console.print(table)


def _print_packages(snapshot: Snapshot, console: Console) -> None:
    console.print(Rule("Environment", align="left"))
    if not snapshot.environment.packages:
        console.print("No packages recorded.")
        return

    table = Table(
        box=box.SIMPLE_HEAD,
        expand=False,
        pad_edge=False,
        show_edge=False,
    )
    table.add_column("PACKAGE")
    table.add_column("VERSION")
    for package, version in snapshot.environment.packages.items():
        table.add_row(Text(package), Text(version))
    console.print(table)


def _print_hardware(snapshot: Snapshot, console: Console) -> None:
    gpu = snapshot.hardware.gpu
    _print_fields(
        console,
        "Hardware",
        (
            ("GPU", ", ".join(gpu.devices) if gpu and gpu.devices else None),
            (
                "Driver",
                ", ".join(gpu.driver_versions) if gpu and gpu.driver_versions else None,
            ),
            ("CUDA", gpu.cuda_version if gpu is not None else None),
        ),
    )


def _print_experiment(snapshot: Snapshot, console: Console) -> None:
    _print_fields(
        console,
        "Experiment",
        (
            ("Command", snapshot.experiment.command),
            ("Config path", snapshot.experiment.config_path),
            ("Config SHA-256", snapshot.experiment.config_hash),
        ),
    )
    if snapshot.experiment.config_path is None:
        console.print("Config values  —")
        return

    config_json = json.dumps(
        snapshot.experiment.config,
        allow_nan=False,
        ensure_ascii=False,
        indent=2,
        sort_keys=True,
    )
    console.print("Config values")
    console.print(Syntax(config_json, "json", word_wrap=True))


def _yes_no(value: bool) -> str:
    return "yes" if value else "no"


def _difference_value(
    difference: SnapshotDifference,
    *,
    before: bool,
) -> str:
    if before and difference.kind is DifferenceKind.ADDED:
        return "—"
    if not before and difference.kind is DifferenceKind.REMOVED:
        return "—"

    value = difference.before if before else difference.after
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "yes" if value else "no"
    if isinstance(value, str):
        return value
    return json.dumps(
        value,
        allow_nan=False,
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    )


def _display_name(name: str | None) -> str:
    if name is None:
        return "—"
    normalized = _WHITESPACE.sub(" ", name).strip()
    return normalized or "—"
