"""Utility functions for converting between various data types."""

from __future__ import annotations
from pathlib import Path
from typing import BinaryIO

import calendar
import datetime as dt
import fsspec

MS_ORIGIN = 116444736000000000  # January 1, 1970
MS_PRECISION = 10000000  # hundreds of nanoseconds


def datetime(filetime: int) -> dt.datetime:
    """Convert a Microsoft Windows File-time to a UTC datetime."""
    timestamp = (filetime - MS_ORIGIN) / MS_PRECISION
    return dt.datetime.utcfromtimestamp(timestamp)


def filetime(datetime: dt.datetime) -> int:
    """Convert UTC datetie to a Microsoft Windows File-time."""
    timestamp = calendar.timegm(datetime.utctimetuple())
    return timestamp * MS_PRECISION + MS_ORIGIN


def bitstream(urlpath: str | Path | BinaryIO):
    """Load a bitstream for reading from a path if necessary."""
    if isinstance(urlpath, (str, Path)):
        return fsspec.open(str(urlpath), mode="rb").open()
    return urlpath
