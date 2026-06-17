from __future__ import annotations

import typing

try:
    import fiona

    HAS_FIONA = True
except ImportError:
    HAS_FIONA = False

from typing import Any

from ..base import BaseCodec, BaseFileIterable
from ..types import Row


class GeoPackageIterable(BaseFileIterable):
    datamode = "binary"

    def __init__(
        self,
        filename: str | None = None,
        stream: typing.IO[Any] | None = None,
        codec: BaseCodec | None = None,
        mode="r",
        layer: str | None = None,
        options: dict[str, Any] | None = None,
    ):
        if options is None:
            options = {}
        if not HAS_FIONA:
            raise ImportError("fiona library is required for GeoPackage support. Install it with: pip install fiona")

        super().__init__(filename, stream, codec=codec, mode=mode, binary=True, encoding="utf8", options=options)
        self.layer = layer
        if "layer" in options:
            self.layer = options["layer"]
        self.reset()

    def reset(self):
        super().reset()
        self.features = []
        self.pos = 0
        self.collection = None

        if self.mode == "r":
            try:
                # Open GeoPackage
                if self.layer:
                    self.collection = fiona.open(self.filename, layer=self.layer, mode="r")
                else:
                    # Use first layer if not specified
                    self.collection = fiona.open(self.filename, mode="r")

                # Read all features
                for feature in self.collection:
                    # Convert fiona feature to GeoJSON-like format
                    geojson_feature = {
                        "type": "Feature",
                        "properties": feature.get("properties", {}),
                        "geometry": feature.get("geometry", {}),
                    }
                    self.features.append(geojson_feature)

                self.iterator = iter(self.features)
            except Exception:
                self.features = []
                self.iterator = iter(self.features)
        elif self.mode in ["w", "wr"]:
            # Initialize writer
            self.writer = None
            self.writer_initialized = False

    @staticmethod
    def id() -> str:
        return "geopackage"

    @staticmethod
    def is_flatonly() -> bool:
        return False

    @staticmethod
    def has_tables() -> bool:
        """Indicates if this format supports multiple tables/layers."""
        return True

    def list_tables(self, filename: str | None = None) -> list[str] | None:
        """List available layer names in the GeoPackage file.

        Args:
            filename: Optional filename. If None, uses instance's filename and reuses open collection.

        Returns:
            list[str]: List of layer names, or empty list if no layers.
        """
        target_filename = filename if filename is not None else self.filename
        if target_filename is None:
            return None

        # fiona can list layers without opening a specific one
        if HAS_FIONA:
            try:
                # Open in read mode to get layer list
                layers = fiona.listlayers(target_filename)
                return list(layers)
            except Exception:
                return []
        return None

    @staticmethod
    def has_totals() -> bool:
        """Has totals indicator"""
        return True

    def totals(self):
        """Returns file totals"""
        if hasattr(self, "features"):
            return len(self.features)
        return 0

    def read(self, skip_empty: bool = True) -> dict:
        """Read single GeoPackage feature"""
        feature = next(self.iterator)
        self.pos += 1
        return feature

    def write(self, record: Row) -> None:
        """Write single GeoPackage feature"""
        if not HAS_FIONA:
            raise ImportError("fiona library is required for GeoPackage support")

        # Initialize writer on first write
        if not hasattr(self, "writer_initialized") or not self.writer_initialized:
            # Determine schema from first record
            geometry = record.get("geometry", {})
            properties = record.get("properties", {})

            # Determine geometry type
            geom_type = geometry.get("type") if geometry else None

            # Create schema
            schema = {"geometry": geom_type or "Unknown", "properties": {}}

            # Add property schemas
            for key, value in properties.items():
                if isinstance(value, int):
                    schema["properties"][key] = "int"
                elif isinstance(value, float):
                    schema["properties"][key] = "float"
                elif isinstance(value, bool):
                    schema["properties"][key] = "bool"
                else:
                    schema["properties"][key] = "str"

            # Create driver options
            driver = "GPKG"
            crs = "EPSG:4326"  # Default to WGS84

            # Open writer
            if self.layer:
                self.writer = fiona.open(self.filename, "w", driver=driver, layer=self.layer, schema=schema, crs=crs)
            else:
                self.writer = fiona.open(self.filename, "w", driver=driver, schema=schema, crs=crs)

            self.writer_initialized = True

        # Write feature in fiona format
        fiona_feature = {
            "type": "Feature",
            "properties": record.get("properties", {}),
            "geometry": record.get("geometry", {}),
        }

        self.writer.write(fiona_feature)
        self.pos += 1

    def write_bulk(self, records: list[Row]) -> None:
        """Write bulk GeoPackage features"""
        for record in records:
            self.write(record)

    def close(self):
        """Close GeoPackage"""
        if hasattr(self, "writer") and self.writer is not None:
            self.writer.close()
        if hasattr(self, "collection") and self.collection is not None:
            self.collection.close()
        super().close()
