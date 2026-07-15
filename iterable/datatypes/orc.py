from __future__ import annotations

import typing
from typing import Any

import pyorc

from ..base import DEFAULT_BULK_NUMBER, BaseCodec, BaseFileIterable
from ..types import Row


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
    datamode = "binary"

    def __init__(
        self,
        filename: str | None = None,
        stream: typing.IO[Any] | None = None,
        codec: BaseCodec | None = None,
        mode: str = "r",
        keys: list[str] | None = None,
        schema: list[str] = None,
        compression: int = 5,
        options: dict[str, Any] | None = None,
    ):
        if options is None:
            options = {}
        self.keys = keys
        self.schema = schema
        self.compression = compression
        super().__init__(filename, stream, codec=codec, mode=mode, binary=True, options=options)
        self.reset()
        pass

    def reset(self):
        """Reset iterable"""
        super().reset()
        self.pos = 0
        self.reader = None
        if self.mode == "r":
            self.reader = pyorc.Reader(self.fobj, struct_repr=pyorc.StructRepr.DICT)
        self.writer = None
        # When writing without an explicit schema or field list, defer writer
        # creation until the first record is written and infer the field names
        # from it. This mirrors columnar writers (e.g. Parquet) that derive the
        # schema from the data and avoids requiring callers to pass ``keys``.
        self._writer_pending = False
        if self.mode == "w":
            if self.schema is not None or self.keys is not None:
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

    def _ensure_writer(self, record: Row) -> None:
        """Lazily create the writer, inferring field names from the first record."""
        if self._writer_pending:
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
        return len(self.reader)

    def close(self):
        """Close iterable"""
        if self.writer is not None:
            self.writer.close()
        super().close()

    def read(self, skip_empty: bool = True) -> dict:
        """Read single record"""
        row = next(self.reader)
        self.pos += 1
        return row

    def read_bulk(self, num: int = DEFAULT_BULK_NUMBER) -> list[dict]:
        """Read bulk ORC records efficiently.

        Note: pyorc.Reader is an iterator that yields rows one at a time.
        This implementation reads directly from the iterator to avoid
        method call overhead from read().
        """
        chunk = []
        for _n in range(num):
            try:
                # Read directly from iterator to avoid method call overhead
                row = next(self.reader)
                chunk.append(row)
                self.pos += 1
            except StopIteration:
                break
        return chunk

    def write(self, record: Row) -> None:
        """Write single record"""
        self._ensure_writer(record)
        self.writer.write(record)

    def write_bulk(self, records: list[Row]) -> None:
        """Write bulk records"""
        if not records:
            return
        self._ensure_writer(records[0])
        self.writer.writerows(records)
