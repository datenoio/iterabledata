from __future__ import annotations

import typing

try:
    import numpy as np

    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False

from typing import Any

from ..base import BaseCodec, BaseFileIterable
from ..exceptions import FormatNotSupportedError, WriteError
from ..types import Row


class NumPyIterable(BaseFileIterable):
    """
    NumPy array format reader/writer.

    Supports:
    - .npy files: Single NumPy array (1D or 2D)
    - .npz files: Compressed archive of multiple named arrays

    For 2D arrays, each row is returned as a dictionary.
    For 1D arrays, each element is returned as a dictionary with a single key.
    For .npz files, each array can be accessed separately.
    """

    datamode = "binary"

    def __init__(
        self,
        filename: str = None,
        stream: typing.IO[Any] | None = None,
        codec: BaseCodec | None = None,
        mode: str = "r",
        array_name: str = None,
        options: dict[str, Any] | None = None,
    ):
        """
        Initialize NumPy iterable.

        Args:
            array_name: For .npz files, name of the array to iterate over.
                       If None, uses the first array found.
        """
        if options is None:
            options = {}
        if not HAS_NUMPY:
            raise ImportError("NumPy support requires 'numpy' package")
        self.array_name = array_name
        if "array_name" in options:
            self.array_name = options["array_name"]
        self.pos = 0
        self.is_npz = False
        self.npz_data = None
        self.current_array = None
        self.array_keys = []
        super().__init__(filename, stream, codec=codec, binary=True, mode=mode, options=options)
        self.reset()

    def reset(self):
        """Reset iterable"""
        super().reset()
        self.pos = 0

        # Close any existing .npz file
        if hasattr(self, "npz_data") and self.npz_data is not None:
            self.npz_data.close()
            self.npz_data = None

        if self.mode == "r":
            # NumPy requires file path for reading
            if self.filename:
                # Check if it's .npz or .npy
                if self.filename.lower().endswith(".npz"):
                    self.is_npz = True
                    self.npz_data = np.load(self.filename)
                    self.array_keys = list(self.npz_data.keys())
                    if self.array_name:
                        if self.array_name not in self.array_keys:
                            raise ValueError(
                                f"Array '{self.array_name}' not found in .npz file. Available: {self.array_keys}"
                            )
                        self.current_array = self.npz_data[self.array_name]
                    elif self.array_keys:
                        # Use first array if no name specified
                        self.array_name = self.array_keys[0]
                        self.current_array = self.npz_data[self.array_name]
                    else:
                        raise FormatNotSupportedError(
                            "numpy",
                            reason="NPZ file contains no arrays",
                        )
                else:
                    # .npy file
                    self.is_npz = False
                    self.current_array = np.load(self.filename)
                self.iterator = self.__iterator()
            else:
                raise ValueError("NumPy file reading requires filename (not stream)")
        else:
            # Write mode
            if not self.filename:
                raise WriteError(
                    "NumPy file writing requires filename",
                    filename=None,
                    error_code="RESOURCE_REQUIREMENT_NOT_MET",
                )
            self.current_array = None
            self.rows_written = []

    def __iterator(self):
        """Iterator for reading NumPy array"""
        if self.current_array is None:
            return

        if len(self.current_array.shape) == 1:
            # 1D array - treat each element as a record
            for _, value in enumerate(self.current_array):
                yield {"value": value.item() if hasattr(value, "item") else value}
        elif len(self.current_array.shape) == 2:
            # 2D array - treat each row as a record
            for idx in range(self.current_array.shape[0]):
                row = self.current_array[idx]
                # Convert row to dict with column indices as keys
                yield {
                    f"col_{j}": row[j].item() if hasattr(row[j], "item") else row[j]
                    for j in range(self.current_array.shape[1])
                }
        else:
            raise FormatNotSupportedError(
                "numpy",
                reason=f"Only 1D and 2D arrays are supported for iteration, got shape {self.current_array.shape}",
            )

    @staticmethod
    def id() -> str:
        return "numpy"

    @staticmethod
    def is_flatonly() -> bool:
        return True

    @staticmethod
    def has_tables() -> bool:
        """Indicates if this format supports multiple tables/datasets."""
        return True  # .npz files can contain multiple arrays

    def list_tables(self, filename: str | None = None) -> list[str] | None:
        """List available arrays in .npz file.

        Args:
            filename: Optional filename. If None, uses instance's filename.

        Returns:
            list[str]: List of array names for .npz files, or None for .npy files.
        """
        target_filename = filename if filename is not None else self.filename
        if target_filename is None:
            return None

        if target_filename.lower().endswith(".npz"):
            npz_data = np.load(target_filename)
            try:
                return list(npz_data.keys())
            finally:
                npz_data.close()
        else:
            # .npy files contain a single array, no named tables
            return None

    @staticmethod
    def has_totals() -> bool:
        """Has totals indicator"""
        return True

    def totals(self):
        """Returns total number of rows/elements"""
        if hasattr(self, "current_array") and self.current_array is not None:
            if len(self.current_array.shape) >= 1:
                return self.current_array.shape[0]
        return 0

    def read(self, skip_empty: bool = True) -> dict:
        """Read single NumPy array record"""
        row = next(self.iterator)
        self.pos += 1
        return row

    def write(self, record: Row) -> None:
        """Write single NumPy array record"""
        self.write_bulk([record])

    def write_bulk(self, records: list[Row]) -> None:
        """Write bulk NumPy array records"""
        if not records:
            return

        # Collect rows
        self.rows_written.extend(records)

    def close(self):
        """Close NumPy file and save if in write mode"""
        if self.mode == "w" and self.rows_written:
            # Convert records to NumPy array
            if not self.rows_written:
                return

            # Determine array shape from first record
            first_record = self.rows_written[0]
            if isinstance(first_record, dict):
                # Get all unique keys across all records
                all_keys = set()
                for record in self.rows_written:
                    all_keys.update(record.keys())
                sorted_keys = sorted(all_keys)

                # Create 2D array
                num_rows = len(self.rows_written)
                num_cols = len(sorted_keys)
                array_data = np.zeros((num_rows, num_cols), dtype=float)

                for i, record in enumerate(self.rows_written):
                    for j, key in enumerate(sorted_keys):
                        value = record.get(key, 0)
                        try:
                            array_data[i, j] = float(value)
                        except (ValueError, TypeError):
                            array_data[i, j] = 0.0

                # Save array
                if self.filename.lower().endswith(".npz"):
                    # For .npz, we need an array name
                    array_name = self.array_name if self.array_name else "data"
                    np.savez_compressed(self.filename, **{array_name: array_data})
                else:
                    # .npy file
                    np.save(self.filename, array_data)
            else:
                # Single value per record (1D array)
                array_data = np.array([float(r) if isinstance(r, (int, float)) else 0.0 for r in self.rows_written])
                if self.filename.lower().endswith(".npz"):
                    array_name = self.array_name if self.array_name else "data"
                    np.savez_compressed(self.filename, **{array_name: array_data})
                else:
                    np.save(self.filename, array_data)

        # Close .npz file if open
        if hasattr(self, "npz_data") and self.npz_data is not None:
            self.npz_data.close()
            self.npz_data = None

        super().close()
