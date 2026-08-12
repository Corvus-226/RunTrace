"""Command-line entry point for RunTrace."""

from pathlib import Path
from typing import Annotated

import typer

from runtrace import __version__
from runtrace.project import ProjectInitializationError, initialize_project

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


def main() -> None:
    """Run the command-line application."""
    app()
