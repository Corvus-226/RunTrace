"""Command-line entry point for RunTrace."""

from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console

from ml_runtrace import __version__
from ml_runtrace.config import ConfigLoadError
from ml_runtrace.diff import compare_snapshots
from ml_runtrace.git import GitMetadataError
from ml_runtrace.presentation import (
    print_snapshot,
    print_snapshot_comparison,
    print_snapshot_list,
)
from ml_runtrace.project import (
    ProjectInitializationError,
    initialize_project,
    require_initialized_project,
)
from ml_runtrace.snapshot import SnapshotCaptureError, create_snapshot
from ml_runtrace.storage import SnapshotStorageError, SnapshotStore

app = typer.Typer(
    help=(
        "Capture and compare the code, configuration, environment, and metadata "
        "behind machine-learning experiments."
    ),
    no_args_is_help=True,
)


def _show_version(value: bool) -> None:
    """Print the package version and exit."""
    if value:
        typer.echo(f"ml-runtrace {__version__}")
        raise typer.Exit


@app.callback()
def cli(
    version: Annotated[
        bool,
        typer.Option(
            "--version",
            callback=_show_version,
            is_eager=True,
            help="Show the installed version and exit.",
        ),
    ] = False,
) -> None:
    """RunTrace command group."""


@app.command("init")
def init_project() -> None:
    """Initialize RunTrace in the current Git repository."""
    try:
        project_root = initialize_project(Path.cwd())
    except ProjectInitializationError as error:
        typer.echo(f"Error: {error}", err=True)
        raise typer.Exit(code=1) from error

    typer.echo("Initialized RunTrace in current repository.")
    typer.echo(f"Project: {project_root}")


@app.command("snapshot")
def snapshot_command(
    name: Annotated[
        str | None,
        typer.Option("--name", help="Human-readable name for this run."),
    ] = None,
    config: Annotated[
        Path | None,
        typer.Option("--config", help="YAML experiment config to capture."),
    ] = None,
    command: Annotated[
        str | None,
        typer.Option("--command", help="Command used to run the experiment."),
    ] = None,
) -> None:
    """Capture and persist the current experiment context."""
    try:
        saved = create_snapshot(
            Path.cwd(),
            name=name,
            config_path=config,
            command=command,
        )
    except (
        ConfigLoadError,
        GitMetadataError,
        ProjectInitializationError,
        SnapshotCaptureError,
        SnapshotStorageError,
    ) as error:
        typer.echo(f"Error: {error}", err=True)
        raise typer.Exit(code=1) from error

    typer.echo(f"Created snapshot {saved.snapshot.run_id}.")
    typer.echo(f"Path: {saved.path}")


@app.command("list")
def list_command() -> None:
    """List locally recorded experiment runs, newest first."""
    try:
        project_root = require_initialized_project(Path.cwd())
        snapshots = SnapshotStore(project_root).list_snapshots()
    except (ProjectInitializationError, SnapshotStorageError) as error:
        typer.echo(f"Error: {error}", err=True)
        raise typer.Exit(code=1) from error

    print_snapshot_list(snapshots, Console(highlight=False))


@app.command("show")
def show_command(
    run_id: Annotated[
        str,
        typer.Argument(help="Full or unique abbreviated run ID."),
    ],
) -> None:
    """Show the complete stored record for one experiment run."""
    try:
        project_root = require_initialized_project(Path.cwd())
        snapshot = SnapshotStore(project_root).load(run_id)
    except (ProjectInitializationError, SnapshotStorageError) as error:
        typer.echo(f"Error: {error}", err=True)
        raise typer.Exit(code=1) from error

    print_snapshot(snapshot, Console(highlight=False))


@app.command("diff")
def diff_command(
    run_a: Annotated[
        str,
        typer.Argument(help="First full or unique abbreviated run ID."),
    ],
    run_b: Annotated[
        str,
        typer.Argument(help="Second full or unique abbreviated run ID."),
    ],
) -> None:
    """Compare reproducibility values in two stored experiment runs."""
    try:
        project_root = require_initialized_project(Path.cwd())
        store = SnapshotStore(project_root)
        before = store.load(run_a)
        after = store.load(run_b)
    except (ProjectInitializationError, SnapshotStorageError) as error:
        typer.echo(f"Error: {error}", err=True)
        raise typer.Exit(code=1) from error

    comparison = compare_snapshots(before, after)
    print_snapshot_comparison(comparison, Console(highlight=False))


def main() -> None:
    """Run the command-line application."""
    app()
