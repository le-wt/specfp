"""Decoders for various Raman spectroscopy file types."""

from . import wdf

import pandas as pd

__all__ = ["wdf", "load"]


def load(urlpath: str):
    """Load a Raman spectroscopy file.

    Args:
        urlpath: a WDF file path.

    Returns:
        the spectra as a dataframe with columns as wavelengths and rows as
        individual spectrum.
    """
    decoder = wdf.WDF(urlpath)
    decoder.decode()  # type: ignore
    df = pd.DataFrame(decoder.spectra, columns=decoder.wavelengths)
    df.index.name = "spectrum"
    return df
