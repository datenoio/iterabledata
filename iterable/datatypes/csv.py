from __future__ import annotations

import importlib.util
import logging
import os
import typing
from collections.abc import Iterable, Mapping
from csv import reader as csv_reader
from csv import writer as csv_writer
from itertools import islice
from operator import itemgetter
from typing import Any

import chardet

from ..base import DEFAULT_BULK_NUMBER, ITERABLE_TYPE_CODEC, ITERABLE_TYPE_FILE, BaseCodec, BaseFileIterable
from ..exceptions import FormatParseError
from ..helpers.utils import rowincount
from ..types import Row

DEFAULT_ENCODING = "utf8"
DEFAULT_DELIMITER = ","
DEFAULT_QUOTECHAR = '"'
TSV_DELIMITER = "\t"
TSV_EXTENSIONS = ("tsv",)
# Codec extensions whose streams PyArrow decompresses itself on the native batch path.
ARROW_COMPRESSION = {"gz": "gzip", "bz2": "bz2", "zst": "zstd", "zstd": "zstd"}


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


def _is_tsv_name(name: str | None) -> bool:
    """True when ``name`` ends in ``.tsv``, optionally followed by a compression extension."""
    if not name:
        return False
    parts = str(name).lower().rsplit(".", 2)
    if len(parts) < 2:
        return False
    if parts[-1] in TSV_EXTENSIONS:
        return True
    if len(parts) == 3 and parts[-2] in TSV_EXTENSIONS:
        from ..helpers.detect import _get_codec_registry

        return parts[-1] in _get_codec_registry()
    return False


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


class _DictRowReader:
    """``csv.DictReader`` on top of ``csv.reader``, with a batch fast path.

    Records are the same as ``DictReader``'s with ``restkey=None`` and ``restval=None``: rows
    shorter than the header get ``None`` for the missing fields, extra values of longer rows go
    to a list under the ``None`` key, and blank lines are skipped.
    """

    def __init__(self, f: Iterable[str], fieldnames: typing.Sequence[str] | None = None, **dialect: Any) -> None:
        self.reader = csv_reader(f, **dialect)
        self._fieldnames = fieldnames
        self.line_num = 0

    @property
    def fieldnames(self) -> typing.Sequence[str] | None:
        if self._fieldnames is None:
            try:
                self._fieldnames = next(self.reader)
            except StopIteration:
                pass
        self.line_num = self.reader.line_num
        return self._fieldnames

    @fieldnames.setter
    def fieldnames(self, value: typing.Sequence[str] | None) -> None:
        self._fieldnames = value

    def __iter__(self) -> _DictRowReader:
        return self

    def __next__(self) -> dict[Any, Any]:
        if self.line_num == 0:
            self.fieldnames  # noqa: B018 - reads the header, as DictReader does
        row = next(self.reader)
        self.line_num = self.reader.line_num
        while row == []:
            row = next(self.reader)
        fieldnames = self._fieldnames
        if fieldnames is not None and len(row) == len(fieldnames):
            return dict(zip(fieldnames, row, strict=False))
        return self._record(row)

    def _record(self, row: list[str]) -> dict[Any, Any]:
        fieldnames = self._fieldnames or ()
        record: dict[Any, Any] = dict(zip(fieldnames, row, strict=False))
        if len(fieldnames) < len(row):
            record[None] = row[len(fieldnames) :]
        elif len(fieldnames) > len(row):
            for key in fieldnames[len(row) :]:
                record[key] = None
        return record

    def read_many(self, num: int) -> list[dict[Any, Any]]:
        """Up to ``num`` records; fewer only at the end of the input."""
        if self.line_num == 0:
            self.fieldnames  # noqa: B018 - reads the header, as DictReader does
        fieldnames = self._fieldnames or ()
        width = len(fieldnames)
        chunk: list[dict[Any, Any]] = []
        append = chunk.append
        while len(chunk) < num:
            wanted = num - len(chunk)
            before = len(chunk)
            blank = 0
            for row in islice(self.reader, wanted):
                if len(row) == width:
                    append(dict(zip(fieldnames, row, strict=False)))
                elif row:
                    append(self._record(row))
                else:
                    blank += 1
            self.line_num = self.reader.line_num
            if len(chunk) - before + blank < wanted:
                break
        return chunk


