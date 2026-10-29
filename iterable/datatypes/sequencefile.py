from __future__ import annotations

import base64
import json
import os
import struct
import typing
from collections.abc import Callable
from typing import Any

from ..base import ITERABLE_TYPE_CODEC, BaseCodec, BaseFileIterable
from ..exceptions import FormatParseError
from ..helpers.jsonbackend import make_encoder
from ..helpers.jsonvalues import json_default_from_options
from ..types import Row

# Hadoop SequenceFile layout (uncompressed):
#   header: b"SEQ" + version byte, key and value class names (Text), compression and
#           block-compression flags, metadata (int count + Text pairs), 16-byte sync marker
#   record: int record length, int key length, key bytes, value bytes
#   sync:   int -1 followed by the sync marker, between records every few hundred kilobytes
HADOOP_MAGIC = b"SEQ"
HADOOP_VERSION = 6
# Oldest version with Text class names and a block-compression flag.
MIN_HADOOP_VERSION = 4
# Version that added the metadata block.
METADATA_VERSION = 6
SYNC_ESCAPE = -1
SYNC_HASH_SIZE = 16

TEXT_CLASS = "org.apache.hadoop.io.Text"
BYTES_CLASS = "org.apache.hadoop.io.BytesWritable"
INT_CLASS = "org.apache.hadoop.io.IntWritable"
LONG_CLASS = "org.apache.hadoop.io.LongWritable"
NULL_CLASS = "org.apache.hadoop.io.NullWritable"


def _encode_vint(value: int) -> bytes:
    """Encode an int as a Hadoop ``WritableUtils`` variable-length integer."""
    if -112 <= value <= 127:
        return struct.pack(">b", value)
    marker = -112
    if value < 0:
        value ^= -1
        marker = -120
    size = (value.bit_length() + 7) // 8
    return struct.pack(">b", marker - size) + value.to_bytes(size, "big")


def _vint_size(first: int) -> int:
    """Return the total encoded size of a vint from its signed first byte."""
    if first >= -112:
        return 1
    if first < -120:
        return -119 - first
    return -111 - first


def _decode_vint(data: bytes) -> int:
    """Decode a complete Hadoop vint (first byte plus its value bytes)."""
    first = int.from_bytes(data[:1], "big", signed=True)
    if len(data) == 1:
        return first
    value = int.from_bytes(data[1:], "big")
    return value ^ -1 if first < -120 else value


def _encode_text(data: bytes) -> bytes:
    """Serialize bytes as a Hadoop ``Text`` value: vint length, then the bytes."""
    return _encode_vint(len(data)) + data


def _decode_payload(data: bytes) -> Any:
    """Decode raw payload bytes as JSON, else UTF-8 text, else base64."""
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError:
        return base64.b64encode(data).decode("utf-8")
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return text


def _decode_writable(class_name: str | None, data: bytes) -> Any:
    """Decode a serialized key or value of the given Hadoop Writable class."""
    if class_name == TEXT_CLASS:
        size = _vint_size(int.from_bytes(data[:1], "big", signed=True))
        length = _decode_vint(data[:size])
        if len(data) != size + length:
            raise ValueError(f"Text length {length} does not match {len(data) - size} payload bytes")
        return _decode_payload(data[size:])
    if class_name == BYTES_CLASS:
        (length,) = struct.unpack(">i", data[:4])
        if len(data) != 4 + length:
            raise ValueError(f"BytesWritable length {length} does not match {len(data) - 4} payload bytes")
        return _decode_payload(data[4:])
    if class_name == INT_CLASS:
        return struct.unpack(">i", data)[0]
    if class_name == LONG_CLASS:
        return struct.unpack(">q", data)[0]
    if class_name == NULL_CLASS:
        return None
    return _decode_payload(data)


