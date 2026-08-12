"""Command-line entry point for RunTrace."""

from pathlib import Path
from typing import Annotated

import typer

from runtrace import __version__
from runtrace.config import ConfigLoadError
from runtrace.git import GitMetadataError
from runtrace.project import ProjectInitializationError, initialize_project
from runtrace.snapshot import SnapshotCaptureError, create_snapshot
from runtrace.storage import SnapshotStorageError

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
        typer.echo(f"runtrace {__version__}")
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


def main() -> None:
    """Run the command-line application."""
    app()
