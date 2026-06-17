from __future__ import annotations

import datetime
import typing
from json import dumps, loads
from typing import Any

from ..base import DEFAULT_BULK_NUMBER, BaseCodec, BaseFileIterable
from ..exceptions import FormatParseError
from ..helpers.utils import rowincount
from ..types import Row


def date_handler(obj):
    return obj.isoformat() if isinstance(obj, (datetime.datetime, datetime.date)) else None


class JSONLinesIterable(BaseFileIterable):
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
        self.pos = 0
        super().__init__(filename, stream, codec=codec, binary=False, mode=mode, encoding=encoding, options=options)
        # Track line number and byte offset for error context
        self._current_line_number = 0
        self._current_byte_offset = 0

    @staticmethod
    def id() -> str:
        return "jsonl"

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

    def reset(self):
        """Reset iterator and line tracking"""
        super().reset()
        self._current_line_number = 0
        self._current_byte_offset = 0

    def read(self, skip_empty: bool = True) -> dict:
        """Read single JSON lines record"""
        while True:
            try:
                # Get byte offset before reading
                if hasattr(self.fobj, "tell"):
                    try:
                        self._current_byte_offset = self.fobj.tell()
                    except (OSError, AttributeError):
                        pass

                line = next(self.fobj)
                self._current_line_number += 1

                if skip_empty and len(line.strip()) == 0:
                    continue

                original_line = line.rstrip("\n\r")

                if line:
                    try:
                        result = loads(line)
                        self.pos += 1
                        return result
                    except (ValueError, TypeError, SyntaxError) as e:
                        # JSON parse error
                        error = FormatParseError(
                            format_id="jsonl",
                            message=str(e),
                            filename=self.filename,
                            row_number=self._current_line_number,
                            byte_offset=self._current_byte_offset if self._current_byte_offset > 0 else None,
                            original_line=original_line,
                        )
                        self._handle_error(
                            error,
                            row_number=self._current_line_number,
                            byte_offset=self._current_byte_offset if self._current_byte_offset > 0 else None,
                            original_line=original_line,
                        )
                        # If we get here, error was handled (skip/warn), continue to next record
                        continue
                return None
            except StopIteration:
                raise

    def read_bulk(self, num: int = DEFAULT_BULK_NUMBER) -> list[dict]:
        """Read bulk JSON lines records efficiently"""
        chunk = []
        for _n in range(0, num):
            try:
                # Get byte offset before reading
                if hasattr(self.fobj, "tell"):
                    try:
                        self._current_byte_offset = self.fobj.tell()
                    except (OSError, AttributeError):
                        pass

                line = self.fobj.readline()
                if not line:
                    break

                self._current_line_number += 1
                original_line = line.rstrip("\n\r")
                line = line.strip()

                if line:
                    try:
                        chunk.append(loads(line))
                        self.pos += 1
                    except (ValueError, TypeError, SyntaxError) as e:
                        # JSON parse error
                        error = FormatParseError(
                            format_id="jsonl",
                            message=str(e),
                            filename=self.filename,
                            row_number=self._current_line_number,
                            byte_offset=self._current_byte_offset if self._current_byte_offset > 0 else None,
                            original_line=original_line,
                        )
                        self._handle_error(
                            error,
                            row_number=self._current_line_number,
                            byte_offset=self._current_byte_offset if self._current_byte_offset > 0 else None,
                            original_line=original_line,
                        )
                        # If we get here, error was handled (skip/warn), continue to next record
                        continue
            except StopIteration:
                break
        return chunk

    def is_streaming(self) -> bool:
        """Returns True - JSONL always streams line by line"""
        return True

    def write(self, record: Row) -> None:
        """Write single JSON lines record"""
        if self._validation_hooks:
            validated = self._apply_validation_hooks(record)
            if validated is None:
                return
            record = validated
        self.fobj.write(dumps(record, ensure_ascii=False, default=date_handler) + "\n")

    def write_bulk(self, records: list[Row]) -> None:
        """Write bulk JSON lines records"""
        if self._validation_hooks:
            validated_records = []
            for record in records:
                validated = self._apply_validation_hooks(record)
                if validated is not None:
                    validated_records.append(validated)
            records = validated_records
        if not records:
            return
        # Minimize per-record I/O by writing a single concatenated batch.
        batch = "\n".join(dumps(r, ensure_ascii=False, default=date_handler) for r in records)
        self.fobj.write(batch + "\n")
