"""Decoders for various Raman spectroscopy file types."""

from __future__ import annotations
from loguru import logger
from pathlib import Path
from typing import BinaryIO
from . import wdf

import pandas as pd
import sys

__all__ = ["wdf", "load"]


def load(urlpath: str | Path | BinaryIO, *, verbose: int = 1):
    """Load a Raman spectroscopy file.

    Args:
        urlpath: a WDF file path or binary stream.
        verbose: set the logging level (default to success).

    Returns:
        the spectra as a dataframe with columns as wavelengths and rows as
        individual spectrum.
    """
    if verbose:
        level = max(25 - verbose * 10, 0)
    else:
        level = 40
    logger.remove()
    logger.add(
        sys.stderr,
        level=level,
        format=(
            "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> "
            "| <level>{level: <8}</level> "
            "| <level>{message}</level>"))
    decoder = wdf.WDF(urlpath)
    decoder.decode()  # type: ignore
    df = pd.DataFrame(decoder.spectra, columns=decoder.wavelengths)
    df.index.name = "spectrum"
    return df
