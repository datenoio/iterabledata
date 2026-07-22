"""MapInfo Interchange Format (MIF/MID) reader via Fiona MapInfo File driver."""

from __future__ import annotations

import typing
from typing import Any

try:
    import fiona

    HAS_FIONA = True
except ImportError:
    HAS_FIONA = False

from ..base import DEFAULT_BULK_NUMBER, BaseCodec, BaseFileIterable
from ..exceptions import ReadError, WriteNotSupportedError
from ..types import Row


class MapInfoIterable(BaseFileIterable):
    """Read MapInfo ``.mif`` (optionally with co-located ``.mid``) as GeoJSON-like Features.

    Features are streamed from the Fiona collection without loading the full file.
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
        if not HAS_FIONA:
            raise ImportError(
                "MapInfo MIF support requires 'fiona'. Install with: pip install iterabledata[geospatial]"
            )
        if mode not in ("r",):
            raise WriteNotSupportedError("mif", "MapInfo MIF is read-only")

        self._collection = None
        super().__init__(
            filename,
            stream,
            codec=codec,
            mode=mode,
            binary=True,
            encoding="utf8",
            noopen=True,
            options=options,
        )
        self.reset()

    def reset(self) -> None:
        super().reset()
        self.pos = 0
        if self._collection is not None:
            try:
                self._collection.close()
            except Exception:
                pass
            self._collection = None

        if self.filename is None:
            raise ReadError(
                "MapInfo MIF requires a file path; stream and codec are not supported.",
                filename=None,
                error_code="RESOURCE_REQUIREMENT_NOT_MET",
            )

        self._collection = fiona.open(self.filename, driver="MapInfo File")
        self._iterator = self._feature_iterator()

    def _feature_iterator(self) -> typing.Iterator[Row]:
        assert self._collection is not None
        for feature in self._collection:
            yield {
                "type": "Feature",
                "id": feature.get("id"),
                "properties": dict(feature.get("properties") or {}),
                "geometry": feature.get("geometry"),
            }

    @staticmethod
    def id() -> str:
        return "mif"

    @staticmethod
    def is_flatonly() -> bool:
        return False

    def is_streaming(self) -> bool:
        return True

    def read(self, skip_empty: bool = True) -> Row:
        feature = next(self._iterator)
        self.pos += 1
        return feature

    def read_bulk(self, num: int = DEFAULT_BULK_NUMBER) -> list[Row]:
        rows: list[Row] = []
        for _ in range(num):
            try:
                rows.append(self.read())
            except StopIteration:
                break
        return rows

    def write(self, record: Row) -> None:
        raise WriteNotSupportedError("mif", "MapInfo MIF is read-only")

    def write_bulk(self, records: list[Row]) -> None:
        raise WriteNotSupportedError("mif", "MapInfo MIF is read-only")

    def close(self) -> None:
        if self._collection is not None:
            self._collection.close()
            self._collection = None
        super().close()
