"""Provide the command-line interface for the specfp toolkit."""

from __future__ import annotations
from loguru import logger
from pathlib import Path
from . import __version__, decoders

import click
import pandas as pd
import sys


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
    if quiet:
        level = 40
    else:
        level = max(25 - verbose * 10, 0)
    logger.remove()
    logger.add(
        sys.stderr,
        level=level,
        format=(
            "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> "
            "| <level>{level: <8}</level> "
            "| <level>{message}</level>"))
    spectra = decoders.load(urlpath).T
    if output:
        output.parent.mkdir(parents=True, exist_ok=True)
        spectra.to_csv(output)
    else:
        pd.set_option('display.max_rows', None)
        pd.set_option('display.max_columns', None)
        pd.set_option('display.width', None)
        print(spectra)
