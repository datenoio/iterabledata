from __future__ import annotations

import os
import typing

try:
    import deltalake
    from deltalake import write_deltalake

    HAS_DELTALAKE = True
except ImportError:
    HAS_DELTALAKE = False

from typing import Any

from ..base import BaseCodec, BaseFileIterable
from ..convert.batch import BatchSelection, chunk_rows, resolve_row_window, select_rows, to_pyarrow_expression
from ..exceptions import ReadError, WriteNotSupportedError
from ..helpers.lakehouse_write import infer_arrow_schema, records_to_arrow_table
from ..types import Row

DEFAULT_BATCH_SIZE = 1024


class DeltaIterable(BaseFileIterable):
    """Delta Lake table reader/writer.

    Memory behavior: records are read batch by batch via
    ``DeltaTable.to_pyarrow_dataset().to_batches()``; writes flush Arrow
    batches via ``write_deltalake`` at ``batch_size``.
    """

    datamode = "binary"
    supports_native_batch = False

    def __init__(
        self,
        filename: str | None = None,
        stream: typing.IO[Any] | None = None,
        codec: BaseCodec | None = None,
        mode: str = "r",
        batch_size: int = DEFAULT_BATCH_SIZE,
        write_mode: str = "append",
        options: dict[str, Any] | None = None,
    ):
        if options is None:
            options = {}
        else:
            options = dict(options)
        if not HAS_DELTALAKE:
            raise ImportError(
                "Delta Lake support requires the 'deltalake' package. Install with: pip install iterabledata[lakehouse]"
            )
        self.batch_size = int(options.pop("batch_size", batch_size))
        self.write_mode = str(options.pop("write_mode", write_mode)).lower()
        self._buffer: list[Row] = []
        self._arrow_schema = options.pop("schema", None)
        self._wrote_once = False
        # Native batches (pyarrow dataset scanner pushdown) are available
        # whenever the deltalake backend is importable.
        self.supports_native_batch = HAS_DELTALAKE
        super().__init__(filename, stream, codec=codec, binary=True, mode=mode, noopen=True, options=options)
        self.reset()

    def reset(self):
        """Reset iterable"""
        super().reset()
        self.pos = 0
        self.delta_table = None
        self.dataset = None
        self.iterator = None
        if self.mode == "r":
            if self.filename:
                self.delta_table = deltalake.DeltaTable(self.filename)
                self.dataset = self.delta_table.to_pyarrow_dataset()
                self.iterator = self.__iterator()
            else:
                raise ReadError(
                    "Delta Lake reading requires filename (path to delta table)",
                    filename=None,
                    error_code="RESOURCE_REQUIREMENT_NOT_MET",
                )
        else:
            if self.filename is None:
                raise ReadError(
                    "Delta Lake writing requires filename (path to delta table)",
                    filename=None,
                    error_code="RESOURCE_REQUIREMENT_NOT_MET",
                )
            if self.write_mode not in {"append", "overwrite", "error", "ignore"}:
                raise ValueError(f"Unsupported Delta write_mode: {self.write_mode}")
            self._buffer = []
            self._wrote_once = False

    def __iterator(self):
        """Iterator for reading Delta table records batch by batch"""
        for batch in self.dataset.to_batches():
            yield from batch.to_pylist()

    @staticmethod
    def id() -> str:
        return "delta"

    @staticmethod
    def is_flatonly() -> bool:
        return True

    def is_streaming(self) -> bool:
        """Records are read incrementally from dataset batches."""
        return True

    @staticmethod
    def has_tables() -> bool:
        return False

    def list_tables(self, filename: str | None = None) -> list[str] | None:
        target_path = filename if filename is not None else (self.filename if hasattr(self, "filename") else None)
        if target_path is None:
            return None
        try:
            if os.path.isdir(target_path) and os.path.exists(os.path.join(target_path, "_delta_log")):
                return None
            return None
        except Exception:
            return None

    @staticmethod
    def has_totals() -> bool:
        return True

    def totals(self):
        if hasattr(self, "dataset") and self.dataset is not None:
            return self.dataset.count_rows()
        return 0

    def read(self, skip_empty: bool = True) -> dict:
        row = next(self.iterator)
        self.pos += 1
        return row

    def read_batches(self, selection: BatchSelection | None = None):
        """Yield Delta table batches with projection/filter pushdown.

        Column projection and structured predicates are pushed to the
        PyArrow dataset scanner backing the Delta table (requires
        ``deltalake>=0.15`` with ``pyarrow``). Row windows and slice steps
        are applied after the scan with row-fallback-identical semantics.
        """
        selection = selection or BatchSelection()
        if selection.table is not None:
            raise NotImplementedError("Delta native batches do not support table selection")
        if self.dataset is None:
            return
        start, stop, step = resolve_row_window(selection)
        target = selection.batch_size or self.batch_size
        scan_kwargs: dict[str, Any] = {
            "batch_size": target,
            # Deterministic data-file order keeps results identical to the
            # sequential row path.
            "use_threads": False,
        }
        if selection.columns is not None:
            scan_kwargs["columns"] = list(selection.columns)
        if selection.predicate is not None:
            scan_kwargs["filter"] = to_pyarrow_expression(selection.predicate)
        scanner = self.dataset.scanner(**scan_kwargs)

        def rows():
            for batch in scanner.to_batches():
                yield from batch.to_pylist()

        window = BatchSelection(row_range=(start, stop) if start or stop is not None else None)
        if step != 1:
            window = BatchSelection(slice=(start, stop, step))

        for chunk in chunk_rows(select_rows(rows(), window), target):
            self.pos += len(chunk)
            yield chunk

    def write_batch(self, records: list[Row]) -> None:
        """Native batch writer hook used by columnar conversion."""
        self.write_bulk(records)

    def _flush_buffer(self) -> None:
        if not self._buffer:
            return
        if self._arrow_schema is None:
            self._arrow_schema = infer_arrow_schema(self._buffer)
        table = records_to_arrow_table(self._buffer, schema=self._arrow_schema)
        mode = self.write_mode
        if self._wrote_once and mode in {"error", "ignore"}:
            mode = "append"
        elif not self._wrote_once and mode == "error":
            mode = "error"
        write_deltalake(self.filename, table, mode=mode)
        self._wrote_once = True
        # Subsequent flushes in the same writer should append
        if self.write_mode in {"overwrite", "error"}:
            self.write_mode = "append"
        self._buffer = []

    def write(self, record: Row) -> None:
        self.write_bulk([record])

    def write_bulk(self, records: list[Row]) -> None:
        # Apply validation hooks if configured
        if self._validation_hooks:
            validated_records = []
            for record in records:
                validated = self._apply_validation_hooks(record)
                if validated is not None:  # Not skipped
                    validated_records.append(validated)
            records = validated_records

        if self.mode != "w":
            raise WriteNotSupportedError("delta", "Delta Lake is open read-only")
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
        super().close()
