"""Provide the command-line interface for the specfp toolkit."""

import click

from . import __version__


@click.command()
@click.version_option(version=__version__)
def main():
    """Spectroscopy band fingerprinting."""
