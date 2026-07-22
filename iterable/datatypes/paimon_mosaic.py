"""Apache Paimon Mosaic format support via the ``paimon-mosaic`` package."""

from __future__ import annotations

import typing
from typing import Any

try:
    from mosaic import MosaicReader, MosaicWriter, WriterOptions

    HAS_MOSAIC = True
except ImportError:
    HAS_MOSAIC = False

try:
    import pyarrow

    HAS_PYARROW = True
except ImportError:
    HAS_PYARROW = False

from ..base import BaseCodec, BaseFileIterable
from ..exceptions import ReadError
from ..types import Row

DEFAULT_BATCH_SIZE = 1024
FOOTER_SIZE = 32
MOSAIC_MAGIC = b"MOSA"


def _require_mosaic() -> None:
    if not HAS_MOSAIC:
        raise ImportError(
            "Paimon Mosaic format support requires the 'paimon-mosaic' package. "
            "Install with: pip install iterabledata[paimon-mosaic]"
        )
    if not HAS_PYARROW:
        raise ImportError("Paimon Mosaic format support requires 'pyarrow'. Install with: pip install pyarrow")


def match_mosaic_footer(footer: bytes) -> bool:
    """Return True if ``footer`` ends with Mosaic magic and is 32 bytes."""
    return len(footer) == FOOTER_SIZE and footer[-4:] == MOSAIC_MAGIC


def _build_writer_options(options: dict[str, Any]) -> Any:
    kwargs: dict[str, Any] = {}
    if "num_buckets" in options:
        kwargs["num_buckets"] = int(options["num_buckets"])
    if "compression" in options:
        compression = options["compression"]
        if isinstance(compression, str):
            compression = compression.lower()
            if compression in {"zstd", "zstandard"}:
                kwargs["compression"] = WriterOptions.COMPRESSION_ZSTD
            elif compression in {"none", "uncompressed"}:
                kwargs["compression"] = 0
            else:
                raise ValueError(f"Unsupported Mosaic compression: {compression}")
        else:
            kwargs["compression"] = compression
    if "zstd_level" in options:
        kwargs["zstd_level"] = int(options["zstd_level"])
    if "row_group_max_size" in options:
        kwargs["row_group_max_size"] = int(options["row_group_max_size"])
    if "stats_columns" in options:
        kwargs["stats_columns"] = list(options["stats_columns"])
    return WriterOptions(**kwargs) if kwargs else WriterOptions()


