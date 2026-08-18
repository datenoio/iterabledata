from __future__ import annotations

import logging
import typing
from csv import DictReader, DictWriter
from typing import Any

import chardet

from ..base import DEFAULT_BULK_NUMBER, ITERABLE_TYPE_FILE, BaseCodec, BaseFileIterable
from ..exceptions import FormatParseError
from ..helpers.utils import rowincount
from ..types import Row

DEFAULT_ENCODING = "utf8"
DEFAULT_DELIMITER = ","


def _rewind_stream(stream, pos) -> None:
    """Restore a stream to a previous position, tolerating non-seekable streams."""
    if pos is not None and hasattr(stream, "seek"):
        try:
            stream.seek(pos)
            return
        except (OSError, ValueError):
            pass
    if hasattr(stream, "reset"):
        stream.reset()


def detect_encoding_raw(filename=None, stream=None, limit=1000000):
    if filename is not None:
        with open(filename, "rb") as f:
            chunk = f.read(limit)
    else:
        pos = stream.tell() if hasattr(stream, "tell") else None
        chunk = stream.read(limit)
        _rewind_stream(stream, pos)
        # Text streams (e.g. io.StringIO) already yield decoded ``str`` data, so
        # byte-oriented encoding detection is neither possible nor meaningful.
        if isinstance(chunk, str):
            return {"encoding": DEFAULT_ENCODING}
    # Prefer UTF-8 when the sample decodes cleanly: chardet can mis-identify short
    # multilingual UTF-8 samples (e.g. CJK/emoji) as a single-byte codepage.
    try:
        chunk.decode("utf-8")
        logging.debug("Detected encoding utf-8 (clean UTF-8 decode)")
        return {"encoding": "utf-8", "confidence": 1.0}
    except UnicodeDecodeError:
        pass
    detected = chardet.detect(chunk)
    logging.debug("Detected encoding {}".format(detected["encoding"]))
    return detected


def detect_delimiter(filename=None, stream=None, encoding="utf8"):
    if filename is not None:
        with open(filename, encoding=encoding) as f:
            line = f.readline()
    else:
        pos = stream.tell() if hasattr(stream, "tell") else None
        line = stream.readline()
        _rewind_stream(stream, pos)
    dict1 = {",": line.count(","), ";": line.count(";"), "\t": line.count("\t"), "|": line.count("|")}
    delimiter = max(dict1, key=dict1.get)
    logging.debug(f"Detected delimiter {delimiter}")
    return delimiter


