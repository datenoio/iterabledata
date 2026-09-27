from __future__ import annotations

import typing
from collections import deque
from typing import Any

try:
    import pyorc

    HAS_PYORC = True
except ImportError:
    pyorc = None
    HAS_PYORC = False

try:
    import pyarrow
    import pyarrow.orc

    HAS_PYARROW_ORC = True
except ImportError:
    pyarrow = None
    HAS_PYARROW_ORC = False

from ..base import DEFAULT_BULK_NUMBER, BaseCodec, BaseFileIterable
from ..convert.batch import BatchSelection, chunk_rows, resolve_row_window, select_rows, to_pyarrow_expression
from ..types import Row

DEFAULT_BATCH_SIZE = 1024

# pyorc CompressionKind integer values mapped to pyarrow.orc compression names.
_PYORC_TO_PYARROW_COMPRESSION = {
    0: "uncompressed",  # NONE
    1: "zlib",  # ZLIB
    2: "snappy",  # SNAPPY
    4: "lz4",  # LZ4
    5: "zstd",  # ZSTD
}


def df_to_pyorc_schema(df):
    """Extracts column information from pandas dataframe and generate pyorc schema"""
    struct_schema = []
    for k, v in df.dtypes.to_dict().items():
        v = str(v)
        if v == "float64":
            struct_schema.append(f"{k}:float")
        elif v == "float32":
            struct_schema.append(f"{k}:float")
        elif v == "datetime64[ns]":
            struct_schema.append(f"{k}:timestamp")
        elif v == "int32":
            struct_schema.append(f"{k}:int")
        elif v == "int64":
            struct_schema.append(f"{k}:int")
        else:
            struct_schema.append(f"{k}:string")
    return struct_schema


def fields_to_pyorc_schema(fields):
    """Converts list of fields to pyorc schema array"""
    struct_schema = []
    for field in fields:
        struct_schema.append(f"{field}:string")
    return struct_schema


