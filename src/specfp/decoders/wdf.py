"""Decode WDF format produced by the Renishaw system for Raman spectroscopy."""

from __future__ import annotations
from construct import this
from loguru import logger
from typing import Callable, BinaryIO
from .. import converters as to

import attrs
import collections
import construct
import enum
import numpy as np
import transitions


class FiletimeAdapter(construct.Adapter):
    """Adapt between Microsoft Windows File-time and UTC datetime."""

    def _decode(self, obj, context, path):
        """Convert an integer to a UTC datetime."""
        return to.datetime(obj)

    def _encode(self, obj, context, path):
        """Convert a UTC datetime to an integer."""
        return to.filetime(obj)


def Header(magic: bytes | None = None) -> construct.Construct:
    """Construct a decoder for a block header with a length 4 magic string.

    Args:
        magic: a length 4 ascii-encoded string that identifies the block type.

    Returns:
        a byte stream decoder.
    """
    if magic is None:
        string = construct.PaddedString(4, "ascii")
    else:
        string = construct.Const(magic)
    return construct.Struct(
        "magic" / string,
        "padding" / construct.Byte[4 - string.sizeof()],
        "uid" / construct.Int32ul,
        "size" / construct.Int64ul)


def Default(
        magic: bytes | None = None,
        type: construct.Construct = construct.Byte,
) -> construct.Construct:
    """Construct a default block decoder with a length 4 magic string.

    Args:
        magic: a length 4 ascii-encoded string that identifies the block type.
        type: the data type encoding of the block's payload.

    Returns:
        a byte stream decoder.
    """
    header = Header(magic)
    length = (this.header.size - header.sizeof()) // type.sizeof()
    return construct.Struct(
        "header" / header,
        "payload" / type[length])


def AXIS(magic: bytes | None = None) -> construct.Construct:
    """Construct a block decoder for x and y axis data (XLST or YLST)."""
    header = Header(magic)
    length = this.header.size - header.sizeof() - (2 + this._.size) * 4
    return construct.Struct(
        "header" / header,
        "type" / construct.Int32ul,
        "unit" / construct.Int32ul,
        "domain" / construct.Float32l[this._.size],
        "unused" / construct.Byte[length])


class Block(enum.Enum):
    r"""Decoding information for each WDF block type.

    This information is useful to encode a dict containing the corresponding
    data into bytes, essentially allowing writing WDF files.

    Examples:
        >>> block = Block.TEXT.value
        >>> header = {'magic': b'TEXT', 'padding': '', 'uid': 0, 'size': 16}
        >>> bytes(block.build({'header': header, 'payload': []}))
        b'TEXT\x00\x00\x00\x00\x10\x00\x00\x00\x00\x00\x00\x00'
    """

    WDF1 = construct.Struct(
        "header"            / Header(b"WDF1"),
        "signature"         / construct.Int32ul,
        "version"           / construct.Int32ul,
        "size"              / construct.Int32ul,
        "uuid"              / construct.Int32ul[0x4],
        "unused0"           / construct.Int64ul,
        "unused1"           / construct.Int32ul,
        "tracks"            / construct.Int32ul,
        "points"            / construct.Int32ul,
        "capacity"          / construct.Int64ul,
        "count"             / construct.Int64ul,
        "accumulation"      / construct.Int32ul,
        "YLST"              / construct.Int32ul * "block length",
        "XLST"              / construct.Int32ul * "block length",
        "origin_length"     / construct.Int32ul,
        "application"       / construct.PaddedString(0x18, "ascii"),
        "major_version"     / construct.Int16ul,
        "minor_version"     / construct.Int16ul,
        "patch_version"     / construct.Int16ul,
        "build_version"     / construct.Int16ul,
        "scan_type"         / construct.Int32ul,
        "measurement_type"  / construct.Int32ul,
        "time_start"        / FiletimeAdapter(construct.Int64ul),
        "time_end"          / FiletimeAdapter(construct.Int64ul),
        "unit"              / construct.Int32ul,
        "wave_number"       / construct.Float32l,
        "spare"             / construct.Int64ul[0x6],
        "username"          / construct.PaddedString(0x20, "utf-8"),
        "title"             / construct.PaddedString(0xa0, "utf-8"),
        "padded"            / construct.Int64ul[0x6],
        "third_party"       / construct.Int64ul[0x4],
        "internal_use"      / construct.Int64ul[0x4])
    DATA = construct.Struct(
        "header" / Header(b"DATA"),
        "payload" / construct.Float32l[this._.size],
        "unused" / construct.Byte[
            lambda this: this.header.size
            - this._subcons.header.sizeof()
            - this._.size * construct.Float32l.sizeof()])
    YLST = AXIS(b"YLST")
    XLST = AXIS(b"XLST")
    ORGN = Default(b"ORGN") * "Origin"
    TEXT = Default(b"TEXT") * "Comment"
    WXDA = Default(b"WXDA") * "Wire data"
    WXDB = Default(b"WXDB") * "Dataset data"
    WXDM = Default(b"WXDM") * "Measurement"
    WXCS = Default(b"WXCS") * "Calibration"
    WXIS = Default(b"WXIS") * "Instrument"
    WMAP = Default(b"WMAP") * "Map area"
    WHTL = Default(b"WHTL") * "White light"
    NAIL = Default(b"NAIL") * "Thumbnail"
    MAP  = Default(b"MAP")  * "Map"
    CFAR = Default(b"CFAR") * "Curve fit"
    DCLS = Default(b"DCLS") * "Component"
    PCAR = Default(b"PCAR") * "PCA"
    MCRE = Default(b"MCRE") * "EM"
    ZLDC = Default(b"ZLDC") * "Zeldac"
    RCAL = Default(b"RCAL") * "Response cal"
    CAP  = Default(b"CAP")  * "Cap"
    WARP = Default(b"WARP") * "Processing"
    WARA = Default(b"WARA") * "Analysis"
    WLBL = Default(b"WLBL") * "Spectrum labels"
    WCHK = Default(b"WCHK") * "Checksum"
    RXCD = Default(b"RXCD") * "RX cal data"
    RXCF = Default(b"RXCF") * "RX cal fit"
    XCAL = Default(b"XCAL") * "Xcal"
    SRCH = Default(b"SRCH") * "Spec search"
    TEMP = Default(b"TEMP") * "Temp profile"
    UNCV = Default(b"UNCV") * "Unit convert"
    ARPR = Default(b"ARPR") * "Ar plate"
    ELEC = Default(b"ELEC") * "Electrical sign"
    BKXL = Default(b"BKXL") * "BKX list"
    AUX  = Default(b"AUX")  * "Auxiliary data"
    CHLG = Default(b"CHLG") * "Changelog"
    SURF = Default(b"SURF") * "Surface"
    PSET = Default(b"PSET") * "Stream is Pset"


