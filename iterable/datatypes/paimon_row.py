"""Apache Paimon Row (``.row``) format support.

Implements the published Paimon Row binary layout
(https://paimon.apache.org/docs/master/concepts/spec/rowformat/) for standalone
files. Schema is not stored in the file and must be supplied on read.
"""

from __future__ import annotations

import struct
import typing
from typing import Any

try:
    import zstandard as zstd

    HAS_ZSTD = True
except ImportError:
    HAS_ZSTD = False

from ..base import BaseCodec, BaseFileIterable
from ..exceptions import ReadError
from ..types import Row

DEFAULT_BLOCK_SIZE = 64 * 1024
FOOTER_SIZE = 32
ROW_MAGIC = b"ROWS"
FORMAT_VERSION = 1

_TYPE_ALIASES: dict[str, str] = {
    "boolean": "boolean",
    "bool": "boolean",
    "tinyint": "tinyint",
    "int8": "tinyint",
    "byte": "tinyint",
    "smallint": "smallint",
    "int16": "smallint",
    "short": "smallint",
    "int": "int",
    "integer": "int",
    "int32": "int",
    "date": "date",
    "time": "time",
    "bigint": "bigint",
    "int64": "bigint",
    "long": "bigint",
    "float": "float",
    "float32": "float",
    "double": "double",
    "float64": "double",
    "string": "string",
    "str": "string",
    "varchar": "string",
    "char": "string",
    "binary": "binary",
    "bytes": "binary",
    "varbinary": "binary",
}


def _require_zstd() -> None:
    if not HAS_ZSTD:
        raise ImportError(
            "Paimon Row format support requires the 'zstandard' package. "
            "Install with: pip install iterabledata[paimon-row]"
        )


def _encode_varint(value: int) -> bytes:
    if value < 0:
        raise ValueError("varint requires a non-negative integer")
    out = bytearray()
    while True:
        bits = value & 0x7F
        value >>= 7
        out.append(bits | (0x80 if value else 0))
        if not value:
            break
    return bytes(out)


def _decode_varint(data: bytes, offset: int) -> tuple[int, int]:
    result = 0
    shift = 0
    while True:
        if offset >= len(data):
            raise ValueError("Truncated varint")
        byte = data[offset]
        offset += 1
        result |= (byte & 0x7F) << shift
        if not (byte & 0x80):
            return result, offset
        shift += 7
        if shift > 70:
            raise ValueError("Varint too long")


def _zigzag_encode(n: int) -> int:
    return (n << 1) ^ (n >> 63)


def _zigzag_decode(n: int) -> int:
    return (n >> 1) ^ (-(n & 1))


def _encode_delta_array(values: list[int]) -> bytes:
    if not values:
        return _encode_varint(0)
    deltas: list[int] = [values[0]]
    for i in range(1, len(values)):
        deltas.append(values[i] - values[i - 1])
    payload = b"".join(_encode_varint(_zigzag_encode(d)) for d in deltas)
    return _encode_varint(len(payload)) + payload


def _decode_delta_array(data: bytes, offset: int, count: int) -> tuple[list[int], int]:
    byte_len, offset = _decode_varint(data, offset)
    end = offset + byte_len
    values: list[int] = []
    prev = 0
    while offset < end:
        zz, offset = _decode_varint(data, offset)
        delta = _zigzag_decode(zz)
        prev = prev + delta
        values.append(prev)
    if len(values) != count:
        raise ValueError(f"Block index array length mismatch: expected {count}, got {len(values)}")
    return values, offset


def _normalize_field_type(raw: str) -> str:
    key = raw.strip().lower()
    if key not in _TYPE_ALIASES:
        raise ValueError(
            f"Unsupported Paimon Row field type '{raw}'. Supported: {', '.join(sorted(set(_TYPE_ALIASES.values())))}"
        )
    return _TYPE_ALIASES[key]


