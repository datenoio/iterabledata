from __future__ import annotations

import json
import struct
import typing
from typing import Any

from ..base import BaseCodec, BaseFileIterable
from ..exceptions import FormatParseError
from ..types import Row


def _decode_pulsar_payload(data: bytes) -> Any:
    """Decode a key/payload value: JSON when possible, else text, else base64."""
    try:
        text = data.decode("utf-8")
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return text
    except UnicodeDecodeError:
        import base64

        return base64.b64encode(data).decode("utf-8")


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

    def _read_exact(self, nbytes: int) -> bytes:
        """Read exactly ``nbytes`` from the stream; a short read ends iteration."""
        data = self.fobj.read(nbytes)
        if len(data) < nbytes:
            raise StopIteration
        return data

    def _read_optional_payload(self) -> bytes | None:
        """Read a length-prefixed payload (int32 big-endian; -1 means null)."""
        length = struct.unpack(">i", self._read_exact(4))[0]
        if length < 0:
            return None
        return self._read_exact(length)

    def _read_properties(self) -> dict:
        """Read the properties block (count int32, then key/value pairs)."""
        props_count = struct.unpack(">I", self._read_exact(4))[0]
        properties = {}
        for _ in range(props_count):
            # Read property key length (2 bytes, int16, big-endian)
            pkey_len = struct.unpack(">h", self._read_exact(2))[0]

            # Read property key
            pkey = self.fobj.read(pkey_len).decode("utf-8")

            # Read property value length (2 bytes, int16, big-endian)
            pval_len = struct.unpack(">h", self._read_exact(2))[0]

            # Read property value
            pval = self.fobj.read(pval_len).decode("utf-8")
            properties[pkey] = pval
        return properties

    def read(self, skip_empty: bool = True) -> dict:
        """Read single Pulsar message"""
        try:
            # Read message ID length (4 bytes, int32, big-endian)
            msgid_len = struct.unpack(">I", self._read_exact(4))[0]

            # Read message ID
            message_id = self.fobj.read(msgid_len).decode("utf-8")

            # Read publish time (8 bytes, int64, big-endian)
            publish_time = struct.unpack(">q", self._read_exact(8))[0]

            # Read key (length-prefixed, -1 means null)
            key_data = self._read_optional_payload()

            # Read properties
            properties = self._read_properties()

            # Read payload length (4 bytes, int32, big-endian) and payload
            payload_len = struct.unpack(">I", self._read_exact(4))[0]
            payload_data = self._read_exact(payload_len)

            # Parse key and payload
            key_obj = _decode_pulsar_payload(key_data) if key_data else None
            value_obj = _decode_pulsar_payload(payload_data) if payload_data else None

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
        # Apply validation hooks if configured
        if self._validation_hooks:
            validated = self._apply_validation_hooks(record)
            if validated is None:  # Skipped
                return  # Don't write invalid row
            record = validated

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