@attrs.define(slots=False)
class WDF:
    """A WDF binary file format reader.

    WDF files contain (Raman) spectroscopy data in the form of one or more
    spectrum consisting of N different points per acquisition. The binary file
    contains a sequence of blocks, each of which is composed of a header and
    its payload.

    Args:
        stream: the WDF local or remote file path or opened binary stream.

    Methods:
        decode: decode all of the detected WDF blocks.
        close: close the opened WDF bitstream.

    Attributes:
        blocks: an ordered mapping of block name to decoded data.
        decoders: an ordered mapping of block name to the decoding construct.
        states: the available decoding states (registered block decoders).
        spectra: the decoded spectra points data.
        wavelengths: the decoded x-axis data.

    Examples:
        >>> decoder = WDF('tests/WDF/single.wdf')
        >>> decoder.decode()
        True
        >>> list(decoder.blocks.keys())[:2]
        ['WDF1', 'DATA']
    """

    stream: str | BinaryIO = attrs.field(converter=to.bitstream)

    def __attrs_pre_init__(self):
        """Initialize the Finite State Machine controller."""
        self.machine = transitions.Machine(
            states=[block.name for block in Block],
            prepare_event="_identify",
            after_state_change="_log",
            auto_transitions=False,
            queued=True,
            model=self)

    def __attrs_post_init__(self):
        """Open the WDF bitstream and configure the state transitions."""
        self.blocks = collections.OrderedDict()
        self.decoders = collections.OrderedDict()
        self.close = self.stream.close
        for block in Block:
            self.machine.add_transition(
                "decode",
                conditions=self.identified(block.name),
                source=list(self.machine.states),
                dest=block.name,
                after="decode")
            getattr(self.machine, f"on_enter_{block.name}")("_decode")

    @property
    def spectra(self) -> np.ndarray:
        """One or more Raman shift points data (cm-1)."""
        if not len(self.blocks):
            error = "Unprocessed input stream, hint: call decode() first!"
            raise RuntimeError(error)
        try:
            shape = self.blocks["WDF1"].count, self.blocks["WDF1"].points
            return np.reshape(self.blocks["DATA"].payload, shape)
        except KeyError:
            raise AttributeError("Missing DATA/WDF1 blocks, spectra not found")

    @property
    def wavelengths(self) -> np.ndarray:
        """The x-axis of the spectral measurements (nm)."""
        if not len(self.blocks):
            error = "Unprocessed input stream, hint: call decode() first!"
            raise RuntimeError(error)
        try:
            return np.array(self.blocks["XLST"].domain)
        except KeyError:
            raise AttributeError("Missing XLST blocks, wavelengths not found")

    def identified(self, block: str) -> Callable[[], bool]:
        """Return a thunk that checks what the next block is to be decoded.

        This utility method is useful to call once the next block has been
        identified but the current reader's state still hasn't transitioned
        yet. Once the transition occurs, the thunk is equivalent to the
        matching "is_<state>" method that already exists since the current
        state and the most redecently decoded block are the same.
        """
        def is_block() -> bool:
            """Check if the next block matches the closure variable "block"."""
            return next(reversed(self.blocks)) == block
        return is_block

    def _identify(self):
        """Peek at the next 4 bytes of the stream to identify the block."""
        magic = construct.Peek(Header().magic).parse_stream(self.stream)
        self.blocks[magic] = None
        logger.log(
            "SUCCESS" if magic in self.machine.states else "WARNING",
            f"Identified block: {magic}")

    def _decode(self):
        """Decode a single WDF block's header and payload from the stream."""
        self.decoders[self.state] = decoder = Block[self.state].value
        ctx = {}
        if "WDF1" in self.blocks:
            metadata = self.blocks["WDF1"]
            if self.state in ("XLST", "YLST"):
                ctx["size"] = metadata[self.state]
            elif self.state == "DATA":
                ctx["size"] = metadata.count * metadata.points
        self.blocks[self.state] = decoder.parse_stream(self.stream, **ctx)

    def _log(self):
        """Log the current decoded block information."""
        block_size = self.blocks[self.state].header.size
        header_size = self.decoders[self.state].header.sizeof()
        logger.info(
            f"Decoded block: {self.state}"
            f"(payload = {block_size - header_size}/{block_size} bytes)")
