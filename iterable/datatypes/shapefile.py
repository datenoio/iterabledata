from __future__ import annotations

import typing

try:
    import shapefile

    HAS_SHAPEFILE = True
except ImportError:
    HAS_SHAPEFILE = False

from typing import Any

from ..base import BaseCodec, BaseFileIterable
from ..exceptions import ReadError
from ..types import Row


def shape_to_geojson(shape_record, shape_obj):
    """Convert shapefile record to GeoJSON-like feature"""
    record = shape_record.record
    properties = record.as_dict() if hasattr(record, "as_dict") else dict(record)
    feature = {"type": "Feature", "properties": properties, "geometry": None}

    # Convert shape geometry to GeoJSON
    if shape_obj.shapeType == shapefile.POINT:
        if len(shape_obj.points) > 0:
            feature["geometry"] = {"type": "Point", "coordinates": list(shape_obj.points[0])}
    elif shape_obj.shapeType == shapefile.POLYLINE:
        if len(shape_obj.points) > 0:
            feature["geometry"] = {"type": "LineString", "coordinates": [list(p) for p in shape_obj.points]}
    elif shape_obj.shapeType == shapefile.POLYGON:
        if len(shape_obj.points) > 0:
            # Polygon can have multiple parts
            if len(shape_obj.parts) > 1:
                # MultiPolygon
                parts = []
                for i, part_start in enumerate(shape_obj.parts):
                    part_end = shape_obj.parts[i + 1] if i + 1 < len(shape_obj.parts) else len(shape_obj.points)
                    parts.append([list(p) for p in shape_obj.points[part_start:part_end]])
                feature["geometry"] = {"type": "MultiPolygon", "coordinates": [parts]}
            else:
                feature["geometry"] = {"type": "Polygon", "coordinates": [[list(p) for p in shape_obj.points]]}
    elif shape_obj.shapeType == shapefile.MULTIPOINT:
        if len(shape_obj.points) > 0:
            feature["geometry"] = {"type": "MultiPoint", "coordinates": [list(p) for p in shape_obj.points]}

    return feature


