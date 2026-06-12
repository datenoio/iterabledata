from __future__ import annotations

import configparser
import re
import typing
from typing import Any

from ..base import BaseCodec, BaseFileIterable
from ..types import Row


class INIIterable(BaseFileIterable):
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
        super().__init__(filename, stream, codec=codec, binary=False, mode=mode, encoding=encoding, options=options)
        self.reset()
        pass

    def reset(self):
        """Reset iterable"""
        super().reset()
        self.pos = 0
        if self.mode == "r":
            self.entries = []

            # Try to parse as INI format first
            try:
                config = configparser.ConfigParser(allow_no_value=True)
                if self.filename:
                    config.read(self.filename, encoding=self.encoding)
                else:
                    config.read_file(self.fobj)

                # Convert sections to records
                for section_name in config.sections():
                    entry = {"_section": section_name}
                    for key, value in config.items(section_name):
                        entry[key] = value
                    self.entries.append(entry)

                # Also include DEFAULT section if it has values
                if config.defaults():
                    entry = {"_section": "DEFAULT"}
                    for key, value in config.defaults().items():
                        entry[key] = value
                    self.entries.append(entry)
            except Exception:
                # Fallback: parse as simple key=value format (properties file)
                if self.filename:
                    with open(self.filename, encoding=self.encoding) as f:
                        content = f.read()
                else:
                    content = self.fobj.read()
                    # Try to reset stream if possible
                    try:
                        self.fobj.seek(0)
                    except (AttributeError, OSError):
                        pass  # Stream is not seekable

                current_section = None
                current_entry = {}

                for line in content.split("\n"):
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue

                    # Check for section header [section]
                    section_match = re.match(r"^\[(.+)\]$", line)
                    if section_match:
                        if current_entry:
                            self.entries.append(current_entry)
                        current_section = section_match.group(1)
                        current_entry = {"_section": current_section}
                        continue

                    # Parse key=value
                    if "=" in line:
                        key, value = line.split("=", 1)
                        key = key.strip()
                        value = value.strip().strip('"').strip("'")
                        if current_section:
                            current_entry[key] = value
                        else:
                            self.entries.append({key: value})

                if current_entry:
                    self.entries.append(current_entry)

            self.iterator = iter(self.entries)
        else:
            self.entries = []
            self.config = configparser.ConfigParser(allow_no_value=True)

    @staticmethod
    def id() -> str:
        return "ini"

    @staticmethod
    def is_flatonly() -> bool:
        return True

    def read(self, skip_empty: bool = True) -> dict:
        """Read single INI record"""
        row = next(self.iterator)
        self.pos += 1
        return row

    def write(self, record: Row) -> None:
        """Write single INI record"""
        section = record.pop("_section", "DEFAULT")

        if not self.config.has_section(section):
            self.config.add_section(section)

        for key, value in record.items():
            self.config.set(section, key, str(value))

        # Write to file
        if self.filename:
            with open(self.filename, "w", encoding=self.encoding) as f:
                self.config.write(f)
        else:
            self.config.write(self.fobj)

    def write_bulk(self, records: list[Row]) -> None:
        """Write bulk INI records"""
        for record in records:
            self.write(record)
