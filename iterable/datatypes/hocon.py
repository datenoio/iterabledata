from __future__ import annotations

import typing

try:
    from pyhocon import ConfigFactory

    HAS_PYHOCON = True
except ImportError:
    HAS_PYHOCON = False

from typing import Any

from ..base import BaseCodec, BaseFileIterable
from ..types import Row


class HOCONIterable(BaseFileIterable):
    def __init__(
        self,
        filename: str = None,
        stream: typing.IO[Any] | None = None,
        codec: BaseCodec | None = None,
        mode: str = "r",
        encoding: str = "utf8",
        options: dict[str, Any] | None = None,
    ):
        if options is None:
            options = {}
        if not HAS_PYHOCON:
            raise ImportError("HOCON support requires 'pyhocon' package")
        super().__init__(filename, stream, codec=codec, binary=False, mode=mode, encoding=encoding, options=options)
        self.reset()
        pass

    def reset(self):
        """Reset iterable"""
        super().reset()
        self.pos = 0
        if self.mode == "r":
            content = self.fobj.read()

            # Parse HOCON config
            config = ConfigFactory.parse_string(content)

            # Convert to list of records
            self.entries = []

            # If config is a dict, try to find arrays or convert to records
            if isinstance(config, dict):
                # Look for arrays (common pattern in HOCON)
                for key, value in config.items():
                    if isinstance(value, list):
                        # Array of objects
                        for item in value:
                            if isinstance(item, dict):
                                item_copy = item.copy()
                                item_copy["_key"] = key
                                self.entries.append(item_copy)
                            else:
                                self.entries.append({key: item})
                    elif isinstance(value, dict):
                        # Nested object - flatten or add as single record
                        value_copy = value.copy()
                        value_copy["_key"] = key
                        self.entries.append(value_copy)
                    else:
                        # Scalar value
                        self.entries.append({key: value})
            elif isinstance(config, list):
                self.entries = [item if isinstance(item, dict) else {"value": item} for item in config]
            else:
                self.entries = [{"value": config}]

            self.iterator = iter(self.entries)
        else:
            self.entries = []

    @staticmethod
    def id() -> str:
        return "hocon"

    @staticmethod
    def is_flatonly() -> bool:
        return False

    def read(self, skip_empty: bool = True) -> dict:
        """Read single HOCON record"""
        row = next(self.iterator)
        self.pos += 1
        return row

    def write(self, record: Row) -> None:
        """Write single HOCON record"""
        # Convert dict to HOCON format
        from pyhocon import ConfigTree

        config = ConfigTree()

        for key, value in record.items():
            if key.startswith("_"):
                continue  # Skip metadata keys
            config.put(key, value)

        config.as_plain_ordered_dict()
        # Simple HOCON output (pyhocon doesn't have easy write, so we'll do basic)
        lines = []
        for key, value in record.items():
            if key.startswith("_"):
                continue
            if isinstance(value, str):
                lines.append(f'{key} = "{value}"')
            else:
                lines.append(f"{key} = {value}")

        self.fobj.write("\n".join(lines) + "\n")

    def write_bulk(self, records: list[Row]) -> None:
        """Write bulk HOCON records"""
        # Write as array
        self.fobj.write("[\n")
        for i, record in enumerate(records):
            lines = []
            for key, value in record.items():
                if key.startswith("_"):
                    continue
                if isinstance(value, str):
                    lines.append(f'  {key} = "{value}"')
                else:
                    lines.append(f"  {key} = {value}")

            if lines:
                self.fobj.write("  {\n")
                self.fobj.write(",\n".join(lines))
                self.fobj.write("\n  }")
                if i < len(records) - 1:
                    self.fobj.write(",")
                self.fobj.write("\n")
        self.fobj.write("]\n")