class ShapefileIterable(BaseFileIterable):
    """Esri Shapefile reader.

    Memory behavior: features are read lazily one at a time via
    ``shapefile.Reader.iterShapeRecords()``; the file is never fully
    materialized in memory.
    """

    datamode = "binary"

    def __init__(
        self,
        filename: str | None = None,
        stream: typing.IO[Any] | None = None,
        codec: BaseCodec | None = None,
        mode="r",
        options: dict[str, Any] | None = None,
    ):
        if options is None:
            options = {}
        if not HAS_SHAPEFILE:
            raise ImportError("pyshp library is required for Shapefile support. Install it with: pip install pyshp")

        # Shapefile requires .shp extension, but we accept the base filename
        if filename and not filename.endswith(".shp"):
            # Try to find .shp file
            import os

            base = filename.rsplit(".", 1)[0]
            shp_file = base + ".shp"
            if os.path.exists(shp_file):
                filename = shp_file
            else:
                filename = shp_file  # Will be created if writing

        super().__init__(filename, stream, codec=codec, mode=mode, binary=True, encoding="utf8", options=options)
        self.reset()

    def reset(self):
        super().reset()
        self.pos = 0

        if self.mode == "r":
            if self.filename is None:
                raise ReadError(
                    "Shapefile requires a file path; stream and codec are not supported.",
                    filename=None,
                    error_code="RESOURCE_REQUIREMENT_NOT_MET",
                )
            try:
                self.reader = shapefile.Reader(self.filename)
                self.iterator = self.__iterator()
            except Exception:
                self.reader = None
                self.iterator = iter([])
        elif self.mode in ["w", "wr"]:
            # Initialize writer
            self.writer = None
            self.writer_initialized = False

    def __iterator(self):
        """Lazily convert shape records to GeoJSON-like features."""
        for shape_record in self.reader.iterShapeRecords():
            yield shape_to_geojson(shape_record, shape_record.shape)

    @staticmethod
    def id() -> str:
        return "shapefile"

    @staticmethod
    def is_flatonly() -> bool:
        return False

    def is_streaming(self) -> bool:
        """Features are read incrementally from the shapefile reader."""
        return True

    @staticmethod
    def has_totals() -> bool:
        """Has totals indicator"""
        return True

    def totals(self):
        """Returns file totals"""
        if getattr(self, "reader", None) is not None:
            return len(self.reader)
        return 0

    def read(self, skip_empty: bool = True) -> dict:
        """Read single shapefile feature"""
        feature = next(self.iterator)
        self.pos += 1
        return feature

    def write(self, record: Row) -> None:
        """Write single shapefile feature"""
        if not HAS_SHAPEFILE:
            raise ImportError("pyshp library is required for Shapefile support")

        # Initialize writer on first write
        if not hasattr(self, "writer_initialized") or not self.writer_initialized:
            # Determine shape type from first record
            geometry = record.get("geometry", {})
            geom_type = geometry.get("type") if geometry else None

            shape_type = shapefile.POINT  # default
            if geom_type == "LineString":
                shape_type = shapefile.POLYLINE
            elif geom_type == "Polygon":
                shape_type = shapefile.POLYGON
            elif geom_type == "MultiPoint":
                shape_type = shapefile.MULTIPOINT

            # Get field names from properties
            properties = record.get("properties", {})
            fields = []
            for key, value in properties.items():
                # Determine field type
                if isinstance(value, int):
                    field_type = "N"
                    field_length = 10
                elif isinstance(value, float):
                    field_type = "F"
                    field_length = 19
                else:
                    field_type = "C"
                    field_length = 254

                field_def = [key, field_type, field_length]
                if field_type == "F":
                    field_def.append(10)  # decimal places
                fields.append(field_def)

            # Create writer
            base_name = self.filename.rsplit(".", 1)[0]
            self.writer = shapefile.Writer(base_name, shapeType=shape_type)

            # Store field names for later use
            self.field_names = list(properties.keys())

            # Add field definitions
            for field in fields:
                self.writer.field(*field)

            self.writer_initialized = True

        # Extract geometry and properties
        geometry = record.get("geometry", {})
        properties = record.get("properties", {})

        # Convert geometry to shapefile format
        geom_type = geometry.get("type")
        coords = geometry.get("coordinates", [])

        shape_coords = []
        if geom_type == "Point":
            shape_coords = coords
        elif geom_type == "LineString":
            shape_coords = coords
        elif geom_type == "Polygon":
            # Polygon coordinates are nested
            if isinstance(coords[0], list) and isinstance(coords[0][0], list):
                shape_coords = coords[0]  # Outer ring
            else:
                shape_coords = coords
        elif geom_type == "MultiPoint":
            shape_coords = coords

        # Write record
        if shape_coords:
            if geom_type == "Point":
                self.writer.point(*shape_coords)
            elif geom_type == "LineString":
                self.writer.line([shape_coords])
            elif geom_type == "Polygon":
                self.writer.poly([shape_coords])
            elif geom_type == "MultiPoint":
                self.writer.multipoint(shape_coords)

        # Write attributes
        if hasattr(self, "field_names"):
            attr_values = [properties.get(field_name, "") for field_name in self.field_names]
        else:
            attr_values = list(properties.values())
        self.writer.record(*attr_values)

        self.pos += 1

    def write_bulk(self, records: list[Row]) -> None:
        """Write bulk shapefile features"""
        for record in records:
            self.write(record)

    def close(self):
        """Close shapefile"""
        if hasattr(self, "writer") and self.writer is not None:
            self.writer.close()
        if hasattr(self, "reader") and self.reader is not None:
            # Shapefile reader doesn't need explicit close
            pass
        super().close()