def normalize_schema(schema: Any) -> list[tuple[str, str]]:
    """Normalize a user-supplied schema into ``[(name, type), ...]``."""
    if schema is None:
        raise ValueError(
            "Paimon Row reads require an explicit schema via iterableargs={'schema': ...}. "
            "The .row format does not embed schema metadata."
        )
    if hasattr(schema, "names") and hasattr(schema, "types"):
        # pyarrow.Schema
        out: list[tuple[str, str]] = []
        for name, typ in zip(schema.names, schema.types, strict=True):
            type_name = str(typ).lower()
            if type_name.startswith("timestamp"):
                type_name = "bigint"
            elif type_name in {"string", "utf8", "large_string"}:
                type_name = "string"
            elif type_name in {"binary", "large_binary"}:
                type_name = "binary"
            elif type_name.startswith("int64") or type_name == "int64":
                type_name = "bigint"
            elif type_name.startswith("int32"):
                type_name = "int"
            elif type_name.startswith("int16"):
                type_name = "smallint"
            elif type_name.startswith("int8"):
                type_name = "tinyint"
            elif type_name == "bool" or type_name == "boolean":
                type_name = "boolean"
            elif type_name.startswith("float64") or type_name == "double":
                type_name = "double"
            elif type_name.startswith("float32") or type_name == "float":
                type_name = "float"
            out.append((name, _normalize_field_type(type_name)))
        return out
    if isinstance(schema, dict):
        return [(str(k), _normalize_field_type(str(v))) for k, v in schema.items()]
    if not isinstance(schema, (list, tuple)) or not schema:
        raise ValueError(
            "schema must be a non-empty list of (name, type) pairs, a name->type mapping, or a pyarrow.Schema"
        )
    out = []
    for item in schema:
        if isinstance(item, dict):
            name = item.get("name")
            typ = item.get("type")
            if name is None or typ is None:
                raise ValueError("schema dict entries must include 'name' and 'type'")
            out.append((str(name), _normalize_field_type(str(typ))))
        elif isinstance(item, (list, tuple)) and len(item) == 2:
            out.append((str(item[0]), _normalize_field_type(str(item[1]))))
        else:
            raise ValueError("schema entries must be (name, type) pairs or {'name','type'} dicts")
    return out


def _null_bitmap_size(arity: int) -> int:
    return (arity + 7) // 8


def _encode_value(typ: str, value: Any) -> bytes:
    if typ == "boolean":
        return b"\x01" if value else b"\x00"
    if typ == "tinyint":
        return struct.pack("<b", int(value))
    if typ == "smallint":
        return struct.pack("<h", int(value))
    if typ in {"int", "date", "time"}:
        return struct.pack("<i", int(value))
    if typ == "bigint":
        return struct.pack("<q", int(value))
    if typ == "float":
        return struct.pack("<f", float(value))
    if typ == "double":
        return struct.pack("<d", float(value))
    if typ == "string":
        raw = value if isinstance(value, (bytes, bytearray)) else str(value).encode("utf-8")
        return _encode_varint(len(raw)) + raw
    if typ == "binary":
        raw = bytes(value)
        return _encode_varint(len(raw)) + raw
    raise ValueError(f"Unsupported type for encode: {typ}")


def _decode_value(typ: str, data: bytes, offset: int) -> tuple[Any, int]:
    if typ == "boolean":
        return bool(data[offset]), offset + 1
    if typ == "tinyint":
        return struct.unpack_from("<b", data, offset)[0], offset + 1
    if typ == "smallint":
        return struct.unpack_from("<h", data, offset)[0], offset + 2
    if typ in {"int", "date", "time"}:
        return struct.unpack_from("<i", data, offset)[0], offset + 4
    if typ == "bigint":
        return struct.unpack_from("<q", data, offset)[0], offset + 8
    if typ == "float":
        return struct.unpack_from("<f", data, offset)[0], offset + 4
    if typ == "double":
        return struct.unpack_from("<d", data, offset)[0], offset + 8
    if typ == "string":
        length, offset = _decode_varint(data, offset)
        raw = data[offset : offset + length]
        return raw.decode("utf-8"), offset + length
    if typ == "binary":
        length, offset = _decode_varint(data, offset)
        return data[offset : offset + length], offset + length
    raise ValueError(f"Unsupported type for decode: {typ}")


