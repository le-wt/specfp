"""Read spectra data stored in different file formats."""

from datetime import datetime
from specfp import decoders, converters

import construct
import pytest


@pytest.fixture
def wdf_stream():
    """A sample WDF file in the tests directory."""
    with open("tests/WDF/single.wdf", "rb") as file:
        yield file


def test_filetime():
    """Microsoft Windows has their own representation of a UTC datetime."""
    time = datetime.now().replace(microsecond=0)
    assert time == converters.datetime(converters.filetime(time))


def test_filetime_adapter():
    """Microsoft Windows's File-time is a 64 usigned little-endian integer."""
    time = datetime.now().replace(microsecond=0)
    adapter = decoders.wdf.FiletimeAdapter(construct.Int64ul)
    assert time == adapter.parse(adapter.build(time))


class TestWDF:
    """Read a WDF (.wdf) file."""

    def test_WDF1(self, wdf_stream):
        """All WDF files start with a WDF1 header block."""
        decoder = decoders.wdf.Block.WDF1.value
        block = decoder.parse_stream(wdf_stream)
        assert block.header.size == 512

    def test_DATA(self, wdf_stream):
        """WDF files usually have a DATA block after the WDF1 block."""
        self.test_WDF1(wdf_stream)
        decoder = decoders.wdf.Block.DATA.value
        decoder.parse_stream(wdf_stream)

    def test_optional_blocks(self, wdf_stream):
        """All subsequent blocks are have their size encoded in bytes."""
        self.test_DATA(wdf_stream)
        decoder = decoders.wdf.Default()
        while True:
            try:
                block = decoder.parse_stream(wdf_stream)
            except construct.core.StreamError:
                break
            else:
                decoders.wdf.Block[block.header.magic]
