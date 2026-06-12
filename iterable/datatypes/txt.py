from __future__ import annotations

import typing
from typing import Any

from ..base import BaseCodec, BaseFileIterable
from ..helpers.utils import rowincount
from ..types import Row


class TxtIterable(BaseFileIterable):
    def __init__(
        self,
        filename: str = None,
        stream: typing.IO[Any] | None = None,
        codec: BaseCodec | None = None,
        mode: str = "r",
        encoding: str = "utf8",
        parser: typing.Callable[[str], dict] = None,
        options: dict[str, Any] | None = None,
    ):
        if options is None:
            options = {}
        self.pos = 0
        self.parser = parser
        # Check if parser is provided in options
        if self.parser is None and "parser" in options:
            self.parser = options["parser"]
        super().__init__(filename, stream, codec=codec, binary=False, mode=mode, encoding=encoding, options=options)
        pass

    @staticmethod
    def id() -> str:
        return "txt"

    @staticmethod
    def is_flatonly() -> bool:
        return False

    @staticmethod
    def has_totals() -> bool:
        """Has totals indicator"""
        return True

    def totals(self):
        """Returns file totals"""
        if self.codec is not None:
            fobj = self.codec.fileobj()
        else:
            fobj = self.fobj
        return rowincount(self.filename, fobj)

    def read(self, skip_empty: bool = True) -> Row:
        """Read single line from text file

        Returns:
            - If parser is None: returns line content as string (with newline stripped)
            - If parser is provided: returns dict result of parser applied to the line
        """
        line = next(self.fobj)
        if skip_empty and len(line.strip()) == 0:
            return self.read(skip_empty)
        self.pos += 1
        line = line.rstrip("\n\r")

        if self.parser is not None:
            # Apply parser to line and return dict
            result = self.parser(line)
            if not isinstance(result, dict):
                raise ValueError(f"Parser must return a dict, got {type(result)}")
            return result
        else:
            # Return line content as string
            return line

    def write(self, record):
        """Write single line to text file

        Args:
            record: If parser is None, expects a string. If parser is provided, expects a dict
                   that will be converted back to a line (implementation depends on parser)
        """
        if self.parser is not None:
            # If parser is provided, we need to reverse the process
            # This is a limitation - we can't easily reverse parse
            # For now, if record is a dict, we'll try to convert it to string
            if isinstance(record, dict):
                # Simple conversion - join values with space
                # Users should override this or provide a custom writer
                line = " ".join(str(v) for v in record.values())
            else:
                line = str(record)
        else:
            # If no parser, record should be a string
            line = str(record)

        self.fobj.write(line + "\n")

    def write_bulk(self, records):
        """Write bulk lines to text file"""
        for record in records:
            self.write(record)
