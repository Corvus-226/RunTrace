"""Tests for package metadata consistency."""

from importlib.metadata import version

from runtrace import __version__


def test_installed_distribution_matches_package_version() -> None:
    assert version("ml-runtrace") == __version__
