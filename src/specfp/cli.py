"""Provide the command-line interface for the specfp toolkit."""

from __future__ import annotations
from loguru import logger
from pathlib import Path
from . import __version__, decoders, dashboard

import click
import pandas as pd


@click.group()
@click.version_option(version=__version__)
def main():
    """Spectroscopy band fingerprinting."""


@main.command()
@click.argument("urlpath")
@click.option("-o", "--output", type=Path, default=None)
@click.option("-v", "--verbose", count=True)
@click.option("-q", "--quiet", is_flag=True, default=False)
def convert(
        urlpath: str,
        output: Path | None = None,
        verbose: int = 0,
        quiet: bool = False):
    """Convert a WDF spectroscopy file."""
    spectra = decoders.load(urlpath, verbose=0 if quiet else verbose + 1).T
    if output:
        output.parent.mkdir(parents=True, exist_ok=True)
        spectra.to_csv(output)
    else:
        pd.set_option('display.max_rows', None)
        pd.set_option('display.max_columns', None)
        pd.set_option('display.width', None)
        print(spectra)


@main.command()
@click.option("-p", "--port", type=int, default=8050)
def dash(port: int = 8050):
    """Run the web dashboard for spectroscopy band analysis."""
    dashboard.app.run_server(debug=True, port=port)
