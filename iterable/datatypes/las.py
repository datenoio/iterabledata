"""LAS LiDAR point cloud reader via laspy."""

from __future__ import annotations

import typing
from typing import Any

try:
    import laspy

    HAS_LASPY = True
except ImportError:
    HAS_LASPY = False

from ..base import DEFAULT_BULK_NUMBER, BaseCodec, BaseFileIterable
from ..exceptions import ReadError, WriteNotSupportedError
from ..types import Row


class LASIterable(BaseFileIterable):
    """Read LAS point clouds one point at a time.

    Each record includes ``x``, ``y``, ``z``, ``intensity``, ``classification``,
    and ``return_number`` when available.
    """

    datamode = "binary"

    def __init__(
        self,
        filename: str | None = None,
        stream: typing.IO[Any] | None = None,
        codec: BaseCodec | None = None,
        mode: str = "r",
        options: dict[str, Any] | None = None,
    ):
        if options is None:
            options = {}
        if not HAS_LASPY:
            raise ImportError("LAS support requires 'laspy'. Install with: pip install iterabledata[lidar]")
        if mode not in ("r",):
            raise WriteNotSupportedError("las", "LAS is read-only")

        self._reader = None
        self._point_count: int | None = None
        self._iterator: typing.Iterator[Row] | None = None
        super().__init__(
            filename,
            stream,
            codec=codec,
            mode=mode,
            binary=True,
            noopen=True,
            options=options,
        )
        self.reset()

    def reset(self) -> None:
        super().reset()
        self.pos = 0
        if self._reader is not None:
            try:
                self._reader.close()
            except Exception:
                pass
            self._reader = None

        if self.filename is None:
            raise ReadError(
                "LAS requires a file path; stream and codec are not supported.",
                filename=None,
                error_code="RESOURCE_REQUIREMENT_NOT_MET",
            )

        self._reader = laspy.open(self.filename)
        self._point_count = int(self._reader.header.point_count)
        self._iterator = self._point_iterator()

    def _point_iterator(self) -> typing.Iterator[Row]:
        assert self._reader is not None
        # Stream in small chunks so the first yield does not require full load.
        chunk_size = int(self.options.get("chunk_size", 50_000)) if self.options else 50_000
        for points in self._reader.chunk_iterator(chunk_size):
            n = len(points)
            xs = points.x
            ys = points.y
            zs = points.z
            has_intensity = hasattr(points, "intensity")
            has_classification = hasattr(points, "classification")
            has_return = hasattr(points, "return_number")
            intensity = points.intensity if has_intensity else None
            classification = points.classification if has_classification else None
            return_number = points.return_number if has_return else None
            for i in range(n):
                yield {
                    "x": float(xs[i]),
                    "y": float(ys[i]),
                    "z": float(zs[i]),
                    "intensity": int(intensity[i]) if intensity is not None else None,
                    "classification": int(classification[i]) if classification is not None else None,
                    "return_number": int(return_number[i]) if return_number is not None else None,
                }

    @staticmethod
    def id() -> str:
        return "las"

    @staticmethod
    def is_flatonly() -> bool:
        return True

    def is_streaming(self) -> bool:
        return True

    @staticmethod
    def has_totals() -> bool:
        return True

    def totals(self) -> int:
        return self._point_count or 0

    def read(self, skip_empty: bool = True) -> Row:
        assert self._iterator is not None
        row = next(self._iterator)
        self.pos += 1
        return row

    def read_bulk(self, num: int = DEFAULT_BULK_NUMBER) -> list[Row]:
        rows: list[Row] = []
        for _ in range(num):
            try:
                rows.append(self.read())
            except StopIteration:
                break
        return rows

    def write(self, record: Row) -> None:
        raise WriteNotSupportedError("las", "LAS is read-only")

    def write_bulk(self, records: list[Row]) -> None:
        raise WriteNotSupportedError("las", "LAS is read-only")

    def close(self) -> None:
        if self._reader is not None:
            try:
                self._reader.close()
            except Exception:
                pass
            self._reader = None
        super().close()
