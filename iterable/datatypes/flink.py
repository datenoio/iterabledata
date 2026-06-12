from __future__ import annotations

import json
import struct
import typing
from typing import Any

from ..base import BaseCodec, BaseFileIterable
from ..exceptions import FormatParseError
from ..types import Row


class FlinkIterable(BaseFileIterable):
    """
    Apache Flink checkpoint format reader/writer.
    Flink checkpoint format: [checkpoint id][timestamp][state data]
    Simplified version for iterable reading/writing of checkpoint data.
    """

    datamode = "binary"

    def __init__(
        self,
        filename: str = None,
        stream: typing.IO[Any] | None = None,
        codec: BaseCodec | None = None,
        mode: str = "r",
        include_metadata: bool = True,
        options: dict[str, Any] | None = None,
    ):
        """
        Initialize Flink iterable.

        Args:
            include_metadata: Include checkpoint_id, timestamp in output (default: True)
        """
        if options is None:
            options = {}
        super().__init__(filename, stream, codec=codec, binary=True, mode=mode, options=options)
        self.include_metadata = include_metadata
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
        return "flink"

    @staticmethod
    def is_flatonly() -> bool:
        return False

    def read(self, skip_empty: bool = True) -> dict:
        """Read single Flink checkpoint record"""
        try:
            # Read checkpoint ID (8 bytes, int64, big-endian)
            checkpoint_id_bytes = self.fobj.read(8)
            if len(checkpoint_id_bytes) < 8:
                raise StopIteration
            checkpoint_id = struct.unpack(">q", checkpoint_id_bytes)[0]

            # Read timestamp (8 bytes, int64, big-endian)
            timestamp_bytes = self.fobj.read(8)
            if len(timestamp_bytes) < 8:
                raise StopIteration
            timestamp = struct.unpack(">q", timestamp_bytes)[0]

            # Read state data length (4 bytes, int32, big-endian)
            state_len_bytes = self.fobj.read(4)
            if len(state_len_bytes) < 4:
                raise StopIteration
            state_len = struct.unpack(">I", state_len_bytes)[0]

            # Read state data
            state_data = self.fobj.read(state_len)
            if len(state_data) < state_len:
                raise StopIteration

            # Parse state data
            try:
                state_str = state_data.decode("utf-8")
                try:
                    state_obj = json.loads(state_str)
                except json.JSONDecodeError:
                    state_obj = state_str
            except UnicodeDecodeError:
                import base64

                state_obj = base64.b64encode(state_data).decode("utf-8")

            result = {}
            if self.include_metadata:
                result["checkpoint_id"] = checkpoint_id
                result["timestamp"] = timestamp

            # If state is a dict, merge it; otherwise use 'data' key
            if isinstance(state_obj, dict):
                result.update(state_obj)
            else:
                result["data"] = state_obj

            self.pos += 1
            return result

        except StopIteration:
            raise StopIteration from None
        except Exception as e:
            raise FormatParseError(
                format_id="flink",
                message=f"Error reading Flink checkpoint: {e}",
                filename=self.filename,
            ) from e

    def write(self, record: Row) -> None:
        """Write single Flink checkpoint record"""
        # Get metadata
        checkpoint_id = record.get("checkpoint_id", self.pos)
        timestamp = record.get("timestamp", 0)

        # Extract state data (everything except metadata)
        state_data = {}
        if self.include_metadata:
            for key, value in record.items():
                if key not in ["checkpoint_id", "timestamp"]:
                    state_data[key] = value
        else:
            state_data = record

        # Convert to bytes
        if isinstance(state_data, dict):
            state_bytes = json.dumps(state_data, ensure_ascii=False).encode("utf-8")
        elif isinstance(state_data, str):
            state_bytes = state_data.encode("utf-8")
        else:
            state_bytes = json.dumps({"data": state_data}, ensure_ascii=False).encode("utf-8")

        # Write checkpoint ID (8 bytes, int64, big-endian)
        self.fobj.write(struct.pack(">q", checkpoint_id))

        # Write timestamp (8 bytes, int64, big-endian)
        self.fobj.write(struct.pack(">q", timestamp))

        # Write state data length (4 bytes, int32, big-endian)
        self.fobj.write(struct.pack(">I", len(state_bytes)))

        # Write state data
        self.fobj.write(state_bytes)

    def write_bulk(self, records: list[Row]) -> None:
        """Write bulk Flink checkpoint records"""
        for record in records:
            self.write(record)
