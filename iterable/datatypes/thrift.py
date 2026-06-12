from __future__ import annotations

import typing

try:
    from thrift.protocol import TBinaryProtocol
    from thrift.transport import TTransport

    HAS_THRIFT = True
except ImportError:
    HAS_THRIFT = False

from typing import Any

from ..base import BaseCodec, BaseFileIterable
from ..types import Row


class ThriftIterable(BaseFileIterable):
    datamode = "binary"

    def __init__(
        self,
        filename: str = None,
        stream: typing.IO[Any] | None = None,
        codec: BaseCodec | None = None,
        mode: str = "r",
        struct_class=None,
        options: dict[str, Any] | None = None,
    ):
        if options is None:
            options = {}
        if not HAS_THRIFT:
            raise ImportError("Apache Thrift support requires 'thrift' package")
        super().__init__(filename, stream, codec=codec, binary=True, mode=mode, options=options)
        self.struct_class = struct_class
        if "struct_class" in options:
            self.struct_class = options["struct_class"]
        if self.struct_class is None:
            raise ValueError("Thrift requires struct_class parameter (the generated Thrift struct class)")
        self.reset()
        pass

    def reset(self):
        """Reset iterable"""
        super().reset()
        self.pos = 0
        if self.mode == "r":
            try:
                if hasattr(self.fobj, "seek"):
                    self.fobj.seek(0)
                # Read all data
                data = self.fobj.read()
                if len(data) == 0:
                    self.iterator = iter([])
                else:
                    # Thrift can contain multiple serialized structs
                    # This is a simplified implementation
                    messages = []
                    transport = TTransport.TMemoryBuffer(data)
                    protocol = TBinaryProtocol.TBinaryProtocol(transport)

                    # Try to read all structs
                    while True:
                        try:
                            struct = self.struct_class()
                            struct.read(protocol)
                            # Convert to dict
                            msg_dict = {}
                            for field in struct.__dict__:
                                msg_dict[field] = getattr(struct, field)
                            messages.append(msg_dict)
                        except Exception:
                            break

                    self.iterator = iter(messages)
            except Exception:
                self.iterator = iter([])
        else:
            # Write mode
            pass

    @staticmethod
    def id() -> str:
        return "thrift"

    @staticmethod
    def is_flatonly() -> bool:
        return False

    def read(self, skip_empty: bool = True) -> dict:
        """Read single Thrift record"""
        try:
            row = next(self.iterator)
            self.pos += 1
            return row
        except (StopIteration, EOFError, ValueError):
            raise StopIteration from None

    def write(self, record: Row) -> None:
        """Write single Thrift record"""
        struct = self.struct_class()
        # Set struct fields from dict
        for key, value in record.items():
            if hasattr(struct, key):
                setattr(struct, key, value)

        transport = TTransport.TMemoryBuffer()
        protocol = TBinaryProtocol.TBinaryProtocol(transport)
        struct.write(protocol)
        self.fobj.write(transport.getvalue())

    def write_bulk(self, records: list[Row]) -> None:
        """Write bulk Thrift records"""
        for record in records:
            self.write(record)
