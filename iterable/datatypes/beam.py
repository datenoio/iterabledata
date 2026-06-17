from __future__ import annotations

import json
import struct
import typing
from typing import Any

from ..base import BaseCodec, BaseFileIterable
from ..exceptions import FormatParseError
from ..types import Row


class BeamIterable(BaseFileIterable):
    """
    Apache Beam format reader/writer.
    Beam format: [window][timestamp][key][value]
    Simplified version for iterable reading/writing of Beam data.
    """

    datamode = "binary"

    def __init__(
        self,
        filename: str | None = None,
        stream: typing.IO[Any] | None = None,
        codec: BaseCodec | None = None,
        mode: str = "r",
        key_name: str = "key",
        value_name: str = "value",
        include_metadata: bool = True,
        options: dict[str, Any] | None = None,
    ):
        """
        Initialize Beam iterable.

        Args:
            key_name: Key name for the record key when reading (default: 'key')
            value_name: Key name for the record value when reading (default: 'value')
            include_metadata: Include window, timestamp in output (default: True)
        """
        if options is None:
            options = {}
        super().__init__(filename, stream, codec=codec, binary=True, mode=mode, options=options)
        self.key_name = key_name
        self.value_name = value_name
        self.include_metadata = include_metadata
        if "key_name" in options:
            self.key_name = options["key_name"]
        if "value_name" in options:
            self.value_name = options["value_name"]
        if "include_metadata" in options:
            self.include_metadata = options["include_metadata"]

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
        return "beam"

    @staticmethod
    def is_flatonly() -> bool:
        return False

    def read(self, skip_empty: bool = True) -> dict:
        """Read single Beam record"""
        try:
            # Read window length (4 bytes, int32, big-endian)
            window_len_bytes = self.fobj.read(4)
            if len(window_len_bytes) < 4:
                raise StopIteration
            window_len = struct.unpack(">I", window_len_bytes)[0]

            # Read window
            window = None
            if window_len > 0:
                window_data = self.fobj.read(window_len)
                if len(window_data) < window_len:
                    raise StopIteration
                window = window_data.decode("utf-8")

            # Read timestamp (8 bytes, int64, big-endian)
            timestamp_bytes = self.fobj.read(8)
            if len(timestamp_bytes) < 8:
                raise StopIteration
            timestamp = struct.unpack(">q", timestamp_bytes)[0]

            # Read key length (4 bytes, int32, big-endian, -1 means null)
            key_len_bytes = self.fobj.read(4)
            if len(key_len_bytes) < 4:
                raise StopIteration
            key_len = struct.unpack(">i", key_len_bytes)[0]

            # Read key
            key_data = None
            if key_len >= 0:
                key_data = self.fobj.read(key_len)
                if len(key_data) < key_len:
                    raise StopIteration

            # Read value length (4 bytes, int32, big-endian, -1 means null)
            value_len_bytes = self.fobj.read(4)
            if len(value_len_bytes) < 4:
                raise StopIteration
            value_len = struct.unpack(">i", value_len_bytes)[0]

            # Read value
            value_data = None
            if value_len >= 0:
                value_data = self.fobj.read(value_len)
                if len(value_data) < value_len:
                    raise StopIteration

            # Parse key and value
            key_obj = None
            if key_data:
                try:
                    key_str = key_data.decode("utf-8")
                    try:
                        key_obj = json.loads(key_str)
                    except json.JSONDecodeError:
                        key_obj = key_str
                except UnicodeDecodeError:
                    import base64

                    key_obj = base64.b64encode(key_data).decode("utf-8")

            value_obj = None
            if value_data:
                try:
                    value_str = value_data.decode("utf-8")
                    try:
                        value_obj = json.loads(value_str)
                    except json.JSONDecodeError:
                        value_obj = value_str
                except UnicodeDecodeError:
                    import base64

                    value_obj = base64.b64encode(value_data).decode("utf-8")

            result = {}
            if self.include_metadata:
                if window:
                    result["window"] = window
                result["timestamp"] = timestamp

            if key_obj is not None:
                result[self.key_name] = key_obj
            if value_obj is not None:
                result[self.value_name] = value_obj

            self.pos += 1
            return result

        except StopIteration:
            raise StopIteration from None
        except Exception as e:
            raise FormatParseError(
                format_id="beam",
                message=f"Error reading Beam record: {e}",
                filename=self.filename,
            ) from e

    def write(self, record: Row) -> None:
        """Write single Beam record"""
        # Extract key and value from record
        key_obj = record.get(self.key_name)
        value_obj = record.get(self.value_name)

        # If not found, try to infer from record structure
        if key_obj is None and value_obj is None:
            if len(record) == 2 and self.include_metadata:
                # Skip metadata fields
                items = [(k, v) for k, v in record.items() if k not in ["window", "timestamp"]]
                if len(items) == 2:
                    key_obj = items[0][1]
                    value_obj = items[1][1]
            elif len(record) == 1:
                value_obj = list(record.values())[0]

        # Get metadata
        window = record.get("window")
        timestamp = record.get("timestamp", 0)

        # Convert to bytes
        window_bytes = window.encode("utf-8") if window else b""

        key_data = None
        if key_obj is not None:
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
        elif value_obj is not None:
            value_data = str(value_obj).encode("utf-8")
        else:
            value_data = None

        # Write window length (4 bytes, int32, big-endian)
        self.fobj.write(struct.pack(">I", len(window_bytes)))
        if window_bytes:
            self.fobj.write(window_bytes)

        # Write timestamp (8 bytes, int64, big-endian)
        self.fobj.write(struct.pack(">q", timestamp))

        # Write key length (4 bytes, int32, big-endian, -1 for null)
        if key_data:
            self.fobj.write(struct.pack(">i", len(key_data)))
            self.fobj.write(key_data)
        else:
            self.fobj.write(struct.pack(">i", -1))

        # Write value length (4 bytes, int32, big-endian, -1 for null)
        if value_data:
            self.fobj.write(struct.pack(">i", len(value_data)))
            self.fobj.write(value_data)
        else:
            self.fobj.write(struct.pack(">i", -1))

    def write_bulk(self, records: list[Row]) -> None:
        """Write bulk Beam records"""
        for record in records:
            self.write(record)
