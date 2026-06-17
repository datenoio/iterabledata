from __future__ import annotations

import json
import struct
import typing
from typing import Any

from ..base import BaseCodec, BaseFileIterable
from ..exceptions import FormatParseError
from ..types import Row


class PulsarIterable(BaseFileIterable):
    """
    Apache Pulsar message format reader/writer.
    Pulsar message format: [message id][publish time][key][properties][payload]
    Simplified version for iterable reading/writing.
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
        Initialize Pulsar iterable.

        Args:
            key_name: Key name for the message key when reading (default: 'key')
            value_name: Key name for the message value when reading (default: 'value')
            include_metadata: Include message_id, publish_time, properties in output (default: True)
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
        return "pulsar"

    @staticmethod
    def is_flatonly() -> bool:
        return False

    def read(self, skip_empty: bool = True) -> dict:
        """Read single Pulsar message"""
        try:
            # Read message ID length (4 bytes, int32, big-endian)
            msgid_len_bytes = self.fobj.read(4)
            if len(msgid_len_bytes) < 4:
                raise StopIteration
            msgid_len = struct.unpack(">I", msgid_len_bytes)[0]

            # Read message ID
            message_id = self.fobj.read(msgid_len).decode("utf-8")

            # Read publish time (8 bytes, int64, big-endian)
            publish_time_bytes = self.fobj.read(8)
            if len(publish_time_bytes) < 8:
                raise StopIteration
            publish_time = struct.unpack(">q", publish_time_bytes)[0]

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

            # Read properties count (4 bytes, int32, big-endian)
            props_count_bytes = self.fobj.read(4)
            if len(props_count_bytes) < 4:
                raise StopIteration
            props_count = struct.unpack(">I", props_count_bytes)[0]

            # Read properties
            properties = {}
            for _ in range(props_count):
                # Read property key length (2 bytes, int16, big-endian)
                pkey_len_bytes = self.fobj.read(2)
                if len(pkey_len_bytes) < 2:
                    raise StopIteration
                pkey_len = struct.unpack(">h", pkey_len_bytes)[0]

                # Read property key
                pkey = self.fobj.read(pkey_len).decode("utf-8")

                # Read property value length (2 bytes, int16, big-endian)
                pval_len_bytes = self.fobj.read(2)
                if len(pval_len_bytes) < 2:
                    raise StopIteration
                pval_len = struct.unpack(">h", pval_len_bytes)[0]

                # Read property value
                pval = self.fobj.read(pval_len).decode("utf-8")
                properties[pkey] = pval

            # Read payload length (4 bytes, int32, big-endian)
            payload_len_bytes = self.fobj.read(4)
            if len(payload_len_bytes) < 4:
                raise StopIteration
            payload_len = struct.unpack(">I", payload_len_bytes)[0]

            # Read payload
            payload_data = self.fobj.read(payload_len)
            if len(payload_data) < payload_len:
                raise StopIteration

            # Parse key and payload
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
            if payload_data:
                try:
                    value_str = payload_data.decode("utf-8")
                    try:
                        value_obj = json.loads(value_str)
                    except json.JSONDecodeError:
                        value_obj = value_str
                except UnicodeDecodeError:
                    import base64

                    value_obj = base64.b64encode(payload_data).decode("utf-8")

            result = {}
            if self.include_metadata:
                result["message_id"] = message_id
                result["publish_time"] = publish_time
                if properties:
                    result["properties"] = properties

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
                format_id="pulsar",
                message=f"Error reading Pulsar message: {e}",
                filename=self.filename,
            ) from e

    def write(self, record: Row) -> None:
        """Write single Pulsar message"""
        # Extract key and value from record
        key_obj = record.get(self.key_name)
        value_obj = record.get(self.value_name)

        # If not found, try to infer from record structure
        if key_obj is None and value_obj is None:
            if len(record) == 2 and self.include_metadata:
                # Skip metadata fields
                items = [(k, v) for k, v in record.items() if k not in ["message_id", "publish_time", "properties"]]
                if len(items) == 2:
                    key_obj = items[0][1]
                    value_obj = items[1][1]
            elif len(record) == 1:
                value_obj = list(record.values())[0]

        # Get metadata
        message_id = record.get("message_id", f"msg_{self.pos}")
        publish_time = record.get("publish_time", 0)
        properties = record.get("properties", {})

        # Convert to bytes
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
            value_data = b""

        # Write message ID
        message_id_bytes = message_id.encode("utf-8")
        self.fobj.write(struct.pack(">I", len(message_id_bytes)))
        self.fobj.write(message_id_bytes)

        # Write publish time (8 bytes, int64, big-endian)
        self.fobj.write(struct.pack(">q", publish_time))

        # Write key length (4 bytes, int32, big-endian, -1 for null)
        if key_data:
            self.fobj.write(struct.pack(">i", len(key_data)))
            self.fobj.write(key_data)
        else:
            self.fobj.write(struct.pack(">i", -1))

        # Write properties count (4 bytes, int32, big-endian)
        self.fobj.write(struct.pack(">I", len(properties)))

        # Write properties
        for pkey, pval in properties.items():
            pkey_bytes = pkey.encode("utf-8")
            pval_bytes = str(pval).encode("utf-8")
            self.fobj.write(struct.pack(">h", len(pkey_bytes)))
            self.fobj.write(pkey_bytes)
            self.fobj.write(struct.pack(">h", len(pval_bytes)))
            self.fobj.write(pval_bytes)

        # Write payload length (4 bytes, int32, big-endian)
        self.fobj.write(struct.pack(">I", len(value_data)))
        self.fobj.write(value_data)

    def write_bulk(self, records: list[Row]) -> None:
        """Write bulk Pulsar messages"""
        for record in records:
            self.write(record)