class _DictRowWriter:
    """``csv.DictWriter`` (``restval=""``, ``extrasaction="raise"``) on top of ``csv.writer``.

    Records whose keys are exactly the header are projected with ``itemgetter``; others are
    checked for unknown fields and padded with ``""``, as ``DictWriter`` does.
    """

    def __init__(self, f: typing.IO[str], fieldnames: Iterable[str], **dialect: Any) -> None:
        self.fieldnames = list(fieldnames)
        self.writer = csv_writer(f, **dialect)
        self._keys = frozenset(self.fieldnames)
        self._project: typing.Callable[[Mapping[Any, Any]], Any]
        if not self.fieldnames:
            self._project = lambda record: ()
        elif len(self.fieldnames) == 1:
            # ``itemgetter`` with one key returns the value itself, not a 1-tuple.
            key = self.fieldnames[0]
            self._project = lambda record: (record[key],)
        else:
            self._project = itemgetter(*self.fieldnames)

    def _row(self, record: Mapping[Any, Any]) -> Any:
        if record.keys() == self._keys:
            return self._project(record)
        unknown = record.keys() - self._keys
        if unknown:
            raise ValueError("dict contains fields not in fieldnames: " + ", ".join([repr(x) for x in unknown]))
        return [record.get(key, "") for key in self.fieldnames]

    def writeheader(self) -> Any:
        return self.writer.writerow(self.fieldnames)

    def writerow(self, record: Mapping[Any, Any]) -> Any:
        return self.writer.writerow(self._row(record))

    def writerows(self, records: Iterable[Mapping[Any, Any]]) -> None:
        self.writer.writerows(map(self._row, records))


