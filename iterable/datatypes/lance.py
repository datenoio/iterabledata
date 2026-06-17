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
from ..types import Row

DEFAULT_BATCH_SIZE = 1024


class LanceIterable(BaseFileIterable):
    datamode = "binary"

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
        if not HAS_LANCE:
            raise ImportError("Lance format support requires 'lance' package. Install with: pip install lance")
        self.batch_size = batch_size
        self.write_mode = write_mode  # 'create', 'overwrite', or 'append'
        self.__buffer = []
        self.is_data_written = False
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
        """Iterator for reading records"""
        table = scanner.to_table()
        for batch in table.to_batches(max_chunksize=self.batch_size):
            yield from batch.to_pylist()

    def read(self, skip_empty: bool = True) -> dict:
        """Read single record"""
        if self.iterator is None:
            raise StopIteration
        row = next(self.iterator)
        self.pos += 1
        return row

    def write(self, record: Row) -> None:
        """Write single record"""
        self.write_bulk(
            [
                record,
            ]
        )

    def write_bulk(self, records: list[Row]) -> None:
        """Write bulk records"""
        self.__buffer.extend(records)
