"""Streaming FlatGeobuf reader using Fiona's GDAL driver when available."""

from __future__ import annotations

import typing
from typing import Any

try:
    import fiona
except ImportError:
    fiona = None

from ..base import DEFAULT_BULK_NUMBER, BaseCodec, BaseFileIterable
from ..types import Row


class FlatGeobufIterable(BaseFileIterable):
    datamode = "binary"

    def __init__(
        self,
        filename: str | None = None,
        stream: typing.IO[Any] | None = None,
        mode: str = "r",
        codec: BaseCodec | None = None,
        bbox: tuple[float, float, float, float] | None = None,
        options: dict[str, Any] | None = None,
    ):
        if fiona is None:
            raise ImportError(
                "FlatGeobuf support requires Fiona/GDAL. Install with: pip install iterabledata[geospatial]"
            )
        if stream is not None or filename is None:
            raise ValueError("FlatGeobuf requires a local filename")
        self.bbox = bbox
        self._collection = None
        super().__init__(filename, stream, codec=codec, mode=mode, binary=True, noopen=True, options=options or {})
        self.reset()

    @staticmethod
    def id() -> str:
        return "flatgeobuf"

    @staticmethod
    def is_flatonly() -> bool:
        return False

    def is_streaming(self) -> bool:
        return True

    def reset(self) -> None:
        super().reset()
        self.pos = 0
        if self._collection is not None:
            self._collection.close()
        self._collection = fiona.open(self.filename, bbox=self.bbox)

    def totals(self) -> int:
        return len(self._collection) if self._collection is not None else 0

    def read(self, skip_empty: bool = True) -> Row:
        if self._collection is None:
            raise StopIteration
        try:
            feature = next(self._collection)
        except StopIteration:
            raise
        self.pos += 1
        return {"geometry": feature.get("geometry"), **dict(feature.get("properties") or {})}

    def read_bulk(self, num: int = DEFAULT_BULK_NUMBER) -> list[Row]:
        rows: list[Row] = []
        for _ in range(num):
            try:
                rows.append(self.read())
            except StopIteration:
                break
        return rows

    def close(self) -> None:
        if self._collection is not None:
            self._collection.close()
            self._collection = None
        super().close()
