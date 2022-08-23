"""Read spectra data stored in different file formats."""

from datetime import datetime
from specfp import decoders, converters

import construct
import pytest


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

    @pytest.mark.integration
    def test_WDF1(self, wdf_stream):
        """All WDF files start with a WDF1 header block."""
        block = decoders.wdf.Block.WDF1.value.parse_stream(wdf_stream)
        assert block.header.size == 512

    @pytest.mark.integration
    def test_DATA(self, wdf_stream):
        """WDF files usually have a DATA block after the WDF1 block."""
        decoders.wdf.Block.WDF1.value.parse_stream(wdf_stream)
        decoders.wdf.Block.DATA.value.parse_stream(wdf_stream)

    @pytest.mark.integration
    def test_optional_blocks(self, wdf_stream):
        """All subsequent blocks are have their size encoded in bytes."""
        decoder = decoders.wdf.Default()
        while True:
            try:
                block = decoder.parse_stream(wdf_stream)
            except construct.core.StreamError:
                break
            else:
                decoders.wdf.Block[block.header.magic]
