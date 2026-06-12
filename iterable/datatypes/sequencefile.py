from __future__ import annotations

import json
import struct
import typing
from typing import Any

from ..base import BaseCodec, BaseFileIterable
from ..exceptions import FormatParseError
from ..types import Row


class SequenceFileIterable(BaseFileIterable):
    """
    Hadoop SequenceFile format reader/writer.
    SequenceFile format: [sync marker][key length][value length][key][value]...
    """

    datamode = "binary"

    def __init__(
        self,
        filename: str = None,
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
        super().__init__(filename, stream, codec=codec, binary=True, mode=mode, options=options)
        self.key_name = key_name
        self.value_name = value_name
        if "key_name" in options:
            self.key_name = options["key_name"]
        if "value_name" in options:
            self.value_name = options["value_name"]

        # SequenceFile sync marker (16 bytes)
        self.sync_marker = b"SEQ\x06" + b"\x00" * 12
        self.reset()
        pass

    def reset(self):
        """Reset iterable"""
        super().reset()
        self.pos = 0
        if self.mode == "r":
            # Read header if reading
            self._read_header()

    def _read_header(self):
        """Read SequenceFile header"""
        try:
            # Read version (1 byte)
            version = self.fobj.read(1)
            if len(version) == 0:
                return

            # Read key class name length and name
            key_class_len_bytes = self.fobj.read(4)
            if len(key_class_len_bytes) < 4:
                return
            key_class_len = struct.unpack(">I", key_class_len_bytes)[0]
            self.fobj.read(key_class_len)  # Skip key class name

            # Read value class name length and name
            value_class_len_bytes = self.fobj.read(4)
            if len(value_class_len_bytes) < 4:
                return
            value_class_len = struct.unpack(">I", value_class_len_bytes)[0]
            self.fobj.read(value_class_len)  # Skip value class name

            # Read compression flag
            self.fobj.read(1)

            # Read block compression flag
            self.fobj.read(1)

            # Read metadata
            metadata_len_bytes = self.fobj.read(4)
            if len(metadata_len_bytes) < 4:
                return
            metadata_len = struct.unpack(">I", metadata_len_bytes)[0]
            for _ in range(metadata_len):
                # Read metadata key
                key_len_bytes = self.fobj.read(4)
                if len(key_len_bytes) < 4:
                    return
                key_len = struct.unpack(">I", key_len_bytes)[0]
                self.fobj.read(key_len)
                # Read metadata value
                value_len_bytes = self.fobj.read(4)
                if len(value_len_bytes) < 4:
                    return
                value_len = struct.unpack(">I", value_len_bytes)[0]
                self.fobj.read(value_len)

            # Read sync marker
            self.fobj.read(16)
        except Exception:
            # If header reading fails, assume we're at data start
            pass

    @staticmethod
    def id() -> str:
        return "sequencefile"

    @staticmethod
    def is_flatonly() -> bool:
        return False

    def read(self, skip_empty: bool = True) -> dict:
        """Read single SequenceFile record"""
        try:
            # Check for sync marker (indicates new block)
            sync_check = self.fobj.read(16)
            if len(sync_check) < 16:
                raise StopIteration

            if sync_check == self.sync_marker:
                # This is a sync marker, read next record
                pass
            else:
                # Not a sync marker, seek back
                self.fobj.seek(-16, 1)

            # Read key length (4 bytes, big-endian)
            key_len_bytes = self.fobj.read(4)
            if len(key_len_bytes) < 4:
                raise StopIteration

            key_len = struct.unpack(">I", key_len_bytes)[0]

            # Read value length (4 bytes, big-endian)
            value_len_bytes = self.fobj.read(4)
            if len(value_len_bytes) < 4:
                raise StopIteration

            value_len = struct.unpack(">I", value_len_bytes)[0]

            # Read key
            key_data = self.fobj.read(key_len)
            if len(key_data) < key_len:
                raise StopIteration

            # Read value
            value_data = self.fobj.read(value_len)
            if len(value_data) < value_len:
                raise StopIteration

            # Try to decode as UTF-8 strings or JSON
            try:
                key_str = key_data.decode("utf-8")
                try:
                    key_obj = json.loads(key_str)
                except json.JSONDecodeError:
                    key_obj = key_str
            except UnicodeDecodeError:
                import base64

                key_obj = base64.b64encode(key_data).decode("utf-8")

            try:
                value_str = value_data.decode("utf-8")
                try:
                    value_obj = json.loads(value_str)
                except json.JSONDecodeError:
                    value_obj = value_str
            except UnicodeDecodeError:
                import base64

                value_obj = base64.b64encode(value_data).decode("utf-8")

            self.pos += 1
            return {self.key_name: key_obj, self.value_name: value_obj}

        except StopIteration:
            raise StopIteration from None
        except Exception as e:
            raise FormatParseError(
                format_id="sequencefile",
                message=f"Error reading SequenceFile: {e}",
                filename=self.filename,
            ) from e

    def write(self, record: Row) -> None:
        """Write single SequenceFile record"""
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
            key_data = json.dumps(key_obj, ensure_ascii=False).encode("utf-8")
        else:
            key_data = str(key_obj).encode("utf-8")

        if isinstance(value_obj, str):
            value_data = value_obj.encode("utf-8")
        elif isinstance(value_obj, (dict, list)):
            value_data = json.dumps(value_obj, ensure_ascii=False).encode("utf-8")
        else:
            value_data = str(value_obj).encode("utf-8")

        # Write key length (4 bytes, big-endian)
        self.fobj.write(struct.pack(">I", len(key_data)))

        # Write value length (4 bytes, big-endian)
        self.fobj.write(struct.pack(">I", len(value_data)))

        # Write key
        self.fobj.write(key_data)

        # Write value
        self.fobj.write(value_data)

    def write_bulk(self, records: list[Row]) -> None:
        """Write bulk SequenceFile records"""
        for record in records:
            self.write(record)
