from __future__ import annotations

import typing

try:
    import ldif3  # noqa: F401

    HAS_LDIF3 = True
except ImportError:
    try:
        import ldif  # noqa: F401

        HAS_LDIF = True
        HAS_LDIF3 = False
    except ImportError:
        HAS_LDIF = False
        HAS_LDIF3 = False

from typing import Any

from ..base import BaseCodec, BaseFileIterable
from ..exceptions import WriteError
from ..types import Row


class LDIFIterable(BaseFileIterable):
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
        if not HAS_LDIF3 and not HAS_LDIF:
            raise ImportError("LDIF support requires 'ldif3' or 'ldif' package")
        super().__init__(filename, stream, codec=codec, binary=False, mode=mode, encoding=encoding, options=options)
        self.reset()
        pass

    def reset(self):
        """Reset iterable"""
        super().reset()
        self.pos = 0
        if self.mode == "r":
            self.entries = []
            current_entry = {}
            current_dn = None

            for line in self.fobj:
                line = line.rstrip("\n\r")

                if line == "":
                    # Empty line indicates end of entry
                    if current_dn and current_entry:
                        current_entry["dn"] = current_dn
                        self.entries.append(current_entry)
                    current_entry = {}
                    current_dn = None
                    continue

                if line.startswith(" ") or line.startswith("\t"):
                    # Continuation line
                    if current_entry and current_entry.get("_last_attr"):
                        current_entry[current_entry["_last_attr"]] += line[1:]
                    continue

                if ":" in line:
                    parts = line.split(":", 1)
                    if len(parts) == 2:
                        attr_name = parts[0].strip()
                        attr_value = parts[1].strip()

                        if attr_name.lower() == "dn":
                            current_dn = attr_value
                        else:
                            # Handle multi-valued attributes
                            if attr_name in current_entry:
                                if not isinstance(current_entry[attr_name], list):
                                    current_entry[attr_name] = [current_entry[attr_name]]
                                current_entry[attr_name].append(attr_value)
                            else:
                                current_entry[attr_name] = attr_value
                            current_entry["_last_attr"] = attr_name

            # Add last entry if file doesn't end with newline
            if current_dn and current_entry:
                current_entry["dn"] = current_dn
                self.entries.append(current_entry)

            # Clean up temporary keys
            for entry in self.entries:
                entry.pop("_last_attr", None)

            self.iterator = iter(self.entries)
        else:
            self.entries = []

    @staticmethod
    def id() -> str:
        return "ldif"

    @staticmethod
    def is_flatonly() -> bool:
        return False

    def read(self, skip_empty: bool = True) -> dict:
        """Read single LDIF record"""
        row = next(self.iterator)
        self.pos += 1
        return row

    def write(self, record: Row) -> None:
        """Write single LDIF record"""
        if "dn" not in record:
            raise WriteError(
                "LDIF entry must have 'dn' field",
                filename=self.filename,
                error_code="INVALID_PARAMETER",
            )

        self.fobj.write(f"dn: {record['dn']}\n")
        for key, value in record.items():
            if key == "dn":
                continue
            if isinstance(value, list):
                for v in value:
                    self.fobj.write(f"{key}: {v}\n")
            else:
                self.fobj.write(f"{key}: {value}\n")
        self.fobj.write("\n")

    def write_bulk(self, records: list[Row]) -> None:
        """Write bulk LDIF records"""
        for record in records:
            self.write(record)
