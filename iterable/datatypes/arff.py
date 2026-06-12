from __future__ import annotations

import typing
from typing import Any

from ..base import DEFAULT_BULK_NUMBER, BaseCodec, BaseFileIterable
from ..exceptions import WriteNotSupportedError
from ..types import Row

try:
    import arff

    HAS_ARFF = True
except ImportError:
    HAS_ARFF = False


class ARFFIterable(BaseFileIterable):
    """ARFF (Attribute-Relation File Format) iterable"""

    def __init__(
        self,
        filename: str = None,
        stream: typing.IO[Any] | None = None,
        codec: BaseCodec | None = None,
        mode: str = "r",
        encoding: str = "utf8",
        options: dict[str, Any] | None = None,
    ):
        if options is None:
            options = {}
        if not HAS_ARFF:
            raise ImportError(
                "ARFF format requires 'liac-arff' package. "
                "Install it with: pip install iterabledata[arff] or pip install liac-arff"
            )
        super().__init__(filename, stream, codec=codec, mode=mode, binary=False, encoding=encoding, options=options)
        self.reset()
        pass

    def reset(self):
        """Reset iterable"""
        super().reset()
        self.pos = 0
        if self.mode == "r":
            # Read entire ARFF content
            content = self.fobj.read()

            # Parse ARFF file
            arff_data = arff.loads(content)

            # Extract relation name
            self.relation_name = arff_data.get("relation", "unknown")

            # Extract attribute names
            attributes = arff_data.get("attributes", [])
            self.keys = [attr[0] for attr in attributes]

            # Extract data
            self.data = arff_data.get("data", [])

            # Convert sparse format to dense if needed
            self.rows = []
            for row in self.data:
                if isinstance(row, dict):
                    # Sparse format: {index: value, ...}
                    dense_row = [None] * len(self.keys)
                    for idx, val in row.items():
                        dense_row[int(idx)] = val
                    self.rows.append(dense_row)
                else:
                    # Dense format: list of values
                    # Handle missing values (represented as '?' or None)
                    processed_row = []
                    for _i, val in enumerate(row):
                        if val == "?" or val is None:
                            processed_row.append(None)
                        else:
                            processed_row.append(val)
                    self.rows.append(processed_row)
        else:
            self.rows = []
            self.keys = []
            self.relation_name = None

    @staticmethod
    def id() -> str:
        return "arff"

    @staticmethod
    def is_flatonly() -> bool:
        return True

    def read(self, skip_empty: bool = True) -> dict:
        """Read single ARFF record"""
        if self.pos >= len(self.rows):
            raise StopIteration

        row_values = self.rows[self.pos]
        result = dict(zip(self.keys, row_values, strict=False))
        # Add relation name as metadata if needed
        if self.relation_name:
            result["_relation"] = self.relation_name
        self.pos += 1
        return result

    def read_bulk(self, num: int = DEFAULT_BULK_NUMBER) -> list[dict]:
        """Read bulk ARFF records efficiently using slicing.

        This optimized implementation uses list slicing instead of calling
        read() in a loop, providing significant performance improvements
        for in-memory data access.
        """
        # Calculate how many rows are available
        remaining = len(self.rows) - self.pos
        if remaining == 0:
            return []

        # Use slicing to get the requested number of rows
        read_count = min(num, remaining)
        row_slice = self.rows[self.pos : self.pos + read_count]

        # Convert row values to dictionaries
        chunk = []
        for row_values in row_slice:
            result = dict(zip(self.keys, row_values, strict=False))
            # Add relation name as metadata if needed
            if self.relation_name:
                result["_relation"] = self.relation_name
            chunk.append(result)

        # Update position
        self.pos += read_count

        return chunk

    def write(self, record: Row) -> None:
        """Write single ARFF record (not supported)"""
        raise WriteNotSupportedError("arff", "ARFF write mode is not currently supported")

    def write_bulk(self, records: list[Row]) -> None:
        """Write bulk ARFF records (not supported)"""
        raise WriteNotSupportedError("arff", "ARFF write mode is not currently supported")
