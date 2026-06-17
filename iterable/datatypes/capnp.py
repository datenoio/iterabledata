from __future__ import annotations

import os
import typing

try:
    import capnp

    HAS_CAPNP = True
except ImportError:
    HAS_CAPNP = False

from typing import Any

from ..base import BaseCodec, BaseFileIterable
from ..types import Row


class CapnpIterable(BaseFileIterable):
    datamode = "binary"

    def __init__(
        self,
        filename: str | None = None,
        stream: typing.IO[Any] | None = None,
        codec: BaseCodec | None = None,
        mode: str = "r",
        schema_file: str | None = None,
        schema_name: str | None = None,
        options: dict[str, Any] | None = None,
    ):
        if options is None:
            options = {}
        if not HAS_CAPNP:
            raise ImportError("Cap'n Proto support requires 'pycapnp' package")
        super().__init__(filename, stream, codec=codec, binary=True, mode=mode, options=options)
        self.schema_file = schema_file
        self.schema_name = schema_name
        if "schema_file" in options:
            self.schema_file = options["schema_file"]
        if "schema_name" in options:
            self.schema_name = options["schema_name"]
        if self.schema_file is None:
            raise ValueError("Cap'n Proto requires schema_file parameter")
        if self.schema_name is None:
            raise ValueError("Cap'n Proto requires schema_name parameter")
        self.schema = None
        self.reset()
        pass

    def reset(self):
        """Reset iterable"""
        super().reset()
        self.pos = 0

        # Load schema
        if not os.path.exists(self.schema_file):
            raise FileNotFoundError(f"Schema file not found: {self.schema_file}")
        self.schema = capnp.load(self.schema_file)
        self.message_class = getattr(self.schema, self.schema_name)

        if self.mode == "r":
            try:
                if hasattr(self.fobj, "seek"):
                    self.fobj.seek(0)
                # Read all data
                data = self.fobj.read()
                if len(data) == 0:
                    self.iterator = iter([])
                else:
                    # Decode Cap'n Proto messages
                    # Cap'n Proto typically stores a single message per file
                    # For multiple messages, they would need to be in a container format
                    try:
                        message = self.message_class.from_bytes_packed(data)
                        # Convert message to dict
                        msg_dict = message.to_dict()
                        if isinstance(msg_dict, list):
                            self.iterator = iter(msg_dict)
                        else:
                            self.iterator = iter([msg_dict])
                    except Exception:
                        # If that fails, try unpacked format
                        try:
                            message = self.message_class.from_bytes(data)
                            msg_dict = message.to_dict()
                            if isinstance(msg_dict, list):
                                self.iterator = iter(msg_dict)
                            else:
                                self.iterator = iter([msg_dict])
                        except Exception:
                            self.iterator = iter([])
            except Exception:
                self.iterator = iter([])
        else:
            # Write mode - no initialization needed
            pass

    @staticmethod
    def id() -> str:
        return "capnp"

    @staticmethod
    def is_flatonly() -> bool:
        return False

    def read(self, skip_empty: bool = True) -> dict:
        """Read single Cap'n Proto record"""
        try:
            row = next(self.iterator)
            self.pos += 1
            return row
        except (StopIteration, EOFError, ValueError):
            raise StopIteration from None

    def write(self, record: Row) -> None:
        """Write single Cap'n Proto record"""
        message = self.message_class.from_dict(record)
        packed = message.to_bytes_packed()
        self.fobj.write(packed)

    def write_bulk(self, records: list[Row]) -> None:
        """Write bulk Cap'n Proto records"""
        for record in records:
            self.write(record)
