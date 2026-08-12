"""Tests for the RunTrace command-line skeleton."""

from typer.testing import CliRunner

from runtrace import __version__
from runtrace.cli import app

runner = CliRunner()


def test_help_describes_runtrace() -> None:
    result = runner.invoke(app, ["--help"])

    assert result.exit_code == 0
    assert "Capture and compare" in result.stdout


def test_version_reports_package_version() -> None:
    result = runner.invoke(app, ["--version"])

    assert result.exit_code == 0
    assert result.stdout.strip() == f"runtrace {__version__}"