class CSVIterable(BaseFileIterable):
    # The csv module needs untranslated line endings, also through codecs (``.csv.gz``):
    # universal-newline mode turns its ``\r\n`` into ``\r\r\n`` on Windows.
    text_newline = ""
    # Native batches: rows via ``read_batches``; Arrow batches when PyArrow is installed.
    supports_native_batch = True

    def __init__(
        self,
        filename: str | None = None,
        stream: typing.IO[Any] | None = None,
        codec: BaseCodec | None = None,
        keys: list[str] | None = None,
        delimiter: str | None = None,
        quotechar: str | None = None,
        mode: str = "r",
        encoding: str | None = None,
        autodetect: bool = False,
        options: dict[str, Any] | None = None,
    ):
        if options is None:
            options = {}
        logging.debug(f"Params: encoding: {encoding}, options {options}")
        self.fileobj = stream
        self.encoding = self._resolve_encoding(encoding, options, filename, stream, mode)
        logging.debug(f"Final encoding {self.encoding}")
        # Constructor arguments win; otherwise take the dialect from ``options`` (that is,
        # ``open_iterable(iterableargs=...)``), then the extension default, then autodetection.
        self.keys = keys if keys is not None else options.get("keys")
        delimiter = delimiter if delimiter is not None else options.get("delimiter")
        quotechar = quotechar if quotechar is not None else options.get("quotechar")
        autodetect = autodetect or bool(options.get("autodetect", False))
        self.escapechar = options.get("escapechar")
        self.doublequote = options.get("doublequote", True)

        super().__init__(
            filename, stream, codec=codec, binary=False, encoding=self.encoding, mode=mode, options=options
        )
        self.delimiter = delimiter or self._default_delimiter(filename, codec, options, autodetect and mode == "r")
        self.quotechar = quotechar or DEFAULT_QUOTECHAR
        logging.debug(f"Detected delimiter {self.delimiter}")
        self.reset()

    @staticmethod
    def _resolve_encoding(
        encoding: str | None,
        options: dict[str, Any],
        filename: str | None,
        stream: typing.IO[Any] | None,
        mode: str,
    ) -> str:
        """Explicit encoding, then ``options["encoding"]``, then detection when reading."""
        if encoding is None:
            encoding = options.get("encoding")
        if encoding is not None:
            return encoding
        if mode == "r" and stream is not None:
            return detect_encoding_raw(stream=stream)["encoding"]
        if mode == "r" and filename is not None:
            return detect_encoding_raw(filename=filename)["encoding"]
        return DEFAULT_ENCODING

    def _default_delimiter(
        self, filename: str | None, codec: BaseCodec | None, options: dict[str, Any], autodetect: bool
    ) -> str:
        """Tab for TSV sources, the detected delimiter with ``autodetect``, else a comma."""
        if self._is_tsv_source(filename, codec, options):
            return TSV_DELIMITER
        if autodetect:
            return detect_delimiter(filename, self.fobj, encoding=self.encoding)
        return DEFAULT_DELIMITER

    @staticmethod
    def _is_tsv_source(filename: str | None, codec: BaseCodec | None, options: dict[str, Any]) -> bool:
        """Whether the source is tab-separated by its explicit format or its file name."""
        if str(options.get("format") or "").lower() in TSV_EXTENSIONS:
            return True
        return _is_tsv_name(filename) or _is_tsv_name(getattr(codec, "filename", None))

    def _dialect(self) -> dict[str, Any]:
        """Keyword arguments for ``csv.reader``/``csv.writer``."""
        return {
            "delimiter": self.delimiter,
            "quotechar": self.quotechar,
            "escapechar": self.escapechar,
            "doublequote": self.doublequote,
        }

    @staticmethod
    def has_totals() -> bool:
        """Has totals indicator"""
        return True

    def totals(self) -> int:
        """Return the number of data rows, counted by lines.

        The header line is not counted when the header is read from the file. Quoted
        fields that contain line breaks make this an over-estimate.
        """
        total = rowincount(self.filename, self.fobj, include_unterminated=True)
        if self.mode == "r" and self.keys is None and total > 0:
            total -= 1
        return total

    def reset(self) -> None:
        super().reset()
        if self.fobj is None and self.codec is not None:
            fobj = self._codec_text_io()
        else:
            fobj = self.fobj
        logging.debug(f"Detected delimiter {self.delimiter}")
        self.reader = None
        if self.mode == "r":
            self.reader = _DictRowReader(fobj, fieldnames=self.keys, **self._dialect())
        if self.mode in ["w", "wr"] and self.keys is not None:
            self.writer = _DictRowWriter(fobj, fieldnames=self.keys, **self._dialect())
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

    def _row_reader(self) -> _DictRowReader:
        if self.reader is None:
            raise ValueError("CSV iterable is not open for reading")
        return self.reader

    def _report_parse_error(self, exc: Exception) -> None:
        """Hand a row that failed to parse to the error policy (raises in ``raise`` mode)."""
        # The underlying ``csv.reader`` has already counted the line that failed.
        line_num = getattr(getattr(self.reader, "reader", self.reader), "line_num", 0)
        if line_num:
            self._current_line_number = line_num
        row_number = self._current_line_number if self._current_line_number > 0 else self.pos + 1
        byte_offset = self._current_byte_offset if self._current_byte_offset > 0 else None
        error = FormatParseError(
            format_id="csv",
            message=str(exc),
            filename=self.filename,
            row_number=row_number,
            byte_offset=byte_offset,
            original_line=self._current_line,
        )
        self._handle_error(error, row_number=row_number, byte_offset=byte_offset, original_line=self._current_line)

    def read(self, skip_empty: bool = True) -> Row:
        """Read single CSV record"""
        if self._on_error != "raise" or self._debug:
            return self._read_tracked(skip_empty)
        reader = self.reader
        while True:
            try:
                row = next(reader)
            except StopIteration:
                raise
            except Exception as e:
                self._report_parse_error(e)
                continue
            if row or not skip_empty:
                self.pos += 1
                return row

    def _read_tracked(self, skip_empty: bool = True) -> Row:
        """``read`` that records byte offsets and line numbers for skip/warn handling and debug."""
        while True:
            if hasattr(self.fobj, "tell"):
                try:
                    self._current_byte_offset = self.fobj.tell()
                except (OSError, AttributeError):
                    pass
            try:
                row = next(self.reader)
            except StopIteration:
                raise
            except Exception as e:
                self._report_parse_error(e)
                # The error was handled (skip/warn); continue with the next record.
                continue
            self._current_line_number = self.reader.line_num
            if skip_empty and len(row) == 0:
                continue
            self.pos += 1
            return row

    def read_bulk(self, num: int = DEFAULT_BULK_NUMBER) -> list[Row]:
        """Read bulk CSV records efficiently"""
        if self._on_error != "raise" or self._debug:
            return self._read_bulk_tracked(num)
        try:
            chunk = self._row_reader().read_many(num)
        except Exception as e:
            self._report_parse_error(e)  # raises: on_error is "raise" here
            raise
        self.pos += len(chunk)
        return chunk

    def _read_bulk_tracked(self, num: int) -> list[Row]:
        """``read_bulk`` with byte offsets and skip/warn handling, one record at a time."""
        chunk: list[Row] = []
        while len(chunk) < num:
            try:
                chunk.append(self._read_tracked(skip_empty=False))
            except StopIteration:
                break
        return chunk

    def is_streaming(self) -> bool:
        """Returns True - CSV always streams row by row"""
        return True

    def read_batches(self, selection: Any = None) -> typing.Iterator[list[Row]]:
        """Native row-batch hook: the row reader with the selection applied row-wise."""
        from ..convert.batch import BatchSelection, chunk_rows, select_rows

        selection = selection or BatchSelection()
        if selection.table is not None:
            raise NotImplementedError("CSV has no tables")
        yield from chunk_rows(select_rows(self, selection), selection.batch_size or DEFAULT_BULK_NUMBER)

    @property
    def supports_arrow_batches(self) -> bool:
        """Arrow batches need PyArrow."""
        return importlib.util.find_spec("pyarrow") is not None

    def _arrow_source(self) -> Any:
        """A PyArrow input stream over the file, decompressing ``.gz``/``.bz2``/``.zst`` itself."""
        import pyarrow

        if self.stype == ITERABLE_TYPE_FILE and self.filename:
            return pyarrow.input_stream(self.filename, compression=None)
        codec_file = getattr(self.codec, "filename", None)
        if self.stype == ITERABLE_TYPE_CODEC and codec_file and os.path.isfile(codec_file):
            compression = ARROW_COMPRESSION.get(str(codec_file).rsplit(".", 1)[-1].lower())
            if compression is not None:
                return pyarrow.input_stream(codec_file, compression=compression)
        raise NotImplementedError("Native CSV batches need a local file, plain or .gz/.bz2/.zst")

    def _arrow_options(self, names: list[str], columns: list[str] | None) -> dict[str, Any]:
        """``pyarrow.csv.open_csv`` options matching the row reader: every column a string."""
        import pyarrow
        import pyarrow.csv as pacsv

        return {
            "read_options": pacsv.ReadOptions(
                column_names=names, skip_rows=0 if self.keys is not None else 1, encoding=self.encoding
            ),
            "parse_options": pacsv.ParseOptions(
                delimiter=self.delimiter,
                quote_char=self.quotechar or False,
                double_quote=self.doublequote,
                escape_char=self.escapechar or False,
                newlines_in_values=True,
                ignore_empty_lines=True,
            ),
            "convert_options": pacsv.ConvertOptions(
                column_types={name: pyarrow.string() for name in names},
                strings_can_be_null=False,
                quoted_strings_can_be_null=False,
                include_columns=columns,
            ),
        }

    def _arrow_columns(self, selection: Any) -> tuple[list[str], list[str] | None]:
        """Header names and projected columns, or ``NotImplementedError`` for the row path."""
        unsupported = (selection.predicate, selection.table, selection.row_range, selection.slice)
        if any(value is not None for value in unsupported):
            raise NotImplementedError("Native CSV batches support column projection only")
        if self.mode != "r" or self.pos != 0:
            raise NotImplementedError("Native CSV batches need a fresh reader")
        names = list(self.keys) if self.keys is not None else list(self._row_reader().fieldnames or [])
        columns = list(selection.columns) if selection.columns is not None else None
        if not names or len(set(names)) != len(names) or not set(columns or ()) <= set(names):
            raise NotImplementedError("Native CSV batches need unique header names covering the selection")
        return names, columns

    def read_arrow_batches(self, selection: Any = None) -> typing.Iterator[Any]:
        """Yield ``pyarrow.RecordBatch`` objects with every column typed as string.

        Values equal the row reader's (no type inference; empty fields stay ``""``). Column
        projection is pushed down; predicates and row windows raise ``NotImplementedError``
        so ``convert()`` uses the row path. Every row must have as many fields as the header.
        """
        import pyarrow
        import pyarrow.csv as pacsv

        from ..convert.batch import BatchSelection

        names, columns = self._arrow_columns(selection or BatchSelection())
        source = self._arrow_source()
        try:
            for batch in pacsv.open_csv(source, **self._arrow_options(names, columns)):
                self.pos += batch.num_rows
                yield batch
        except pyarrow.ArrowInvalid as e:
            raise FormatParseError(
                format_id="csv",
                message=f"{e}. The native batch path needs every row to have the header's fields; "
                "read ragged files with use_native_batch=False.",
                filename=self.filename,
            ) from e
        finally:
            source.close()

    def _ensure_writer(self, record: Row) -> None:
        """Create writer on first write when keys were not set at open."""
        if self.writer is None and self.mode in ["w", "wr"] and self.fobj is not None:
            self.keys = list(record.keys()) if isinstance(record, dict) else list(record)
            self.writer = _DictRowWriter(self.fobj, fieldnames=self.keys, **self._dialect())
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