class PaimonMosaicIterable(BaseFileIterable):
    """Paimon Mosaic columnar-bucket hybrid format reader/writer.

    Memory behavior: reads one row group at a time via ``MosaicReader``;
    writes flush Arrow batches at ``batch_size`` using ``MosaicWriter``.
    """

    datamode = "binary"

    def __init__(
        self,
        filename: str | None = None,
        stream: typing.IO[Any] | None = None,
        mode: str = "r",
        codec: BaseCodec | None = None,
        batch_size: int = DEFAULT_BATCH_SIZE,
        columns: list[str] | None = None,
        options: dict[str, Any] | None = None,
    ):
        if options is None:
            options = {}
        else:
            options = dict(options)
        if stream is not None and filename is None and mode == "r":
            # MosaicReader needs random access via read_at; require a filename for simplicity.
            raise ReadError(
                "Paimon Mosaic format does not support stream mode. Use filename instead.",
                filename=None,
                error_code="RESOURCE_REQUIREMENT_NOT_MET",
            )
        if filename is None:
            raise ReadError(
                "Paimon Mosaic format requires a filename",
                filename=None,
                error_code="RESOURCE_REQUIREMENT_NOT_MET",
            )
        _require_mosaic()
        self.batch_size = int(options.pop("batch_size", batch_size))
        self.columns = options.pop("columns", columns)
        if self.columns is None:
            self.columns = options.pop("project", None)
        self._writer_option_keys = {
            "num_buckets",
            "compression",
            "zstd_level",
            "row_group_max_size",
            "stats_columns",
            "page_size_threshold",
            "max_dict_total_bytes",
            "max_dict_entries",
        }
        self._writer_options_raw = {k: options.pop(k) for k in list(options) if k in self._writer_option_keys}
        self._reader: Any | None = None
        self._reader_file: typing.IO[Any] | None = None
        self._writer: Any | None = None
        self._writer_file: typing.IO[Any] | None = None
        self._arrow_schema: Any | None = None
        self._buffer: list[Row] = []
        self._iterator: typing.Iterator[dict[str, Any]] | None = None
        self.pos = 0
        super().__init__(filename, stream, codec=codec, mode=mode, binary=True, noopen=True, options=options)
        self.reset()

    def reset(self) -> None:
        super().reset()
        self.pos = 0
        self._close_reader()
        self._iterator = None
        if self.mode == "r":
            self._open_reader()
            self._iterator = self._iter_rows()
        elif self.mode == "w":
            self._buffer = []
            self._arrow_schema = None
            if self._writer is not None:
                try:
                    self._writer.close()
                except Exception:
                    pass
                self._writer = None
            if self._writer_file is not None:
                try:
                    self._writer_file.close()
                except Exception:
                    pass
                self._writer_file = None

    def _close_reader(self) -> None:
        if self._reader is not None:
            try:
                self._reader.close()
            except Exception:
                pass
            self._reader = None
        if self._reader_file is not None:
            try:
                self._reader_file.close()
            except Exception:
                pass
            self._reader_file = None

    def _open_reader(self) -> None:
        assert self.filename is not None
        f = open(self.filename, "rb")
        f.seek(0, 2)
        size = f.tell()

        def read_at(offset: int, length: int) -> bytes:
            f.seek(offset)
            return f.read(length)

        reader = MosaicReader.from_input_file(read_at, size)
        if self.columns is not None:
            reader.project(list(self.columns))
        self._reader_file = f
        self._reader = reader

    def _iter_rows(self) -> typing.Iterator[dict[str, Any]]:
        assert self._reader is not None
        for rg in range(self._reader.num_row_groups):
            batch = self._reader.read_row_group(rg)
            yield from batch.to_pylist()

    @staticmethod
    def id() -> str:
        return "paimon_mosaic"

    @staticmethod
    def is_flatonly() -> bool:
        return True

    def is_streaming(self) -> bool:
        return True

    @staticmethod
    def has_totals() -> bool:
        return True

    def totals(self) -> int:
        if self.mode != "r":
            return 0
        if self._reader is None:
            self._open_reader()
        assert self._reader is not None
        return sum(self._reader.row_group_num_rows(i) for i in range(self._reader.num_row_groups))

    def read(self, skip_empty: bool = True) -> dict:
        if self._iterator is None:
            raise RuntimeError("Iterator not initialized. Call reset() first.")
        row = next(self._iterator)
        self.pos += 1
        return row

    def _ensure_writer(self, records: list[Row]) -> None:
        if self._writer is not None:
            return
        assert self.filename is not None
        table = pyarrow.Table.from_pylist(records)
        self._arrow_schema = table.schema
        self._writer_file = open(self.filename, "wb")
        opts = _build_writer_options(self._writer_options_raw)
        self._writer = MosaicWriter(self._writer_file, self._arrow_schema, opts)

    def _flush_buffer(self) -> None:
        if not self._buffer:
            return
        self._ensure_writer(self._buffer)
        assert self._writer is not None and self._arrow_schema is not None
        table = pyarrow.Table.from_pylist(self._buffer, schema=self._arrow_schema)
        self._writer.write(table)
        self._buffer = []

    def write(self, record: Row) -> None:
        self.write_bulk([record])

    def write_bulk(self, records: list[Row]) -> None:
        if not records:
            return
        self._buffer.extend(records)
        if len(self._buffer) >= self.batch_size:
            self._flush_buffer()

    def flush(self) -> None:
        if self.mode == "w":
            self._flush_buffer()

    def close(self) -> None:
        if self.mode == "w":
            self._flush_buffer()
            if self._writer is not None:
                self._writer.close()
                self._writer = None
            if self._writer_file is not None:
                self._writer_file.close()
                self._writer_file = None
        self._close_reader()
        super().close()
