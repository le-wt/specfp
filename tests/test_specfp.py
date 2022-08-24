"""Test the top level specfp package as well as its CLI entry-points."""

from specfp import __version__, cli

import pytest
import tempfile


def test_version():
    """Double check package version."""
    assert __version__ == "0.0.0"


@pytest.mark.integration
def test_version_pyproject():
    """Package version should match the pyproject version."""
    with open("pyproject.toml", "r") as file:
        for line in file:
            parts = line.split()
            if parts[0] == "version":
                version = parts[2].replace('"', '')
                break
        else:
            raise ValueError("Couldn't find version in pyproject.toml")
    assert __version__ == version


class TestCLI:
    """A command-line interface for invoking various utilities."""

    def test_help(self, CLI):
        """Invoke the CLI without an error code."""
        assert CLI.invoke(cli.main).exit_code == 0
        assert CLI.invoke(cli.convert).exit_code == 2

    @pytest.mark.integration
    def test_convert(self, CLI):
        """Invoke the convert command on valid and invalid WDF files."""
        convert = CLI.invoke(
            cli.convert,
            ["tests/WDF/empty.wdf", "-q"])
        assert convert.exit_code == 1
        cmd = ["tests/WDF/single.wdf"]
        convert = CLI.invoke(cli.convert, cmd)
        assert convert.exit_code == 0
        with tempfile.TemporaryDirectory() as tmp:
            cmd.extend(["-o", f"{tmp}/output.csv"])
            convert = CLI.invoke(cli.convert, cmd)
            assert convert.exit_code == 0
