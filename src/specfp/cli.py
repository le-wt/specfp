"""Provide the command-line interface for the specfp toolkit."""

import click

from . import __version__, decoders


@click.group()
@click.version_option(version=__version__)
def main():
    """Spectroscopy band fingerprinting."""


@main.command()
@click.argument("urlpath")
def convert(urlpath: str):
    """Convert a WDF spectroscopy file."""
    print(decoders.load(urlpath))
