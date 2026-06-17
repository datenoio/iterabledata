from __future__ import annotations

import typing

try:
    import h5py

    HAS_H5PY = True
except ImportError:
    HAS_H5PY = False

from typing import Any

from ..base import BaseCodec, BaseFileIterable
from ..exceptions import FormatNotSupportedError, ReadError, WriteError, WriteNotSupportedError
from ..types import Row


class HDF5Iterable(BaseFileIterable):
    datamode = "binary"

    def __init__(
        self,
        filename: str | None = None,
        stream: typing.IO[Any] | None = None,
        codec: BaseCodec | None = None,
        mode: str = "r",
        dataset_path: str = "/data",
        options: dict[str, Any] | None = None,
    ):
        if options is None:
            options = {}
        if not HAS_H5PY:
            raise ImportError("HDF5 support requires 'h5py' package")
        if dataset_path is None and "dataset_path" in options:
            dataset_path = options["dataset_path"]
        self.dataset_path = dataset_path
        super().__init__(filename, stream, codec=codec, binary=True, mode=mode, options=options)
        self.reset()
        pass

    def reset(self):
        """Reset iterable"""
        super().reset()
        self.pos = 0
        if self.mode == "r":
            # HDF5 requires file path or file-like object
            if self.filename:
                self.h5file = h5py.File(self.filename, "r")
            else:
                # Try to use file object if it has a name
                if hasattr(self.fobj, "name"):
                    self.h5file = h5py.File(self.fobj.name, "r")
                else:
                    raise ReadError(
                        "HDF5 file reading requires filename or named file object",
                        filename=None,
                        error_code="RESOURCE_REQUIREMENT_NOT_MET",
                    )

            if self.dataset_path in self.h5file:
                self.dataset = self.h5file[self.dataset_path]
                self.iterator = self.__iterator()
            else:
                raise FormatNotSupportedError(
                    "hdf5",
                    f"Dataset path '{self.dataset_path}' not found in HDF5 file",
                )
        else:
            if self.filename:
                self.h5file = h5py.File(self.filename, "w")
            else:
                raise WriteError(
                    "HDF5 file writing requires filename",
                    filename=None,
                    error_code="RESOURCE_REQUIREMENT_NOT_MET",
                )

    def __iterator(self):
        """Iterator for reading HDF5 dataset"""
        # HDF5 datasets are typically arrays/tables
        if len(self.dataset.shape) == 1:
            # 1D array - treat as single column
            for i in range(len(self.dataset)):
                yield {self.dataset_path.split("/")[-1]: self.dataset[i]}
        elif len(self.dataset.shape) == 2:
            # 2D array - treat as table
            if hasattr(self.dataset, "dtype") and self.dataset.dtype.names:
                # Structured array
                for row in self.dataset:
                    yield {name: row[name] for name in self.dataset.dtype.names}
            else:
                # Regular 2D array
                for i in range(self.dataset.shape[0]):
                    yield {f"col_{j}": self.dataset[i, j] for j in range(self.dataset.shape[1])}
        else:
            raise FormatNotSupportedError(
                "hdf5",
                "HDF5 dataset must be 1D or 2D for iteration",
            )

    @staticmethod
    def id() -> str:
        return "hdf5"

    @staticmethod
    def is_flatonly() -> bool:
        return True

    @staticmethod
    def has_tables() -> bool:
        """Indicates if this format supports multiple tables/datasets."""
        return True

    @staticmethod
    def _list_datasets_recursive(group, prefix=""):
        """Recursively list all datasets in an HDF5 group."""
        datasets = []
        for key in group.keys():
            item = group[key]
            path = f"{prefix}/{key}" if prefix else f"/{key}"
            if isinstance(item, h5py.Dataset):
                datasets.append(path)
            elif isinstance(item, h5py.Group):
                # Recursively get datasets from subgroups
                datasets.extend(HDF5Iterable._list_datasets_recursive(item, path))
        return datasets

    def list_tables(self, filename: str | None = None) -> list[str] | None:
        """List available dataset paths in the HDF5 file.

        Args:
            filename: Optional filename. If None, uses instance's filename and reuses open file handle.

        Returns:
            list[str]: List of dataset paths (e.g., ['/data', '/group/dataset1']), or empty list if no datasets.
        """
        # If file is already open, reuse it
        if filename is None and hasattr(self, "h5file") and self.h5file is not None:
            return self._list_datasets_recursive(self.h5file)

        # Otherwise, open temporarily
        target_filename = filename if filename is not None else self.filename
        if target_filename is None:
            return None

        h5file = h5py.File(target_filename, "r")
        try:
            return self._list_datasets_recursive(h5file)
        finally:
            h5file.close()

    @staticmethod
    def has_totals() -> bool:
        """Has totals indicator"""
        return True

    def totals(self):
        """Returns file totals"""
        if hasattr(self, "dataset"):
            if len(self.dataset.shape) >= 1:
                return self.dataset.shape[0]
        return 0

    def close(self):
        """Close HDF5 file"""
        if hasattr(self, "h5file"):
            self.h5file.close()
        super().close()

    def read(self, skip_empty: bool = True) -> dict:
        """Read single HDF5 record"""
        row = next(self.iterator)
        self.pos += 1
        return row

    def write(self, record: Row) -> None:
        """Write single HDF5 record"""
        self.write_bulk(
            [
                record,
            ]
        )

    def write_bulk(self, records: list[Row]) -> None:
        """Write bulk HDF5 records"""
        if not hasattr(self, "dataset") or self.dataset is None:
            # Create dataset on first write
            if records:
                keys = list(records[0].keys())
                dtype = [(key, type(records[0][key]).__name__) for key in keys]
                max_len = len(records)
                self.dataset = self.h5file.create_dataset(
                    self.dataset_path, shape=(max_len,), dtype=dtype, maxshape=(None,)
                )

        start_idx = self.pos if hasattr(self, "pos") else 0
        for i, record in enumerate(records):
            if hasattr(self.dataset, "dtype") and self.dataset.dtype.names:
                # Structured array
                self.dataset[start_idx + i] = tuple(record.values())
            else:
                # Need to handle differently
                raise WriteNotSupportedError("hdf5", "Writing to non-structured HDF5 datasets is not yet implemented")
