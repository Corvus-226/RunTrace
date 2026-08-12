"""Rich terminal presentation for RunTrace snapshot data."""

from __future__ import annotations

import re
from collections.abc import Sequence
from datetime import timezone

from rich import box
from rich.console import Console
from rich.table import Table
from rich.text import Text

from runtrace.models import Snapshot

_WHITESPACE = re.compile(r"\s+")


def print_snapshot_list(snapshots: Sequence[Snapshot], console: Console) -> None:
    """Print a compact newest-first summary of persisted snapshots."""
    if not snapshots:
        console.print(
            "No snapshots recorded yet. Run `runtrace snapshot` to create one."
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


def _display_name(name: str | None) -> str:
    if name is None:
        return "—"
    normalized = _WHITESPACE.sub(" ", name).strip()
    return normalized or "—"
