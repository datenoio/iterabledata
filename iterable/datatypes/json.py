from __future__ import annotations

import json
import os
import typing
from typing import Any

try:
    import ijson

    HAS_IJSON = True
except ImportError:
    HAS_IJSON = False

from ..base import DEFAULT_BULK_NUMBER, BaseCodec, BaseFileIterable
from ..exceptions import FormatParseError, WriteError
from ..types import Row


class JSONIterable(BaseFileIterable):
    def __init__(
        self,
        filename: str = None,
        stream: typing.IO[Any] | None = None,
        codec: BaseCodec | None = None,
        mode="r",
        tagname: str = None,
        options: dict[str, Any] | None = None,
    ):
        if options is None:
            options = {}
        self.tagname = tagname or options.get("tagname")
        self._streaming = False
        self._parser = None
        self._items_buffer = []
        super().__init__(filename, stream, codec=codec, mode=mode, binary=False, options=options)
        self.reset()
        pass

    def _should_use_streaming(self) -> bool:
        """Determine if streaming parser should be used"""
        if not HAS_IJSON:
            return False
        # Use streaming for files larger than 10MB or non-seekable streams
        if self.filename:
            try:
                file_size = os.path.getsize(self.filename)
                return file_size > 10 * 1024 * 1024  # 10MB threshold
            except (OSError, TypeError):
                # Can't determine size, use streaming for safety
                return True
        # For streams without filename, use streaming if not seekable
        if hasattr(self.fobj, "seekable"):
            return not self.fobj.seekable()
        # Default to streaming for unknown cases
        return True

    def reset(self):
        super().reset()
        self.pos = 0
        self._streaming = False
        self._parser = None
        self._items_buffer = []
        self._parse_error = None
        if self.mode in ["w", "wr"]:
            # Re-initialize output (truncate if needed) and prepare streaming JSON writing.
            if hasattr(self.fobj, "seek") and hasattr(self.fobj, "truncate"):
                try:
                    self.fobj.seek(0)
                    self.fobj.truncate(0)
                except Exception:
                    # Best-effort; some streams may not support truncation.
                    pass
            self._write_started = True
            self._first_item = True
            # Support optional wrapper object with a list under tagname.
            if self.tagname:
                self.fobj.write('{"' + str(self.tagname) + '":[')
            else:
                self.fobj.write("[")
            self.total = 0
            self.data = None
        else:
            # Determine if we should use streaming parser
            if self._should_use_streaming():
                # Use streaming parser
                self._streaming = True
                self.fobj.seek(0)
                if self.tagname:
                    # Parse items from a specific key in the JSON object
                    self._parser = ijson.items(self.fobj, self.tagname + ".item")
                else:
                    # Parse items from a JSON array
                    self._parser = ijson.items(self.fobj, "item")
                # Pre-fetch first item to check if parser works
                try:
                    self._first_item = next(self._parser)
                    self._items_buffer = [self._first_item]
                    self.total = None  # Unknown total for streaming
                except StopIteration:
                    self._items_buffer = []
                    self.total = 0
            else:
                # Use traditional json.load() for small files
                self._streaming = False
                try:
                    self.data = json.load(self.fobj)
                except (json.JSONDecodeError, ValueError) as e:
                    # Defer malformed/empty JSON errors to read() so that opening
                    # the iterable succeeds and the error surfaces during iteration.
                    self._parse_error = FormatParseError(format_id="json", message=str(e), filename=self.filename)
                    self.data = []
                    self.total = 0
                    return
                if self.tagname:
                    self.data = self.data[self.tagname]
                self.total = len(self.data)

    @staticmethod
    def id() -> str:
        return "json"

    @staticmethod
    def has_totals() -> bool:
        """Has totals indicator"""
        return True

    def totals(self):
        """Returns file totals"""
        if self.total is None:
            # For streaming mode, total is unknown
            return None
        return self.total

    @staticmethod
    def is_flatonly() -> bool:
        return False

    def is_streaming(self) -> bool:
        """Returns True if using streaming parser"""
        return self._streaming

    def read(self, skip_empty: bool = True) -> dict:
        """Read single JSON record"""
        if self._streaming:
            # Use streaming parser
            if self._items_buffer:
                # Return buffered item
                item = self._items_buffer.pop(0)
                self.pos += 1
                return item
            # Try to get next item from parser
            try:
                item = next(self._parser)
                self.pos += 1
                return item
            except StopIteration:
                raise StopIteration from None
        else:
            if self._parse_error is not None:
                raise self._parse_error
            # Use loaded data
            if self.pos >= self.total:
                raise StopIteration
            row = self.data[self.pos]
            self.pos += 1
            return row

    def read_bulk(self, num: int = DEFAULT_BULK_NUMBER) -> list[dict]:
        """Read bulk JSON records"""
        chunk = []
        if self._streaming:
            # For streaming, read from buffer first, then parser
            while len(chunk) < num:
                if self._items_buffer:
                    chunk.append(self._items_buffer.pop(0))
                    self.pos += 1
                else:
                    try:
                        item = next(self._parser)
                        chunk.append(item)
                        self.pos += 1
                    except StopIteration:
                        break
        else:
            if self._parse_error is not None:
                raise self._parse_error
            # For non-streaming, use efficient slicing
            remaining = self.total - self.pos
            if remaining == 0:
                return []
            read_count = min(num, remaining)
            chunk = self.data[self.pos : self.pos + read_count]
            self.pos += read_count
        return chunk

    def write(self, record: Row) -> None:
        """Write single JSON record (array item)."""
        if self._validation_hooks:
            validated = self._apply_validation_hooks(record)
            if validated is None:
                return
            record = validated
        self.write_bulk([record])

    def write_bulk(self, records: list[Row]) -> None:
        """Write bulk JSON records (array items)."""
        if self.mode not in ["w", "wr"]:
            raise WriteError(
                "Write mode not enabled",
                filename=self.filename,
                error_code="INVALID_MODE",
            )
        if self._validation_hooks:
            validated_records = []
            for record in records:
                validated = self._apply_validation_hooks(record)
                if validated is not None:
                    validated_records.append(validated)
            records = validated_records
        if not records:
            return
        for record in records:
            if not getattr(self, "_first_item", True):
                self.fobj.write(",")
            self.fobj.write(json.dumps(record, ensure_ascii=False, default=str))
            self._first_item = False
            self.total += 1

    def close(self):
        """Close iterable and finalize JSON output if writing."""
        if self.mode in ["w", "wr"] and getattr(self, "_write_started", False):
            if self.tagname:
                self.fobj.write("]}")
            else:
                self.fobj.write("]")
        super().close()
