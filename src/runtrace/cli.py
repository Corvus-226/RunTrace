"""Command-line entry point for RunTrace."""

from typing import Annotated

import typer

from runtrace import __version__

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


def main() -> None:
    """Run the command-line application."""
    app()
