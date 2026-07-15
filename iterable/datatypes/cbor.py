from __future__ import annotations

import typing

try:
    import cbor2

    HAS_CBOR2 = True
except ImportError:
    try:
        import cbor

        HAS_CBOR = True
        HAS_CBOR2 = False
    except ImportError:
        HAS_CBOR = False
        HAS_CBOR2 = False

from typing import Any

from ..base import BaseCodec, BaseFileIterable
from ..types import Row


class CBORIterable(BaseFileIterable):
    """CBOR (Concise Binary Object Representation) reader/writer.

    Memory behavior: the whole file is parsed and materialized in memory on
    open; this format does not stream records incrementally.
    """

    datamode = "binary"

    def __init__(
        self,
        filename: str | None = None,
        stream: typing.IO[Any] | None = None,
        codec: BaseCodec | None = None,
        mode: str = "r",
        options: dict[str, Any] | None = None,
    ):
        if options is None:
            options = {}
        if not HAS_CBOR2 and not HAS_CBOR:
            raise ImportError("CBOR support requires the 'cbor2' package. Install with: pip install iterabledata[cbor]")
        super().__init__(filename, stream, codec=codec, binary=True, mode=mode, options=options)
        self.reset()
        pass

    def reset(self):
        """Reset iterable"""
        super().reset()
        self.pos = 0
        if self.mode == "r":
            # For reading, CBOR files typically contain a single object or array
            # We'll read the entire file and iterate over it
            if HAS_CBOR2:
                try:
                    # Try to seek to beginning
                    if hasattr(self.fobj, "seek"):
                        self.fobj.seek(0)
                    # Read all data
                    data = self.fobj.read()
                    if len(data) == 0:
                        self.iterator = iter([])
                    else:
                        # Decode CBOR data
                        self.data = cbor2.loads(data)
                        if isinstance(self.data, list):
                            self.iterator = iter(self.data)
                        else:
                            # Single object, wrap in list
                            self.iterator = iter([self.data])
                except Exception:
                    # If reading fails, create empty iterator
                    self.iterator = iter([])
            else:
                # cbor library doesn't have a streaming decoder, so we'll read all at once
                try:
                    if hasattr(self.fobj, "seek"):
                        self.fobj.seek(0)
                    self.data = cbor.load(self.fobj)
                    if isinstance(self.data, list):
                        self.iterator = iter(self.data)
                    else:
                        # Single object, wrap in list
                        self.iterator = iter([self.data])
                except Exception:
                    self.iterator = iter([])
        else:
            # Write mode - no initialization needed
            pass

    @staticmethod
    def id() -> str:
        return "cbor"

    @staticmethod
    def is_flatonly() -> bool:
        return False

    def is_streaming(self) -> bool:
        """Memory behavior: the whole file/table is materialized on open."""
        return False

    def read(self, skip_empty: bool = True) -> dict:
        """Read single CBOR record"""
        try:
            row = next(self.iterator)
            self.pos += 1
            return row
        except (StopIteration, EOFError, ValueError):
            raise StopIteration from None

    def write(self, record: Row) -> None:
        """Write single CBOR record"""
        if HAS_CBOR2:
            encoded = cbor2.dumps(record)
            self.fobj.write(encoded)
        else:
            cbor.dump(record, self.fobj)

    def write_bulk(self, records: list[Row]) -> None:
        """Write bulk CBOR records"""
        for record in records:
            self.write(record)