class CSVIterable(BaseFileIterable):
    def __init__(
        self,
        filename: str | None = None,
        stream: typing.IO[Any] | None = None,
        codec: BaseCodec | None = None,
        keys: list[str] | None = None,
        delimiter: str | None = None,
        quotechar: str = '"',
        mode: str = "r",
        encoding: str | None = None,
        autodetect: bool = False,
        options: dict[str, Any] | None = None,
    ):
        if options is None:
            options = {}
        logging.debug(f"Params: encoding: {encoding}, options {options}")
        self.encoding = None
        self.fileobj = stream
        if encoding is not None:
            self.encoding = encoding
        elif "encoding" in options.keys() and options["encoding"] is not None:
            self.encoding = options["encoding"]
        if mode == "r":
            if filename is not None and stream is None and self.encoding is None:
                self.encoding = detect_encoding_raw(filename=filename)["encoding"]
            elif stream is not None and self.encoding is None:
                self.encoding = detect_encoding_raw(stream=stream)["encoding"]
            elif self.encoding is None:
                self.encoding = DEFAULT_ENCODING
        elif self.encoding is None:
            self.encoding = DEFAULT_ENCODING
        logging.debug(f"Final encoding {self.encoding}")
        self.keys = keys

        super().__init__(
            filename, stream, codec=codec, binary=False, encoding=self.encoding, mode=mode, options=options
        )
        if not delimiter:
            if autodetect and mode == "r":
                #                print(filename, stream)
                self.delimiter = detect_delimiter(filename, self.fobj, encoding=self.encoding)
            else:
                self.delimiter = DEFAULT_DELIMITER
        else:
            self.delimiter = delimiter
        self.quotechar = quotechar
        logging.debug(f"Detected delimiter {self.delimiter}")
        self.reset()
        pass

    @staticmethod
    def has_totals() -> bool:
        """Has totals indicator"""
        return True

    def totals(self) -> int:
        """Returns file totals"""
        return rowincount(self.filename, self.fobj)

    def reset(self) -> None:
        super().reset()
        if self.fobj is None and self.codec is not None:
            fobj = self.codec.textIO(self.encoding)
        else:
            fobj = self.fobj
        logging.debug(f"Detected delimiter {self.delimiter}")
        self.reader = None
        if self.mode == "r":
            if self.keys is not None:
                self.reader = DictReader(fobj, fieldnames=self.keys, delimiter=self.delimiter, quotechar=self.quotechar)
            else:
                self.reader = DictReader(fobj, delimiter=self.delimiter, quotechar=self.quotechar)
        if self.mode in ["w", "wr"] and self.keys is not None:
            self.writer = DictWriter(fobj, fieldnames=self.keys, delimiter=self.delimiter, quotechar=self.quotechar)
            self.writer.writeheader()
        else:
            self.writer = None

        #            self.reader = reader(self.fobj, delimiter=self.delimiter, quotechar=self.quotechar)
        self.pos = 0
        # Reset line tracking for error context
        self._current_line = None
        self._current_line_number = 0
        self._current_byte_offset = 0

    def open(self) -> typing.IO[Any] | None:
        """Open text CSV with newline='' so the csv module does not double-translate CR on Windows."""
        if self.stype == ITERABLE_TYPE_FILE and not self.binary:
            self._closed = False
            if self.filename is None:
                raise ValueError("Cannot open file: filename is None")
            self.fobj = open(self.filename, self.mode, encoding=self.encoding, newline="")
            return self.fobj
        return super().open()

    @staticmethod
    def id() -> str:
        return "csv"

    @staticmethod
    def is_flatonly() -> bool:
        return True

    def read(self, skip_empty: bool = True) -> Row:
        """Read single CSV record"""
        while True:
            try:
                # Try to get the raw line before parsing
                # DictReader doesn't expose the raw line, so we need to track it
                # For now, we'll track line number and try to get byte offset
                if hasattr(self.fobj, "tell"):
                    try:
                        self._current_byte_offset = self.fobj.tell()
                    except (OSError, AttributeError):
                        pass

                row = next(self.reader)
                self._current_line_number = self.reader.line_num

                # Try to get the original line if possible
                # Note: DictReader doesn't expose raw lines, so we'll set it to None
                # Format-specific implementations can override this
                self._current_line = None

                if skip_empty and len(row) == 0:
                    continue

                self.pos += 1
                return row
            except StopIteration:
                raise
            except Exception as e:
                # Handle parse errors according to error policy
                error = FormatParseError(
                    format_id="csv",
                    message=str(e),
                    filename=self.filename,
                    row_number=self._current_line_number if self._current_line_number > 0 else self.pos + 1,
                    byte_offset=self._current_byte_offset if self._current_byte_offset > 0 else None,
                    original_line=self._current_line,
                )
                self._handle_error(
                    error,
                    row_number=self._current_line_number if self._current_line_number > 0 else self.pos + 1,
                    byte_offset=self._current_byte_offset if self._current_byte_offset > 0 else None,
                    original_line=self._current_line,
                )
                # If we get here, error was handled (skip/warn), continue to next record
                continue

    def read_bulk(self, num: int = DEFAULT_BULK_NUMBER) -> list[Row]:
        """Read bulk CSV records efficiently"""
        chunk = []
        for _n in range(0, num):
            try:
                if hasattr(self.fobj, "tell"):
                    try:
                        self._current_byte_offset = self.fobj.tell()
                    except (OSError, AttributeError):
                        pass

                row = next(self.reader)
                self._current_line_number = self.reader.line_num
                self._current_line = None

                chunk.append(row)
                self.pos += 1
            except StopIteration:
                break
            except Exception as e:
                # Handle parse errors according to error policy
                error = FormatParseError(
                    format_id="csv",
                    message=str(e),
                    filename=self.filename,
                    row_number=self._current_line_number if self._current_line_number > 0 else self.pos + 1,
                    byte_offset=self._current_byte_offset if self._current_byte_offset > 0 else None,
                    original_line=self._current_line,
                )
                self._handle_error(
                    error,
                    row_number=self._current_line_number if self._current_line_number > 0 else self.pos + 1,
                    byte_offset=self._current_byte_offset if self._current_byte_offset > 0 else None,
                    original_line=self._current_line,
                )
                # If we get here, error was handled (skip/warn), continue to next record
                continue
        return chunk

    def is_streaming(self) -> bool:
        """Returns True - CSV always streams row by row"""
        return True

    def _ensure_writer(self, record: Row) -> None:
        """Create writer on first write when keys were not set at open."""
        if self.writer is None and self.mode in ["w", "wr"] and self.fobj is not None:
            self.keys = list(record.keys()) if isinstance(record, dict) else list(record)
            self.writer = DictWriter(
                self.fobj, fieldnames=self.keys, delimiter=self.delimiter, quotechar=self.quotechar
            )
            self.writer.writeheader()

    def write(self, record: Row) -> None:
        """Write single CSV record"""
        # Apply validation hooks if configured
        if self._validation_hooks:
            validated = self._apply_validation_hooks(record)
            if validated is None:  # Skipped
                return  # Don't write invalid row
            record = validated
        self._ensure_writer(record)
        self.writer.writerow(record)

    def write_bulk(self, records: list[Row]) -> None:
        """Write bulk CSV records"""
        if records is None:
            raise TypeError("write_bulk() requires a list of records, got None")
        # Apply validation hooks if configured
        if self._validation_hooks:
            validated_records = []
            for record in records:
                validated = self._apply_validation_hooks(record)
                if validated is not None:  # Not skipped
                    validated_records.append(validated)
            records = validated_records
        if not records:
            return
        self._ensure_writer(records[0])
        self.writer.writerows(records)
