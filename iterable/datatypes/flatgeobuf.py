"""Streaming FlatGeobuf reader/writer using Fiona's GDAL driver when available."""

from __future__ import annotations

import typing
from typing import Any

try:
    import fiona
except ImportError:
    fiona = None

from ..base import DEFAULT_BULK_NUMBER, BaseCodec, BaseFileIterable
from ..exceptions import FormatParseError, WriteError
from ..types import Row

_DRIVER = "FlatGeobuf"

# Python type -> Fiona field type used when the write schema is inferred from
# the first record. ``int64`` avoids overflow surprises for large ids.
_PROPERTY_TYPES: dict[type, str] = {
    bool: "bool",
    int: "int64",
    float: "float",
    str: "str",
}


class FlatGeobufIterable(BaseFileIterable):
    datamode = "binary"

    def __init__(
        self,
        filename: str | None = None,
        stream: typing.IO[Any] | None = None,
        mode: str = "r",
        codec: BaseCodec | None = None,
        bbox: tuple[float, float, float, float] | None = None,
        crs: Any = None,
        spatial_index: bool = True,
        geometry_type: str | None = None,
        options: dict[str, Any] | None = None,
    ):
        if fiona is None:
            raise ImportError(
                "FlatGeobuf support requires Fiona/GDAL. Install with: pip install iterabledata[geospatial]"
            )
        if stream is not None or filename is None:
            raise ValueError("FlatGeobuf requires a local filename")
        if codec is not None:
            raise ValueError("FlatGeobuf does not support codec wrapping")
        self.bbox = bbox
        self.crs = crs
        self.spatial_index = spatial_index
        self.geometry_type = geometry_type
        self._collection = None
        self._writer = None
        self._iterator = None
        self._totals = 0
        super().__init__(filename, stream, codec=codec, mode=mode, binary=True, noopen=True, options=options or {})
        self.reset()

    @staticmethod
    def id() -> str:
        return "flatgeobuf"

    @staticmethod
    def is_flatonly() -> bool:
        return False

    @staticmethod
    def has_totals() -> bool:
        return True

    def is_streaming(self) -> bool:
        return True

    def reset(self) -> None:
        super().reset()
        self.pos = 0
        for handle in (self._collection, self._writer):
            if handle is not None:
                handle.close()
        self._collection = None
        self._writer = None
        self._iterator = None
        self._totals = 0
        if self.mode == "r":
            try:
                self._collection = fiona.open(self.filename)
            except fiona.errors.DriverError as exc:
                raise FormatParseError(
                    format_id="flatgeobuf",
                    message=str(exc),
                    filename=getattr(self, "filename", None),
                ) from exc
            # Count before creating the read cursor: fiona iteration contexts
            # share the GDAL layer, and the empty-layer fallback scan below
            # would otherwise disturb an in-progress read.
            try:
                self._totals = len(self._collection)
            except TypeError:
                # Some driver/library versions cannot count an empty layer.
                self._totals = sum(1 for _ in self._collection.filter())
            # ``filter(bbox=...)`` drives the packed spatial index; passing
            # ``bbox`` to ``fiona.open`` is silently ignored by the driver.
            # Without an index GDAL falls back to a full scan with the same
            # filtering semantics.
            self._iterator = (
                self._collection.filter(bbox=self.bbox) if self.bbox is not None else iter(self._collection)
            )

    def totals(self) -> int:
        return self._totals

    # -- Reading ------------------------------------------------------------

    def read(self, skip_empty: bool = True) -> Row:
        if self._collection is None or self._iterator is None:
            raise StopIteration
        try:
            feature = next(self._iterator)
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

    # -- Writing ------------------------------------------------------------

    def _to_feature(self, record: Row) -> dict[str, Any]:
        """Accept both the read row shape and full GeoJSON Features."""
        if record.get("type") == "Feature" and "properties" in record:
            return {"geometry": record.get("geometry"), "properties": dict(record.get("properties") or {})}
        properties = {key: value for key, value in record.items() if key != "geometry"}
        return {"geometry": record.get("geometry"), "properties": properties}

    def _infer_schema(self, feature: dict[str, Any]) -> dict[str, Any]:
        geometry = feature.get("geometry") or {}
        geom_type = self.geometry_type or geometry.get("type") or "Unknown"
        fields = {}
        for key, value in (feature.get("properties") or {}).items():
            fields[key] = _PROPERTY_TYPES.get(type(value), "str")
        return {"geometry": geom_type, "properties": fields}

    def _ensure_writer(self, feature: dict[str, Any]) -> None:
        if self._writer is not None:
            return
        kwargs: dict[str, Any] = {}
        if self.crs is not None:
            kwargs["crs"] = self.crs
        if not self.spatial_index:
            kwargs["SPATIAL_INDEX"] = "NO"
        try:
            self._writer = fiona.open(
                self.filename,
                "w",
                driver=_DRIVER,
                schema=self._infer_schema(feature),
                **kwargs,
            )
        except Exception as exc:
            raise WriteError(
                f"Failed to open FlatGeobuf writer: {exc}",
                filename=getattr(self, "filename", None),
                error_code="WRITER_OPEN_FAILED",
            ) from exc

    def write(self, record: Row) -> None:
        """Write a single feature; the file is streamed, never buffered whole."""
        # Apply validation hooks if configured
        if self._validation_hooks:
            validated = self._apply_validation_hooks(record)
            if validated is None:  # Skipped
                return  # Don't write invalid row
            record = validated

        feature = self._to_feature(record)
        self._ensure_writer(feature)
        if self._writer is not None:
            # Fiona requires every record to match the established schema
            # exactly: align property keys (missing -> None, extras dropped),
            # mirroring the Parquet writer's schema normalization.
            schema_fields = list(self._writer.schema["properties"].keys())
            properties = feature.get("properties") or {}
            feature = {**feature, "properties": {key: properties.get(key) for key in schema_fields}}
        try:
            self._writer.write(feature)
        except Exception as exc:
            raise WriteError(
                f"Failed to write FlatGeobuf feature: {exc}",
                filename=getattr(self, "filename", None),
                error_code="FEATURE_WRITE_FAILED",
            ) from exc
        self.pos += 1

    def write_bulk(self, records: list[Row]) -> None:
        for record in records:
            self.write(record)

    def close(self) -> None:
        for attr in ("_collection", "_writer"):
            handle = getattr(self, attr, None)
            if handle is not None:
                handle.close()
                setattr(self, attr, None)
        super().close()