def encode_row(schema: list[tuple[str, str]], record: dict[str, Any]) -> bytes:
    arity = len(schema)
    bitmap = bytearray(_null_bitmap_size(arity))
    parts: list[bytes] = []
    for i, (name, typ) in enumerate(schema):
        value = record.get(name, None)
        if value is None:
            bitmap[i // 8] |= 1 << (i % 8)
            continue
        parts.append(_encode_value(typ, value))
    return bytes(bitmap) + b"".join(parts)


def decode_row(schema: list[tuple[str, str]], data: bytes, offset: int = 0) -> tuple[dict[str, Any], int]:
    arity = len(schema)
    bitmap_size = _null_bitmap_size(arity)
    bitmap = data[offset : offset + bitmap_size]
    offset += bitmap_size
    row: dict[str, Any] = {}
    for i, (name, typ) in enumerate(schema):
        if bitmap[i // 8] & (1 << (i % 8)):
            row[name] = None
            continue
        value, offset = _decode_value(typ, data, offset)
        row[name] = value
    return row, offset


def _compress(raw: bytes) -> bytes:
    _require_zstd()
    cctx = zstd.ZstdCompressor(level=1)
    return cctx.compress(raw)


def _decompress(raw: bytes, uncompressed_size: int) -> bytes:
    _require_zstd()
    dctx = zstd.ZstdDecompressor()
    return dctx.decompress(raw, max_output_size=uncompressed_size)


def pack_block(rows: list[bytes]) -> bytes:
    data_region = b"".join(rows)
    offsets = []
    cursor = 0
    for row in rows:
        offsets.append(cursor)
        cursor += len(row)
    offset_bytes = b"".join(struct.pack("<i", off) for off in offsets)
    return data_region + offset_bytes + struct.pack("<i", len(rows))


def unpack_block(raw: bytes) -> list[bytes]:
    if len(raw) < 4:
        raise ValueError("Corrupt row block: too short")
    row_count = struct.unpack_from("<i", raw, len(raw) - 4)[0]
    if row_count < 0:
        raise ValueError("Corrupt row block: negative row count")
    offset_start = len(raw) - 4 - (row_count * 4)
    if offset_start < 0:
        raise ValueError("Corrupt row block: invalid offset table")
    offsets = [struct.unpack_from("<i", raw, offset_start + i * 4)[0] for i in range(row_count)]
    rows: list[bytes] = []
    for i, start in enumerate(offsets):
        end = offsets[i + 1] if i + 1 < row_count else offset_start
        rows.append(raw[start:end])
    return rows


def pack_footer(
    total_row_count: int,
    block_count: int,
    index_offset: int,
    index_length: int,
    version: int = FORMAT_VERSION,
) -> bytes:
    return struct.pack(
        "<qiqiB3s4s",
        total_row_count,
        block_count,
        index_offset,
        index_length,
        version,
        b"\x00\x00\x00",
        ROW_MAGIC,
    )


def unpack_footer(data: bytes) -> dict[str, int]:
    if len(data) != FOOTER_SIZE:
        raise ValueError("Paimon Row footer must be exactly 32 bytes")
    total_row_count, block_count, index_offset, index_length, version, reserved, magic = struct.unpack(
        "<qiqiB3s4s", data
    )
    if magic != ROW_MAGIC:
        raise ValueError(f"Invalid Paimon Row magic: {magic!r}")
    if reserved != b"\x00\x00\x00":
        raise ValueError("Invalid Paimon Row footer reserved bytes")
    if version != FORMAT_VERSION:
        raise ValueError(f"Unsupported Paimon Row version: {version}")
    return {
        "total_row_count": total_row_count,
        "block_count": block_count,
        "index_offset": index_offset,
        "index_length": index_length,
        "version": version,
    }


def match_row_footer(footer: bytes) -> bool:
    """Return True if ``footer`` looks like a valid Paimon Row footer."""
    if len(footer) != FOOTER_SIZE or footer[-4:] != ROW_MAGIC:
        return False
    try:
        unpack_footer(footer)
        return True
    except ValueError:
        return False


class PaimonRowIterable(BaseFileIterable):
    """Paimon Row (``.row``) reader/writer.

    Memory behavior: reads one ZSTD-compressed block at a time; writes flush when
    the uncompressed block estimate reaches ``block_size``.
    """

    datamode = "binary"

    def __init__(
        self,
        filename: str | None = None,
        stream: typing.IO[Any] | None = None,
        mode: str = "r",
        codec: BaseCodec | None = None,
        schema: Any | None = None,
        block_size: int = DEFAULT_BLOCK_SIZE,
        options: dict[str, Any] | None = None,
    ):
        if options is None:
            options = {}
        else:
            options = dict(options)
        _require_zstd()
        # Pop format-specific keys so _apply_options does not overwrite normalized values.
        self.block_size = int(options.pop("block_size", block_size))
        raw_schema = options.pop("schema", schema)
        self.schema: list[tuple[str, str]] | None = normalize_schema(raw_schema) if raw_schema is not None else None
        self._write_buffer: list[bytes] = []
        self._write_bytes = 0
        self._blocks_meta: list[tuple[int, int, int]] = []  # compressed, uncompressed, row_start
        self._total_rows_written = 0
        self._file_bytes = bytearray()
        self._iterator: typing.Iterator[dict[str, Any]] | None = None
        self._footer: dict[str, int] | None = None
        self._file_data: bytes | None = None
        self.pos = 0
        # Manage file I/O ourselves (footer-based reads / whole-payload writes).
        super().__init__(filename, stream, codec=codec, mode=mode, binary=True, noopen=True, options=options)
        if mode == "r" and self.schema is None:
            raise ValueError(
                "Paimon Row reads require an explicit schema via iterableargs={'schema': ...}. "
                "The .row format does not embed schema metadata."
            )
        self.reset()

    def reset(self) -> None:
        super().reset()
        self.pos = 0
        self._iterator = None
        self._footer = None
        if self.mode == "r":
            if self.schema is None:
                raise ValueError("Paimon Row reads require an explicit schema via iterableargs={'schema': ...}.")
            self._iterator = self._iter_rows()
        elif self.mode == "w":
            self._write_buffer = []
            self._write_bytes = 0
            self._blocks_meta = []
            self._total_rows_written = 0
            self._file_bytes = bytearray()

    @staticmethod
    def id() -> str:
        return "paimon_row"

    @staticmethod
    def is_flatonly() -> bool:
        return True

    def is_streaming(self) -> bool:
        return True

    @staticmethod
    def has_totals() -> bool:
        return True

    def totals(self) -> int:
        if self.mode != "r":
            return self._total_rows_written
        footer = self._read_footer()
        return int(footer["total_row_count"])

    def _read_all_bytes(self) -> bytes:
        if self.filename:
            with open(self.filename, "rb") as f:
                return f.read()
        if self.fobj is None:
            raise ReadError(
                "Paimon Row reading requires a filename or stream",
                filename=None,
                error_code="RESOURCE_REQUIREMENT_NOT_MET",
            )
        pos = self.fobj.tell()
        self.fobj.seek(0)
        data = self.fobj.read()
        self.fobj.seek(pos)
        if not isinstance(data, (bytes, bytearray)):
            raise TypeError("Paimon Row requires a binary stream")
        return bytes(data)

    def _read_footer(self) -> dict[str, int]:
        if self._footer is not None:
            return self._footer
        data = self._read_all_bytes()
        if len(data) < FOOTER_SIZE:
            raise ValueError("File too short to be a Paimon Row file")
        self._footer = unpack_footer(data[-FOOTER_SIZE:])
        self._file_data = data
        return self._footer

    def _iter_rows(self) -> typing.Iterator[dict[str, Any]]:
        assert self.schema is not None
        data = self._read_all_bytes()
        if len(data) < FOOTER_SIZE:
            raise ValueError("File too short to be a Paimon Row file")
        footer = unpack_footer(data[-FOOTER_SIZE:])
        self._footer = footer
        index = data[footer["index_offset"] : footer["index_offset"] + footer["index_length"]]
        offset = 0
        compressed_sizes, offset = _decode_delta_array(index, offset, footer["block_count"])
        uncompressed_sizes, offset = _decode_delta_array(index, offset, footer["block_count"])
        _row_starts, offset = _decode_delta_array(index, offset, footer["block_count"])
        del _row_starts
        block_offsets: list[int] = []
        cursor = 0
        for size in compressed_sizes:
            block_offsets.append(cursor)
            cursor += size
        for block_i in range(footer["block_count"]):
            start = block_offsets[block_i]
            comp = data[start : start + compressed_sizes[block_i]]
            raw = _decompress(comp, uncompressed_sizes[block_i])
            for row_bytes in unpack_block(raw):
                row, _ = decode_row(self.schema, row_bytes, 0)
                yield row

    def read(self, skip_empty: bool = True) -> dict:
        if self._iterator is None:
            raise RuntimeError("Iterator not initialized. Call reset() first.")
        row = next(self._iterator)
        self.pos += 1
        return row

    def _ensure_write_schema(self, record: Row) -> None:
        if self.schema is not None:
            return
        # Infer string/int/float/bool/bytes from first record keys.
        inferred: list[tuple[str, str]] = []
        for key, value in record.items():
            if value is None:
                inferred.append((str(key), "string"))
            elif isinstance(value, bool):
                inferred.append((str(key), "boolean"))
            elif isinstance(value, int):
                inferred.append((str(key), "bigint"))
            elif isinstance(value, float):
                inferred.append((str(key), "double"))
            elif isinstance(value, (bytes, bytearray)):
                inferred.append((str(key), "binary"))
            else:
                inferred.append((str(key), "string"))
        self.schema = inferred

    def _flush_block(self) -> None:
        if not self._write_buffer:
            return
        raw = pack_block(self._write_buffer)
        compressed = _compress(raw)
        row_start = self._total_rows_written - len(self._write_buffer)
        self._blocks_meta.append((len(compressed), len(raw), row_start))
        self._file_bytes.extend(compressed)
        self._write_buffer = []
        self._write_bytes = 0

    def write(self, record: Row) -> None:
        self.write_bulk([record])

    def write_bulk(self, records: list[Row]) -> None:
        if not records:
            return
        for record in records:
            self._ensure_write_schema(record)
            assert self.schema is not None
            encoded = encode_row(self.schema, record)
            self._write_buffer.append(encoded)
            self._write_bytes += len(encoded)
            self._total_rows_written += 1
            if self._write_bytes >= self.block_size:
                self._flush_block()

    def flush(self) -> None:
        if self.mode == "w":
            self._flush_block()

    def close(self) -> None:
        if self.mode == "w":
            self._flush_block()
            # Build index + footer
            compressed_sizes = [m[0] for m in self._blocks_meta]
            uncompressed_sizes = [m[1] for m in self._blocks_meta]
            row_starts = [m[2] for m in self._blocks_meta]
            index = (
                _encode_delta_array(compressed_sizes)
                + _encode_delta_array(uncompressed_sizes)
                + _encode_delta_array(row_starts)
            )
            index_offset = len(self._file_bytes)
            payload = (
                bytes(self._file_bytes)
                + index
                + pack_footer(
                    self._total_rows_written,
                    len(self._blocks_meta),
                    index_offset,
                    len(index),
                )
            )
            if self.filename:
                with open(self.filename, "wb") as f:
                    f.write(payload)
            elif self.fobj is not None:
                self.fobj.write(payload)
            self._file_bytes = bytearray()
            self._blocks_meta = []
        super().close()
