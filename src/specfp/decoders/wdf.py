"""Decode WDF format produced by the Renishaw system for Raman spectroscopy."""

from __future__ import annotations
from construct import this
from .. import converters as to

import enum
import construct


Unused = construct.Computed(construct.Byte[this.header.size - this._sizing])


AXIS = construct.Struct(
    "type" / construct.Int32ul,
    "unit" / construct.Int32ul,
    "domain" / construct.Float32l)


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
        construct.Byte[4 - string.sizeof()],
        "uid" / construct.Int32ul,
        "size" / construct.Int64ul)


def Default(
        magic: bytes | None = None,
        payload: str = "payload",
        type: construct.Construct = construct.Byte,
) -> construct.Construct:
    """Construct a default block decoder with a length 4 magic string.

    Args:
        magic: a length 4 ascii-encoded string that identifies the block type.
        payload: the name of the payload field in the decoded dict.
        type: the data type encoding of the block's payload.

    Returns:
        a byte stream decoder.
    """
    header = Header(magic)
    return construct.Struct(
        "header" / header,
        payload / type[(this.header.size - header.sizeof()) // type.sizeof()],
        "unused" / Unused)


class Block(enum.Enum):
    """Decoding information for each WDF block type."""

    WDF1 = construct.Struct(
        "header"            / Header(b"WDF1"),
        "signature"         / construct.Int32ul,
        "version"           / construct.Int32ul,
        "size"              / construct.Int32ul,
        "uuid"              / construct.Int32ul[0x4],
        "unused"            / construct.Int64ul,
        "unused"            / construct.Int32ul,
        "tracks"            / construct.Int32ul,
        "points"            / construct.Int32ul,
        "capacity"          / construct.Int64ul,
        "count"             / construct.Int64ul,
        "accumulation"      / construct.Int32ul,
        "y_length"          / construct.Int32ul,
        "x_length"          / construct.Int32ul,
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
    DATA = Default(b"DATA", payload="spectra", type=construct.Float32l)
    YLST = construct.Struct(
        "header"            / Header(b"YLST"),
        "axis"              / AXIS,
        "unused"            / Unused)
    XLST = construct.Struct(
        "header"            / Header(b"XLST"),
        "axis"              / AXIS,
        "unused"            / Unused)
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
