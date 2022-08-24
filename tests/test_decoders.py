"""Read spectra data stored in different file formats."""

from datetime import datetime
from specfp import decoders, converters

import construct
import io
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

    def test_urlpath(self):
        """WDF can also accept an already opened file stream."""
        decoders.wdf.WDF(io.BytesIO(b""))

    def test_decoding(self):
        """Success is decoding a single block."""
        data = b"TEXT\x00\x00\x00\x00\x10\x00\x00\x00\x00\x00\x00\x00"
        decoder = decoders.wdf.WDF(io.BytesIO(data))
        decoder.decode()
        assert "TEXT" in decoder.blocks

    def test_missing_blocks(self):
        """Without a DATA block, spectra cannot be returned."""
        decoder = decoders.wdf.WDF(io.BytesIO(b""))
        with pytest.raises(RuntimeError):
            decoder.spectra
        with pytest.raises(RuntimeError):
            decoder.wavelengths
        decoder.decode()
        with pytest.raises(AttributeError):
            decoder.spectra
        with pytest.raises(AttributeError):
            decoder.wavelengths

    @pytest.mark.integration
    def test_raw(self, wdf_stream):
        """The entire file can be decoded as a series of byte blocks."""
        decoder = decoders.wdf.Default()
        while True:
            try:
                block = decoder.parse_stream(wdf_stream)
            except construct.core.StreamError:
                break
            else:
                decoders.wdf.Block[block.header.magic]

    @pytest.mark.integration
    def test_file_blocks(self, wdf_stream):
        """WDF contain at minium a WDF1, a DATA, a YLST and an XLST block."""
        decoder = decoders.wdf.Block.WDF1.value
        WDF1 = decoder.parse_stream(wdf_stream)
        assert WDF1.header.size == 512
        decoder = decoders.wdf.Block.DATA.value
        size = WDF1.count * WDF1.points
        DATA = decoder.parse_stream(wdf_stream, size=size)
        assert size == len(DATA.payload)
        payload = decoder.payload.subcon.subcon.sizeof() * size
        unused = len(DATA.unused)
        header = decoder.header.sizeof()
        assert DATA.header.size == header + payload + unused
        decoder = decoders.wdf.Block.YLST.value
        size = WDF1.YLST
        decoder.parse_stream(wdf_stream, size=size)
        decoder = decoders.wdf.Block.XLST.value
        size = WDF1.XLST
        XLST = decoder.parse_stream(wdf_stream, size=size)
        assert len(XLST.domain) == WDF1.points

    @pytest.mark.integration
    def test_file_decoder(self, wdf_stream):
        """A higher level API for extracting spectra from WDF files."""
        decoder = decoders.wdf.WDF(wdf_stream)
        decoder.decode()
        assert decoder.spectra.shape[1] == len(decoder.wavelengths)

    def test_partial_block(self):
        """Decoder should not fail if encountering a partial block."""
        data = b"TEXT\x00\x00\x00\x00\x10\x00\x00\x00\x00\x00\x00\x00"
        decoder = decoders.wdf.WDF(io.BytesIO(data[:2]))
        decoder.decode()
        decoder = decoders.wdf.WDF(io.BytesIO(data[:-1]))
        with pytest.raises(construct.core.StreamError):
            decoder.decode()

    @pytest.mark.integration
    def test_file_loader(self, wdf_stream):
        """A generic API for extracting spectra from spectroscopy files."""
        spectra = decoders.load(wdf_stream)
        assert spectra.index.name == "spectrum"
        assert spectra.shape == (10, 1021)

    @pytest.mark.integration
    def test_build(self, wdf_stream):
        """WDF blocks can be used both to decode and to encode."""
        decoder = decoders.wdf.Default()
        binary = wdf_stream.read()
        wdf_stream.seek(0)
        blocks = []
        while True:
            try:
                blocks.append(decoder.parse_stream(wdf_stream))
            except construct.core.StreamError:
                break
        encoded = b''.join([decoder.build(block) for block in blocks])
        assert encoded == binary
