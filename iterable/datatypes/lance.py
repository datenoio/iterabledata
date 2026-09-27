from __future__ import annotations

import os
import typing

try:
    import lance
    import pyarrow

    HAS_LANCE = True
except ImportError:
    HAS_LANCE = False

from typing import Any

from ..base import BaseCodec, BaseFileIterable
from ..convert.batch import BatchSelection, chunk_rows, resolve_row_window, select_rows, to_sql_filter
from ..types import Row

DEFAULT_BATCH_SIZE = 1024

# The real Lance columnar library is published as ``pylance`` but imports as
# ``lance``. An unrelated PyPI package named ``lance`` (a codegen helper) shadows
# it on import. Detect that the genuine API is present so we can fail fast with
# an actionable message instead of a cryptic AttributeError at read/write time.
_LANCE_HAS_API = HAS_LANCE and hasattr(lance, "write_dataset") and hasattr(lance, "dataset")


def _require_lance() -> None:
    """Ensure the genuine Lance library (``pylance``) is importable."""
    if not HAS_LANCE:
        raise ImportError("Lance format support requires the 'pylance' package. Install with: pip install pylance")
    if not _LANCE_HAS_API:
        installed = getattr(lance, "__file__", "<unknown>")
        raise ImportError(
            "The imported 'lance' module is not the Lance columnar format library "
            "(missing 'write_dataset'/'dataset'). A different PyPI package named 'lance' "
            f"is shadowing it (loaded from: {installed}). Uninstall it and install the real "
            "library: pip uninstall -y lance && pip install pylance"
        )


class LanceIterable(BaseFileIterable):
    """Lance columnar dataset reader.

    Memory behavior: records are read batch by batch via
    ``scanner.to_batches()``; the dataset is never fully materialized.
    """

    datamode = "binary"
    supports_native_batch = False

    def __init__(
        self,
        filename: str | None = None,
        stream: typing.IO[Any] | None = None,
        mode: str = "r",
        codec: BaseCodec | None = None,
        batch_size: int = DEFAULT_BATCH_SIZE,
        write_mode: str = "create",
        options: dict[str, Any] | None = None,
    ):
        if options is None:
            options = {}
        _require_lance()
        self.batch_size = batch_size
        self.write_mode = write_mode  # 'create', 'overwrite', or 'append'
        self.__buffer = []
        self.is_data_written = False
        # Native batches (scanner projection/filter pushdown) require the
        # genuine Lance library; this is always true after _require_lance().
        self.supports_native_batch = True
        # Lance datasets are directory-based, so we need the directory path
        # If filename ends with .lance, remove it to get directory name
        if filename:
            if filename.endswith(".lance"):
                self.dataset_path = filename[:-6]  # Remove .lance extension
            else:
                self.dataset_path = filename
        else:
            self.dataset_path = None
        # Lance datasets are directories, not files, so we don't want BaseFileIterable to open them as files
        super().__init__(filename, stream, codec=codec, mode=mode, binary=True, noopen=True, options=options)
        self.reset()
        pass

    def reset(self):
        """Reset iterable"""
        super().reset()
        self.pos = 0
        self.dataset = None
        self.iterator = None
        if self.mode == "r":
            if self.filename:
                # Lance datasets are directories, not files
                dataset_path = self.dataset_path
                if os.path.exists(dataset_path):
                    self.dataset = lance.dataset(dataset_path)
                    scanner = self.dataset.scanner()
                    self.iterator = self.__iterator(scanner)
                else:
                    raise FileNotFoundError(f"Lance dataset not found at: {dataset_path}")
        elif self.mode == "w":
            self.dataset = None  # Will be created on first write

    @staticmethod
    def id() -> str:
        return "lance"

    @staticmethod
    def is_flatonly() -> bool:
        return True

    def is_streaming(self) -> bool:
        """Records are read incrementally from scanner batches."""
        return True

    @staticmethod
    def has_totals() -> bool:
        """Has totals indicator"""
        return True

    def totals(self):
        """Returns file totals"""
        if self.mode == "r" and self.dataset:
            return self.dataset.count_rows()
        return 0

    def flush(self):
        """Flush all data"""
        if len(self.__buffer) > 0 and self.mode == "w":
            table = pyarrow.Table.from_pylist(self.__buffer)
            dataset_path = self.dataset_path
            if not self.is_data_written:
                # Create new dataset
                lance.write_dataset(table, dataset_path, mode=self.write_mode)
                self.is_data_written = True
            else:
                # Append to existing dataset
                dataset = lance.dataset(dataset_path)
                dataset.insert(table)
            self.__buffer = []

    def close(self):
        """Close iterable"""
        if self.mode == "w" and len(self.__buffer) > 0:
            self.flush()
        super().close()

    def __iterator(self, scanner):
        """Iterator for reading records batch by batch (no full-table load)."""
        for batch in scanner.to_batches():
            yield from batch.to_pylist()

    def read(self, skip_empty: bool = True) -> dict:
        """Read single record"""
        if self.iterator is None:
            raise StopIteration
        row = next(self.iterator)
        self.pos += 1
        return row

    def read_batches(self, selection: BatchSelection | None = None):
        """Yield Lance scanner batches with projection/filter pushdown.

        Column projection, structured predicates (translated to Lance SQL
        filters; plain strings pass through as trusted raw filters), and
        offset/limit windows are pushed to the Lance scanner. Slice steps
        are applied after the scan with row-fallback-identical semantics.
        Requires ``pylance>=0.9``.
        """
        selection = selection or BatchSelection()
        if selection.table is not None:
            raise NotImplementedError("Lance native batches do not support table selection")
        if self.dataset is None:
            return
        start, stop, step = resolve_row_window(selection)
        scan_kwargs: dict[str, Any] = {"batch_size": selection.batch_size or self.batch_size}
        if selection.columns is not None:
            scan_kwargs["columns"] = list(selection.columns)
        sql_filter = to_sql_filter(selection.predicate)
        if sql_filter is not None:
            scan_kwargs["filter"] = sql_filter
        if step == 1:
            # Offset/limit are pushed to the scanner; steps are not pushable.
            if stop is not None:
                scan_kwargs["limit"] = stop - start
            if start:
                scan_kwargs["offset"] = start
        scanner = self.dataset.scanner(**scan_kwargs)
        target = selection.batch_size or self.batch_size

        def rows():
            for batch in scanner.to_batches():
                yield from batch.to_pylist()

        stream: Any = rows()
        if step != 1:
            # Steps cannot be pushed; apply the window after the scan.
            stream = select_rows(stream, BatchSelection(slice=(start, stop, step)))

        for chunk in chunk_rows(stream, target):
            self.pos += len(chunk)
            yield chunk

    def write_batch(self, records: list[Row]) -> None:
        """Native batch writer hook used by columnar conversion."""
        self.write_bulk(records)

    def write(self, record: Row) -> None:
        """Write single record"""
        self.write_bulk(
            [
                record,
            ]
        )

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

        self.__buffer.extend(records)
        # Keep memory bounded and make single-row writes form sensible Lance
        # fragments instead of issuing one dataset mutation per call.
        if len(self.__buffer) >= self.batch_size:
            self.flush()
