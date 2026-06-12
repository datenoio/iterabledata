from __future__ import annotations

import json
import struct
import typing
from typing import Any

from ..base import BaseCodec, BaseFileIterable
from ..exceptions import FormatParseError
from ..types import Row


class TFRecordIterable(BaseFileIterable):
    """
    TensorFlow TFRecord format reader/writer.
    TFRecord format: [length][crc32(length)][data][crc32(data)]
    """

    datamode = "binary"

    def __init__(
        self,
        filename: str = None,
        stream: typing.IO[Any] | None = None,
        codec: BaseCodec | None = None,
        mode: str = "r",
        value_key: str = "value",
        options: dict[str, Any] | None = None,
    ):
        """
        Initialize TFRecord iterable.

        Args:
            value_key: Key name for the record value when reading (default: 'value')
        """
        if options is None:
            options = {}
        super().__init__(filename, stream, codec=codec, binary=True, mode=mode, options=options)
        self.value_key = value_key
        if "value_key" in options:
            self.value_key = options["value_key"]
        self.reset()
        pass

    def reset(self):
        """Reset iterable"""
        super().reset()
        self.pos = 0
        if self.mode == "r":
            # File is already opened by parent class
            pass

    @staticmethod
    def id() -> str:
        return "tfrecord"

    @staticmethod
    def is_flatonly() -> bool:
        return False

    def _read_crc32(self, data: bytes) -> int:
        """Read CRC32 checksum (simplified - actual TFRecord uses masked CRC32)"""
        # For simplicity, we'll skip CRC32 validation in basic implementation
        # Full implementation would use crc32c from crc32c library
        return 0

    def _write_crc32(self, data: bytes) -> bytes:
        """Write CRC32 checksum (simplified)"""
        # For simplicity, we'll write zeros for CRC32
        # Full implementation would use crc32c from crc32c library
        return struct.pack("<I", 0)

    def read(self, skip_empty: bool = True) -> dict:
        """Read single TFRecord record"""
        try:
            # Read length (8 bytes: uint64 little-endian)
            length_bytes = self.fobj.read(8)
            if len(length_bytes) < 8:
                raise StopIteration

            length = struct.unpack("<Q", length_bytes)[0]

            # Read CRC32 of length (4 bytes)
            crc32_length = self.fobj.read(4)
            if len(crc32_length) < 4:
                raise StopIteration

            # Read data
            data = self.fobj.read(length)
            if len(data) < length:
                raise StopIteration

            # Read CRC32 of data (4 bytes)
            crc32_data = self.fobj.read(4)
            if len(crc32_data) < 4:
                raise StopIteration

            # Parse data as JSON (TFRecord can contain various formats, JSON is common)
            try:
                # Try to parse as JSON first
                decoded = json.loads(data.decode("utf-8"))
                if isinstance(decoded, dict):
                    self.pos += 1
                    return decoded
                else:
                    # If not a dict, wrap it
                    self.pos += 1
                    return {self.value_key: decoded}
            except (json.JSONDecodeError, UnicodeDecodeError):
                # If not JSON, return as raw bytes/base64
                import base64

                self.pos += 1
                return {self.value_key: base64.b64encode(data).decode("utf-8")}

        except StopIteration:
            raise StopIteration from None
        except Exception as e:
            raise FormatParseError(
                format_id="tfrecord",
                message=f"Error reading TFRecord: {e}",
                filename=self.filename,
            ) from e

    def write(self, record: Row) -> None:
        """Write single TFRecord record"""
        # Convert record to JSON bytes
        if isinstance(record, dict):
            data = json.dumps(record, ensure_ascii=False).encode("utf-8")
        else:
            data = json.dumps({self.value_key: record}, ensure_ascii=False).encode("utf-8")

        length = len(data)

        # Write length (8 bytes: uint64 little-endian)
        self.fobj.write(struct.pack("<Q", length))

        # Write CRC32 of length (4 bytes, simplified)
        self.fobj.write(self._write_crc32(struct.pack("<Q", length)))

        # Write data
        self.fobj.write(data)

        # Write CRC32 of data (4 bytes, simplified)
        self.fobj.write(self._write_crc32(data))

    def write_bulk(self, records: list[Row]) -> None:
        """Write bulk TFRecord records"""
        for record in records:
            self.write(record)
