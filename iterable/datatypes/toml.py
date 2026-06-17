from __future__ import annotations

import typing

try:
    import tomli
    import tomli_w

    HAS_TOMLI = True
except ImportError:
    try:
        import toml

        HAS_TOML = True
        HAS_TOMLI = False
    except ImportError:
        HAS_TOML = False
        HAS_TOMLI = False

from typing import Any

from ..base import DEFAULT_BULK_NUMBER, BaseCodec, BaseFileIterable
from ..types import Row


class TOMLIterable(BaseFileIterable):
    def __init__(
        self,
        filename: str | None = None,
        stream: typing.IO[Any] | None = None,
        codec: BaseCodec | None = None,
        mode: str = "r",
        encoding: str = "utf8",
        options: dict[str, Any] | None = None,
    ):
        if options is None:
            options = {}
        if not HAS_TOMLI and not HAS_TOML:
            raise ImportError("TOML support requires either 'tomli' and 'tomli-w' or 'toml' package")
        super().__init__(filename, stream, codec=codec, binary=False, mode=mode, encoding=encoding, options=options)
        self.reset()
        pass

    def reset(self):
        """Reset iterable"""
        super().reset()
        self.pos = 0
        if self.mode == "r":
            data_str = self.fobj.read()
            if HAS_TOMLI:
                self.data = tomli.loads(data_str)
            else:
                self.data = toml.loads(data_str)

            # TOML files typically contain tables/arrays of tables
            # Try to find array of tables or convert top-level to list
            if isinstance(self.data, dict):
                # Look for array of tables (common pattern)
                self.items = []
                for key, value in self.data.items():
                    if isinstance(value, list):
                        # Array of tables
                        for item in value:
                            item_copy = item.copy()
                            item_copy["_table"] = key
                            self.items.append(item_copy)
                    elif isinstance(value, dict):
                        # Single table
                        value_copy = value.copy()
                        value_copy["_table"] = key
                        self.items.append(value_copy)
                    else:
                        # Scalar value
                        self.items.append({key: value})
            else:
                self.items = self.data if isinstance(self.data, list) else [self.data]

            self.iterator = iter(self.items)

    @staticmethod
    def id() -> str:
        return "toml"

    @staticmethod
    def is_flatonly() -> bool:
        return False

    def read(self, skip_empty: bool = True) -> dict:
        """Read single TOML record"""
        row = next(self.iterator)
        self.pos += 1
        return row

    def read_bulk(self, num: int = DEFAULT_BULK_NUMBER) -> list[dict]:
        """Read bulk TOML records efficiently using slicing.

        This optimized implementation uses list slicing instead of calling
        read() in a loop, providing significant performance improvements
        for in-memory data access.
        """
        # Calculate how many items are available
        remaining = len(self.items) - self.pos
        if remaining == 0:
            return []

        # Use slicing to get the requested number of items
        read_count = min(num, remaining)
        chunk = self.items[self.pos : self.pos + read_count]

        # Update position and recreate iterator to stay in sync
        self.pos += read_count
        # Recreate iterator from current position for read() to work correctly
        self.iterator = iter(self.items[self.pos :])

        return chunk

    def write(self, record: Row) -> None:
        """Write single TOML record"""
        self.write_bulk(
            [
                record,
            ]
        )

    def write_bulk(self, records: list[Row]) -> None:
        """Write bulk TOML records"""
        # Convert records to TOML format
        if HAS_TOMLI:
            toml_str = tomli_w.dumps(records)
        else:
            toml_str = toml.dumps(records)
        self.fobj.write(toml_str)
