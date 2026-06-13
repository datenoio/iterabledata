from __future__ import annotations

import typing

try:
    import vortex as vx

    HAS_VORTEX = True
except ImportError:
    HAS_VORTEX = False

try:
    import pyarrow

    HAS_PYARROW = True
except ImportError:
    HAS_PYARROW = False

from typing import Any

from ..base import BaseCodec, BaseFileIterable
from ..exceptions import ReadError
from ..types import Row

DEFAULT_BATCH_SIZE = 1024


class VortexIterable(BaseFileIterable):
    datamode = "binary"

    def __init__(
        self,
        filename: str = None,
        stream: typing.IO[Any] | None = None,
        mode: str = "r",
        codec: BaseCodec | None = None,
        batch_size: int = DEFAULT_BATCH_SIZE,
        options: dict[str, Any] | None = None,
    ):
        if options is None:
            options = {}
        # Validate resource requirements before checking optional dependencies so
        # that misuse (e.g. passing a stream) is reported as a ReadError regardless
        # of whether the optional Vortex dependency is installed.
        if stream is not None:
            raise ReadError(
                "Vortex format does not support stream mode. Use filename instead.",
                filename=None,
                error_code="RESOURCE_REQUIREMENT_NOT_MET",
            )
        if filename is None:
            raise ReadError(
                "Vortex format requires a filename",
                filename=None,
                error_code="RESOURCE_REQUIREMENT_NOT_MET",
            )
        if not HAS_VORTEX:
            raise ImportError(
                "Vortex support requires 'vortex-data' package. Install it with: pip install iterabledata[vortex]"
            )
        if not HAS_PYARROW:
            raise ImportError("Vortex support requires 'pyarrow' package. Install it with: pip install pyarrow")
        self.batch_size = batch_size
        self.__buffer = []
        self.vortex_file = None
        self.iterator = None
        self.pos = 0
        super().__init__(filename, stream, codec=codec, mode=mode, binary=True, options=options)
        # Initialize after super().__init__ to ensure filename is set
        self.reset()

    def reset(self):
        """Reset iterable"""
        super().reset()
        self.pos = 0
        # Close previous vortex_file if it exists
        if self.vortex_file is not None:
            self.vortex_file = None
        self.iterator = None
        if self.mode == "r":
            # Vortex requires a file path
            if self.filename:
                self.vortex_file = vx.open(self.filename)
                scan = self.vortex_file.scan(batch_size=self.batch_size)
                self.iterator = self.__iterator(scan)
            else:
                raise ReadError(
                    "Vortex reading requires filename",
                    filename=None,
                    error_code="RESOURCE_REQUIREMENT_NOT_MET",
                )
        # For write mode, buffer will be flushed on close

    @staticmethod
    def id() -> str:
        return "vortex"

    @staticmethod
    def is_flatonly() -> bool:
        return True

    @staticmethod
    def has_totals() -> bool:
        """Has totals indicator"""
        return True

    def totals(self):
        """Returns file totals"""
        if self.mode == "r" and self.filename:
            # Count rows by scanning (open a new scan to avoid consuming the iterator)
            try:
                vortex_file = vx.open(self.filename)
                scan = vortex_file.scan()
                count = 0
                for batch in scan:
                    # Count rows in each batch
                    if hasattr(batch, "to_arrow_array"):
                        arrow_array = batch.to_arrow_array()
                        if isinstance(arrow_array, pyarrow.Table):
                            count += len(arrow_array)
                        elif isinstance(arrow_array, pyarrow.RecordBatch):
                            count += len(arrow_array)
                        elif isinstance(arrow_array, pyarrow.Array):
                            count += len(arrow_array)
                        else:
                            # Try to get length
                            try:
                                count += len(arrow_array)
                            except (TypeError, AttributeError):
                                count += 1
                    elif hasattr(batch, "__len__"):
                        count += len(batch)
                    else:
                        count += 1
                return count
            except Exception:
                return 0
        return 0

    def flush(self):
        """Flush all buffered data"""
        # For Vortex, we accumulate all data and write once at close
        # This is because vx.io.write() overwrites the file
        # So we just keep the buffer and write everything on close
        pass

    def close(self):
        """Close iterable"""
        if self.mode == "w" and self.__buffer:
            if not HAS_PYARROW:
                raise ImportError("PyArrow is required for writing Vortex files")

            # Convert all buffered records to PyArrow Table
            table = pyarrow.Table.from_pylist(self.__buffer)
            # Write using Vortex (requires file path)
            if self.filename:
                vx.io.write(table, self.filename)
            self.__buffer = []
        # Vortex files don't need explicit close, but reset reference
        if self.vortex_file is not None:
            self.vortex_file = None
        super().close()

    def __iterator(self, scan):
        """Iterator for reading records from Vortex scan"""
        for batch in scan:
            # Convert Vortex batch to PyArrow format
            try:
                # Try to convert batch to arrow array/table
                if hasattr(batch, "to_arrow_array"):
                    arrow_data = batch.to_arrow_array()
                elif hasattr(batch, "to_arrow"):
                    arrow_data = batch.to_arrow()
                elif hasattr(batch, "to_table"):
                    arrow_data = batch.to_table()
                else:
                    # Assume batch is already a PyArrow object
                    arrow_data = batch

                # Convert PyArrow data to list of dicts
                if isinstance(arrow_data, pyarrow.Table):
                    # Table: convert directly to list of dicts
                    yield from arrow_data.to_pylist()
                elif isinstance(arrow_data, pyarrow.RecordBatch):
                    # RecordBatch: convert to list of dicts
                    yield from arrow_data.to_pylist()
                elif isinstance(arrow_data, pyarrow.StructArray):
                    # StructArray: convert to list of dicts
                    yield from arrow_data.to_pylist()
                elif isinstance(arrow_data, pyarrow.Array):
                    # Handle non-struct arrays (single column)
                    for i in range(len(arrow_data)):
                        value = arrow_data[i].as_py()
                        yield {"value": value}
                else:
                    # Try to convert to table
                    try:
                        if hasattr(arrow_data, "to_pylist"):
                            yield from arrow_data.to_pylist()
                        elif hasattr(arrow_data, "to_table"):
                            yield from arrow_data.to_table().to_pylist()
                        else:
                            # Last resort: try to create a table
                            if isinstance(arrow_data, list):
                                # If it's a list, try to convert
                                table = pyarrow.Table.from_pylist(arrow_data)
                                yield from table.to_pylist()
                            else:
                                # Convert single array to table
                                table = pyarrow.Table.from_arrays([arrow_data])
                                yield from table.to_pylist()
                    except Exception as e:
                        # If all else fails, create a simple dict
                        yield {"data": str(arrow_data), "_error": str(e)}
            except Exception as e:
                # If batch processing fails, yield error info
                yield {"_error": f"Failed to process batch: {str(e)}"}

    def read(self, skip_empty: bool = True) -> dict:
        """Read single record"""
        if self.iterator is None:
            raise RuntimeError("Iterator not initialized. Call reset() first.")
        try:
            row = next(self.iterator)
            self.pos += 1
            return row
        except StopIteration:
            raise StopIteration from None

    def write(self, record: Row) -> None:
        """Write single record"""
        self.write_bulk([record])

    def write_bulk(self, records: list[Row]) -> None:
        """Write bulk records"""
        if not records:
            return
        self.__buffer.extend(records)
        # Note: We accumulate all writes and flush on close
        # This is because vx.io.write() overwrites the file
