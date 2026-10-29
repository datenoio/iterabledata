from __future__ import annotations

import typing
from itertools import islice
from typing import Any

from ..base import DEFAULT_BULK_NUMBER, BaseCodec, BaseFileIterable
from ..exceptions import FormatParseError
from ..helpers.jsonbackend import make_decoder, make_encoder, make_lines_encoder
from ..helpers.jsonvalues import encode_default, json_default_from_options
from ..helpers.utils import rowincount
from ..types import Row

# Kept for backward compatibility; the shared encoder never returns ``None`` for a value.
date_handler = encode_default


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
        self._json_default = json_default_from_options(options)
        # JSON backend (msgspec/orjson when installed, else the standard library); see jsonbackend.
        self._loads = make_decoder()
        self._dumps = make_encoder(self._json_default)
        self._dumps_lines = make_lines_encoder(self._json_default)
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

    def _remember_byte_offset(self) -> None:
        """Record the stream offset for error context (skip/warn modes and debug only)."""
        if hasattr(self.fobj, "tell"):
            try:
                self._current_byte_offset = self.fobj.tell()
            except (OSError, AttributeError):
                pass

    def _report_parse_error(self, exc: Exception, line: str) -> None:
        """Hand a line that failed to parse to the error policy (raises in ``raise`` mode)."""
        original_line = line.rstrip("\n\r")
        byte_offset = self._current_byte_offset if self._current_byte_offset > 0 else None
        error = FormatParseError(
            format_id="jsonl",
            message=str(exc),
            filename=self.filename,
            row_number=self._current_line_number,
            byte_offset=byte_offset,
            original_line=original_line,
        )
        self._handle_error(
            error,
            row_number=self._current_line_number,
            byte_offset=byte_offset,
            original_line=original_line,
        )

    def read(self, skip_empty: bool = True) -> dict:
        """Read single JSON lines record"""
        loads = self._loads
        while True:
            # ``tell`` is comparatively expensive on buffered and decompressed streams. Keep
            # offsets for diagnostics, but do not pay that cost on the normal fast path.
            if self._on_error != "raise" or self._debug:
                self._remember_byte_offset()
            line = next(self.fobj)
            self._current_line_number += 1
            try:
                result = loads(line)
            except (ValueError, TypeError, SyntaxError) as e:
                # Blank lines fail to parse too; checking for them only here keeps
                # ``strip()`` off the success path.
                if skip_empty and not line.strip():
                    continue
                self._report_parse_error(e, line)
                # The error was handled (skip/warn); continue with the next record.
                continue
            self.pos += 1
            return result

    def read_bulk(self, num: int = DEFAULT_BULK_NUMBER) -> list[dict]:
        """Read up to ``num`` JSON lines records, skipping blank lines"""
        if self._on_error != "raise" or self._debug:
            return self._read_bulk_tracked(num)
        loads = self._loads
        chunk: list[dict] = []
        append = chunk.append
        while len(chunk) < num:
            wanted = num - len(chunk)
            before = len(chunk)
            blank = 0
            for line in islice(self.fobj, wanted):
                try:
                    append(loads(line))
                except (ValueError, TypeError, SyntaxError) as e:
                    if line.strip():
                        self._current_line_number += len(chunk) - before + blank + 1
                        self.pos += len(chunk)
                        self._report_parse_error(e, line)  # raises: on_error is "raise" here
                    blank += 1
            consumed = len(chunk) - before + blank
            self._current_line_number += consumed
            if consumed < wanted:
                break
        self.pos += len(chunk)
        return chunk

    def _read_bulk_tracked(self, num: int) -> list[dict]:
        """``read_bulk`` with byte offsets and skip/warn handling, one record at a time."""
        chunk: list[dict] = []
        while len(chunk) < num:
            try:
                chunk.append(self.read())
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
        self.fobj.write(self._dumps(record) + "\n")

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
        self.fobj.write(self._dumps_lines(records))