class SequenceFileIterable(BaseFileIterable):
    """
    Hadoop SequenceFile format reader/writer.

    Writes uncompressed version 6 files with ``org.apache.hadoop.io.Text`` keys and values.
    Reads uncompressed versions 4-6; Text, BytesWritable, IntWritable, LongWritable and
    NullWritable payloads are decoded, other classes from their raw bytes. Input without the
    ``SEQ`` magic is read as the headerless layout written by earlier releases:
    [key length][value length][key][value]...
    """

    datamode = "binary"
    # Bytes between sync escapes in written files (Hadoop's SYNC_INTERVAL).
    sync_interval = 100 * 1024

    def __init__(
        self,
        filename: str | None = None,
        stream: typing.IO[Any] | None = None,
        codec: BaseCodec | None = None,
        mode: str = "r",
        key_name: str = "key",
        value_name: str = "value",
        options: dict[str, Any] | None = None,
    ):
        """
        Initialize SequenceFile iterable.

        Args:
            key_name: Key name for the record key when reading (default: 'key')
            value_name: Key name for the record value when reading (default: 'value')
        """
        if options is None:
            options = {}
        # JSON payloads go through the shared value encoder (see helpers.jsonvalues).
        self._dumps: Callable[[Any], str] = make_encoder(json_default_from_options(options))
        super().__init__(filename, stream, codec=codec, binary=True, mode=mode, options=options)
        self.key_name = key_name
        self.value_name = value_name
        if "key_name" in options:
            self.key_name = options["key_name"]
        if "value_name" in options:
            self.value_name = options["value_name"]

        # SequenceFile sync marker (16 bytes): random for written files, from the header when reading
        self.sync_marker = os.urandom(SYNC_HASH_SIZE)
        self._key_class: str | None = None
        self._value_class: str | None = None
        self._legacy = False
        self._pushback = b""
        self._written = 0
        self._last_sync = 0
        try:
            self.reset()
        except FormatParseError:
            # Malformed header: release the file before reporting it
            self.close()
            raise
        pass

    def reset(self):
        """Reset iterable"""
        super().reset()
        self.pos = 0
        if self.mode == "r":
            # Read header if reading
            self._read_header()
        elif self.mode == "w" and (self.stype != ITERABLE_TYPE_CODEC or not self._written):
            # File and stream writers rewind to the start; codec writers keep appending
            self._write_header()

    def _parse_error(self, message: str, row_number: int | None = None) -> FormatParseError:
        return FormatParseError(
            format_id="sequencefile",
            message=message,
            filename=self.filename,
            row_number=row_number,
        )

    def _read(self, size: int) -> bytes:
        """Read up to ``size`` bytes, starting with bytes pushed back by header detection."""
        if not self._pushback:
            chunk: bytes = self.fobj.read(size)
            return chunk
        data, self._pushback = self._pushback[:size], self._pushback[size:]
        if len(data) < size:
            data += self.fobj.read(size - len(data))
        return data

    def _read_exact(self, size: int, what: str, row_number: int | None = None) -> bytes:
        data = self._read(size)
        if len(data) < size:
            raise self._parse_error(f"Truncated SequenceFile {what}", row_number=row_number)
        return data

    def _read_text(self, what: str) -> str:
        """Read a Hadoop ``Text`` value from the header."""
        first = self._read_exact(1, what)
        size = _vint_size(int.from_bytes(first, "big", signed=True))
        length = _decode_vint(first + self._read_exact(size - 1, what))
        if length < 0:
            raise self._parse_error(f"Invalid SequenceFile {what} length {length}")
        try:
            return self._read_exact(length, what).decode("utf-8")
        except UnicodeDecodeError as e:
            raise self._parse_error(f"Invalid UTF-8 in SequenceFile {what}") from e

    def _read_header(self):
        """Read the Hadoop header, or detect the headerless layout of earlier releases."""
        self._pushback = b""
        magic = self.fobj.read(len(HADOOP_MAGIC))
        self._legacy = magic != HADOOP_MAGIC
        if self._legacy:
            # Empty input, or records with no header: replay the bytes as record data
            self._pushback = magic
            return

        version = self._read_exact(1, "header version")[0]
        if not MIN_HADOOP_VERSION <= version <= HADOOP_VERSION:
            raise self._parse_error(
                f"Unsupported SequenceFile version {version} (supported: {MIN_HADOOP_VERSION}-{HADOOP_VERSION})"
            )
        self._key_class = self._read_text("key class name")
        self._value_class = self._read_text("value class name")

        compressed, block_compressed = self._read_exact(2, "compression flags")
        if compressed or block_compressed:
            kind = "Block" if block_compressed else "Record"
            raise self._parse_error(f"{kind}-compressed SequenceFiles are not supported")

        if version >= METADATA_VERSION:
            (metadata_len,) = struct.unpack(">i", self._read_exact(4, "metadata size"))
            if metadata_len < 0:
                raise self._parse_error(f"Invalid SequenceFile metadata size {metadata_len}")
            for _ in range(metadata_len):
                self._read_text("metadata key")
                self._read_text("metadata value")

        self.sync_marker = self._read_exact(SYNC_HASH_SIZE, "sync marker")

    def _write_header(self):
        """Write a Hadoop version 6 header for uncompressed Text keys and values."""
        class_name = _encode_text(TEXT_CLASS.encode("utf-8"))
        header = (
            HADOOP_MAGIC
            + bytes([HADOOP_VERSION])
            + class_name
            + class_name
            + b"\x00\x00"  # no record or block compression
            + struct.pack(">i", 0)  # no metadata
            + self.sync_marker
        )
        self.fobj.write(header)
        self._written = len(header)
        self._last_sync = 0

    @staticmethod
    def id() -> str:
        return "sequencefile"

    @staticmethod
    def is_flatonly() -> bool:
        return False

    def _read_record_start(self, fmt: str) -> int:
        """Read the int that opens a record, raising StopIteration at a clean end of input."""
        data = self._read(4)
        if not data:
            raise StopIteration
        if len(data) < 4:
            raise self._parse_error("Truncated SequenceFile record length", row_number=self.pos + 1)
        value: int = struct.unpack(fmt, data)[0]
        return value

    def _read_record(self) -> tuple[bytes, bytes]:
        row = self.pos + 1
        length = self._read_record_start(">i")
        if length == SYNC_ESCAPE:
            # Sync escape between records: verify the marker, then read the next record
            if self._read_exact(SYNC_HASH_SIZE, "sync marker", row) != self.sync_marker:
                raise self._parse_error("SequenceFile sync marker does not match the header", row_number=row)
            length = self._read_record_start(">i")
        (key_len,) = struct.unpack(">i", self._read_exact(4, "key length", row))
        if not 0 <= key_len <= length:
            raise self._parse_error(
                f"Invalid SequenceFile record lengths (record {length}, key {key_len})", row_number=row
            )
        return self._read_exact(key_len, "key", row), self._read_exact(length - key_len, "value", row)

    def _read_legacy_record(self) -> tuple[bytes, bytes]:
        row = self.pos + 1
        key_len = self._read_record_start(">I")
        (value_len,) = struct.unpack(">I", self._read_exact(4, "value length", row))
        return self._read_exact(key_len, "key", row), self._read_exact(value_len, "value", row)

    def read(self, skip_empty: bool = True) -> dict:
        """Read single SequenceFile record"""
        if self._legacy:
            key_data, value_data = self._read_legacy_record()
            key_obj = _decode_payload(key_data)
            value_obj = _decode_payload(value_data)
        else:
            key_data, value_data = self._read_record()
            try:
                key_obj = _decode_writable(self._key_class, key_data)
                value_obj = _decode_writable(self._value_class, value_data)
            except (ValueError, struct.error) as e:
                raise self._parse_error(f"Error reading SequenceFile: {e}", row_number=self.pos + 1) from e

        self.pos += 1
        return {self.key_name: key_obj, self.value_name: value_obj}

    def write(self, record: Row) -> None:
        """Write single SequenceFile record"""
        # Apply validation hooks if configured
        if self._validation_hooks:
            validated = self._apply_validation_hooks(record)
            if validated is None:  # Skipped
                return  # Don't write invalid row
            record = validated

        # Extract key and value from record
        if self.key_name in record and self.value_name in record:
            key_obj = record[self.key_name]
            value_obj = record[self.value_name]
        elif len(record) == 2:
            # Assume first two items are key and value
            items = list(record.items())
            key_obj = items[0][1]
            value_obj = items[1][1]
        else:
            # Use record as value, generate key
            key_obj = self.pos
            value_obj = record

        # Convert to bytes
        if isinstance(key_obj, str):
            key_data = key_obj.encode("utf-8")
        elif isinstance(key_obj, (dict, list)):
            key_data = self._dumps(key_obj).encode("utf-8")
        else:
            key_data = str(key_obj).encode("utf-8")

        if isinstance(value_obj, str):
            value_data = value_obj.encode("utf-8")
        elif isinstance(value_obj, (dict, list)):
            value_data = self._dumps(value_obj).encode("utf-8")
        else:
            value_data = str(value_obj).encode("utf-8")

        # Serialize key and value as Hadoop Text
        key_bytes = _encode_text(key_data)
        value_bytes = _encode_text(value_data)

        # Write a sync escape once sync_interval bytes have passed since the last one
        if self._written - self._last_sync >= self.sync_interval:
            self.fobj.write(struct.pack(">i", SYNC_ESCAPE) + self.sync_marker)
            self._written += 4 + SYNC_HASH_SIZE
            self._last_sync = self._written

        # Write record length and key length (4 bytes each, big-endian), then key and value
        self.fobj.write(struct.pack(">ii", len(key_bytes) + len(value_bytes), len(key_bytes)))
        self.fobj.write(key_bytes)
        self.fobj.write(value_bytes)
        self._written += 8 + len(key_bytes) + len(value_bytes)

    def write_bulk(self, records: list[Row]) -> None:
        """Write bulk SequenceFile records"""
        for record in records:
            self.write(record)