class ORCIterable(BaseFileIterable):
    """ORC reader/writer with pluggable backend.

    Backends:
    - ``pyorc`` (default when installed): the historical row-oriented path.
    - ``pyarrow`` (``pyarrow.orc``, requires pyarrow): stripe-batch reads and
      writes; enables the native batch protocol and ORC support on systems
      without ``pyorc``.

    The backend is chosen with the ``backend`` option (``'pyorc'``,
    ``'pyarrow'`` or ``None`` for auto). Auto prefers ``pyorc`` so existing
    behavior is unchanged, falling back to ``pyarrow.orc`` when ``pyorc`` is
    not installed.
    """

    datamode = "binary"
    supports_native_batch = False

    def __init__(
        self,
        filename: str | None = None,
        stream: typing.IO[Any] | None = None,
        codec: BaseCodec | None = None,
        mode: str = "r",
        keys: list[str] | None = None,
        schema: list[str] = None,
        compression: int = 5,
        batch_size: int = DEFAULT_BATCH_SIZE,
        backend: str | None = None,
        options: dict[str, Any] | None = None,
    ):
        if options is None:
            options = {}
        self.keys = keys
        self.schema = schema
        self.compression = compression
        self.batch_size = batch_size
        backend = backend or options.get("backend")
        self.backend = self._resolve_backend(backend)
        # Native batches (stripe-level reads, projection/filter pushdown) are
        # only available through the pyarrow.orc backend; pyorc exposes a
        # row-at-a-time reader only.
        self.supports_native_batch = self.backend == "pyarrow"
        self._pending_rows = deque()
        self._stripe_index = 0
        self._orc_file = None
        self._arrow_writer = None
        super().__init__(filename, stream, codec=codec, mode=mode, binary=True, options=options)
        self.reset()
        pass

    @staticmethod
    def _resolve_backend(backend: str | None) -> str:
        """Pick the ORC backend, preferring pyorc for backward compatibility."""
        if backend is None:
            if HAS_PYORC:
                return "pyorc"
            if HAS_PYARROW_ORC:
                return "pyarrow"
            raise ImportError(
                "ORC support requires the 'pyorc' package (pip install pyorc) "
                "or pyarrow with ORC support (pip install 'pyarrow>=14')."
            )
        normalized = str(backend).lower()
        if normalized in ("pyarrow", "arrow"):
            if not HAS_PYARROW_ORC:
                raise ImportError("The 'pyarrow' ORC backend requires pyarrow (pip install 'pyarrow>=14').")
            return "pyarrow"
        if normalized == "pyorc":
            if not HAS_PYORC:
                raise ImportError("The 'pyorc' ORC backend requires the 'pyorc' package (pip install pyorc).")
            return "pyorc"
        raise ValueError(f"Unsupported ORC backend: {backend!r}. Use 'pyorc' or 'pyarrow'.")

    def reset(self):
        """Reset iterable"""
        super().reset()
        self.pos = 0
        self.reader = None
        self._orc_file = None
        self._pending_rows = deque()
        self._stripe_index = 0
        if self.mode == "r":
            if self.backend == "pyarrow":
                if hasattr(self.fobj, "seek"):
                    self.fobj.seek(0)
                self._orc_file = pyarrow.orc.ORCFile(self.fobj)
            else:
                self.reader = pyorc.Reader(self.fobj, struct_repr=pyorc.StructRepr.DICT)
        self.writer = None
        self._arrow_writer = None
        self._arrow_buffer = []
        # When writing without an explicit schema or field list, defer writer
        # creation until the first record is written and infer the field names
        # from it. This mirrors columnar writers (e.g. Parquet) that derive the
        # schema from the data and avoids requiring callers to pass ``keys``.
        self._writer_pending = False
        if self.mode == "w":
            if self.backend == "pyarrow":
                self._writer_pending = True
            elif self.schema is not None or self.keys is not None:
                self._create_writer()
            else:
                self._writer_pending = True

    def _create_writer(self) -> None:
        """Create the underlying pyorc writer from the configured schema/keys.

        When the field list is used (the common/inferred case), the schema is
        built programmatically via :class:`pyorc.Struct` instead of a
        ``struct<...>`` string. Building from a string is fragile because pyorc
        rejects field names that contain spaces, commas, colons, are empty, or
        contain non-ASCII characters. ``pyorc.Struct(**fields)`` accepts any
        field name and therefore handles real-world headers safely.
        """
        if self.schema is not None:
            schema = "struct<{}>".format(",".join(self.schema))
        else:
            schema = pyorc.Struct(**{str(field): pyorc.String() for field in self.keys})
        self.writer = pyorc.Writer(
            self.fobj,
            schema,
            struct_repr=pyorc.StructRepr.DICT,
            compression=self.compression,
            compression_strategy=1,
        )
        self._writer_pending = False

    def _pyarrow_compression(self) -> str:
        """Map the pyorc integer compression kind to a pyarrow codec name."""
        if isinstance(self.compression, str):
            return self.compression
        return _PYORC_TO_PYARROW_COMPRESSION.get(self.compression, "zstd")

    def _create_arrow_writer(self, schema: Any) -> None:
        """Create the pyarrow.orc writer lazily from the first batch schema."""
        self._arrow_writer = pyarrow.orc.ORCWriter(
            self.fobj,
            compression=self._pyarrow_compression(),
        )
        self._arrow_schema = schema
        self._writer_pending = False

    def _ensure_writer(self, record: Row) -> None:
        """Lazily create the writer, inferring field names from the first record."""
        if self._writer_pending:
            if self.backend == "pyarrow":
                # Defer schema inference to the first flush so null-only
                # columns in the first record do not freeze a null type.
                return
            self.keys = list(record.keys())
            self._create_writer()

    @staticmethod
    def id() -> str:
        return "orc"

    @staticmethod
    def is_flatonly() -> bool:
        return True

    def is_streaming(self) -> bool:
        """Records are decoded incrementally; the file is not fully loaded."""
        return True

    @staticmethod
    def has_totals() -> bool:
        """Has totals indicator"""
        return True

    def totals(self):
        """Returns file totals"""
        if self.backend == "pyarrow":
            return self._orc_file.nrows if self._orc_file is not None else 0
        return len(self.reader)

    def close(self):
        """Close iterable"""
        if self.mode == "w" and self.backend == "pyarrow":
            self.flush()
        if self.writer is not None:
            self.writer.close()
        if self._arrow_writer is not None:
            self._arrow_writer.close()
            self._arrow_writer = None
        super().close()

    def _fill_pending_rows(self) -> bool:
        """Load the next ORC stripe into the shared row cursor (pyarrow backend)."""
        if self._pending_rows:
            return True
        if self._orc_file is None or self._stripe_index >= self._orc_file.nstripes:
            return False
        batch = self._orc_file.read_stripe(self._stripe_index)
        self._stripe_index += 1
        self._pending_rows.extend(batch.to_pylist())
        return bool(self._pending_rows)

    def read(self, skip_empty: bool = True) -> dict:
        """Read single record"""
        if self.backend == "pyarrow":
            if not self._fill_pending_rows():
                raise StopIteration
            row = self._pending_rows.popleft()
            self.pos += 1
            return row
        row = next(self.reader)
        self.pos += 1
        return row

    def read_bulk(self, num: int = DEFAULT_BULK_NUMBER) -> list[dict]:
        """Read bulk ORC records efficiently.

        Note: pyorc.Reader is an iterator that yields rows one at a time.
        This implementation reads directly from the iterator to avoid
        method call overhead from read(). The pyarrow backend drains the
        stripe-backed row cursor instead.
        """
        chunk = []
        if self.backend == "pyarrow":
            while len(chunk) < num and self._fill_pending_rows():
                take = min(num - len(chunk), len(self._pending_rows))
                for _ in range(take):
                    chunk.append(self._pending_rows.popleft())
                self.pos += take
            return chunk
        for _n in range(num):
            try:
                # Read directly from iterator to avoid method call overhead
                row = next(self.reader)
                chunk.append(row)
                self.pos += 1
            except StopIteration:
                break
        return chunk

    def read_batches(self, selection: BatchSelection | None = None):
        """Yield ORC stripe batches with projection/filter pushdown.

        Column projection is pushed to the stripe reader; structured
        predicates are pushed through ``pyarrow.dataset`` when the source is
        a plain file path. Remaining window/step operations are applied at
        the row level with semantics identical to the row fallback.
        """
        if self.backend != "pyarrow":
            raise NotImplementedError(
                "ORC native batches require the pyarrow backend (iterableargs={'backend': 'pyarrow'})"
            )
        selection = selection or BatchSelection()
        if selection.table is not None:
            raise NotImplementedError("ORC native batches do not support table selection")
        start, stop, step = resolve_row_window(selection)
        if selection.predicate is not None:
            if not self.filename:
                raise NotImplementedError("ORC predicate pushdown requires a file path source")
            import pyarrow.dataset as ds

            dataset = ds.dataset(self.filename, format="orc")
            scanner = dataset.scanner(
                columns=list(selection.columns) if selection.columns is not None else None,
                filter=to_pyarrow_expression(selection.predicate),
                batch_size=selection.batch_size or self.batch_size,
                # Deterministic stripe order keeps results identical to the
                # sequential row path.
                use_threads=False,
            )

            def rows():
                for batch in scanner.to_batches():
                    yield from batch.to_pylist()

            window = BatchSelection(row_range=(start, stop) if stop is not None or start else None)
            if step != 1:
                window = BatchSelection(slice=(start, stop, step))
            target = selection.batch_size or self.batch_size
            for chunk in chunk_rows(select_rows(rows(), window), target):
                self.pos += len(chunk)
                yield chunk
            return

        def stripe_rows():
            for stripe in range(self._orc_file.nstripes):
                batch = self._orc_file.read_stripe(
                    stripe,
                    columns=list(selection.columns) if selection.columns is not None else None,
                )
                yield from batch.to_pylist()

        window = BatchSelection(row_range=(start, stop) if stop is not None or start else None)
        if step != 1:
            window = BatchSelection(slice=(start, stop, step))
        target = selection.batch_size or self.batch_size
        for chunk in chunk_rows(select_rows(stripe_rows(), window), target):
            self.pos += len(chunk)
            yield chunk

    def write(self, record: Row) -> None:
        """Write single record"""
        self._ensure_writer(record)
        if self.backend == "pyarrow":
            self.write_bulk([record])
            return
        self.writer.write(record)

    def flush(self):
        """Flush buffered records to the pyarrow.orc writer."""
        if self.backend != "pyarrow":
            return
        if not self._arrow_buffer:
            return
        table = pyarrow.Table.from_pylist([dict(record) for record in self._arrow_buffer])
        if self._arrow_writer is None:
            self._create_arrow_writer(table.schema)
        elif table.schema != self._arrow_schema:
            table = table.cast(self._arrow_schema)
        self._arrow_writer.write(table)
        self._arrow_buffer = []

    def write_bulk(self, records: list[Row]) -> None:
        """Write bulk records"""
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
        if self.backend == "pyarrow":
            self._arrow_buffer.extend(records)
            if len(self._arrow_buffer) >= self.batch_size:
                self.flush()
            return
        self.writer.writerows(records)

    def write_batch(self, records: list[Row]) -> None:
        """Native batch writer hook used by columnar conversion."""
        self.write_bulk(records)
