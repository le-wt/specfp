"""Test the top level specfp package as well as its CLI entry-points."""

from specfp import __version__, cli

import click.testing
import pytest


@pytest.fixture
def CLI():
    """Runner for the click CLI."""
    return click.testing.CliRunner()


def test_version():
    """Ensure that the package version matches the pyproject version."""
    with open("pyproject.toml", "r") as file:
        for line in file:
            parts = line.split()
            if parts[0] == "version":
                version = parts[2].replace('"', '')
                break
        else:
            raise ValueError("Couldn't find version in pyproject.toml")
    assert __version__ == version == "0.0.0"


def test_cli(CLI):
    """Invoke the CLI without an error code."""
    assert CLI.invoke(cli.main).exit_code == 0
