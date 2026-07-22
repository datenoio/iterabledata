"""ESRI File Geodatabase reader via Fiona OpenFileGDB driver."""

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


class FileGDBIterable(BaseFileIterable):
    """Read ESRI File Geodatabase (``.gdb``) layers as GeoJSON-like Features.

    Features are streamed from the Fiona collection; the layer is not loaded
    into memory up front. Layer selection uses ``options["layer"]`` or
    ``options["table"]``.
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
                "File Geodatabase support requires 'fiona'. Install with: pip install iterabledata[geospatial]"
            )
        if mode not in ("r",):
            raise WriteNotSupportedError("fgdb", "File Geodatabase is read-only")

        self.layer = options.get("layer") or options.get("table")
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
                "File Geodatabase requires a file path; stream and codec are not supported.",
                filename=None,
                error_code="RESOURCE_REQUIREMENT_NOT_MET",
            )

        layers = fiona.listlayers(self.filename)
        layer = self.layer
        if layer is None:
            if len(layers) == 0:
                raise ValueError(f"No layers found in File Geodatabase: {self.filename}")
            if len(layers) > 1:
                raise ValueError(
                    "File Geodatabase has multiple layers; select one with "
                    f'options={{"layer": "<name>"}} or options={{"table": "<name>"}}. '
                    f"Available layers: {layers}"
                )
            layer = layers[0]

        self._collection = fiona.open(self.filename, layer=layer, driver="OpenFileGDB")
        self._iterator = self._feature_iterator()

    def _feature_iterator(self) -> typing.Iterator[Row]:
        """Yield GeoJSON-like Features from the open Fiona collection."""
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
        return "fgdb"

    @staticmethod
    def is_flatonly() -> bool:
        return False

    @staticmethod
    def has_tables() -> bool:
        return True

    def is_streaming(self) -> bool:
        return True

    def list_tables(self, filename: str | None = None) -> list[str] | None:
        """List layer names via ``fiona.listlayers``."""
        target = filename if filename is not None else self.filename
        if target is None:
            return None
        if not HAS_FIONA:
            return None
        try:
            return list(fiona.listlayers(target))
        except Exception:
            return []

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
        raise WriteNotSupportedError("fgdb", "File Geodatabase is read-only")

    def write_bulk(self, records: list[Row]) -> None:
        raise WriteNotSupportedError("fgdb", "File Geodatabase is read-only")

    def close(self) -> None:
        if self._collection is not None:
            self._collection.close()
            self._collection = None
        super().close()
