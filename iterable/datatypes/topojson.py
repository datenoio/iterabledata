from __future__ import annotations

import json
import os
import typing

try:
    import topojson

    HAS_TOPOJSON = True
except ImportError:
    HAS_TOPOJSON = False

try:
    import ijson

    HAS_IJSON = True
except ImportError:
    HAS_IJSON = False

from typing import Any

from ..base import BaseCodec, BaseFileIterable
from ..exceptions import FormatParseError
from ..types import Row


class TopoJSONIterable(BaseFileIterable):
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
        self._streaming = False
        self._parser = None
        self._items_buffer = []
        super().__init__(filename, stream, codec=codec, binary=False, mode=mode, encoding=encoding, options=options)
        self.reset()

    def _should_use_streaming(self) -> bool:
        """Determine if streaming parser should be used"""
        if not HAS_IJSON:
            return False
        # Use streaming for files larger than 10MB or non-seekable streams
        if self.filename:
            try:
                file_size = os.path.getsize(self.filename)
                return file_size > 10 * 1024 * 1024  # 10MB threshold
            except (OSError, TypeError):
                # Can't determine size, use streaming for safety
                return True
        # For streams without filename, use streaming if not seekable
        if hasattr(self.fobj, "seekable"):
            return not self.fobj.seekable()
        # Default to streaming for unknown cases
        return True

    def reset(self):
        """Reset iterable"""
        super().reset()
        self.pos = 0
        self._streaming = False
        self._parser = None
        self._items_buffer = []
        if self.mode in ["w", "wr"]:
            self._write_buffer = []
        elif self.mode == "r":
            # Determine if we should use streaming parser
            if self._should_use_streaming():
                # Use streaming parser for large files
                self._streaming = True
                self.fobj.seek(0)
                try:
                    # Stream objects from TopoJSON "objects" key
                    # TopoJSON structure: {"type": "Topology", "objects": {"obj1": {...}, "obj2": {...}}, "arcs": [...]}
                    # We'll stream individual objects from the objects dictionary
                    self._parser = ijson.items(self.fobj, "objects.item")
                    # Pre-fetch first item to check if parser works
                    try:
                        self._first_item = next(self._parser)
                        self._items_buffer = [self._first_item]
                        self.total = None  # Unknown total for streaming
                    except StopIteration:
                        self._items_buffer = []
                        self.total = 0
                except Exception:
                    # Fallback to non-streaming if streaming fails
                    self._streaming = False
                    self._parser = None
                    self.fobj.seek(0)
                    # Continue with non-streaming approach below
            else:
                # Use traditional json.load() for small files
                self._streaming = False

            if not self._streaming:
                # Load TopoJSON document (for small files or when streaming fails)
                try:
                    self.fobj.seek(0)
                    self.data = json.load(self.fobj)
                except json.JSONDecodeError as e:
                    raise FormatParseError(
                        format_id="topojson",
                        message=str(e),
                        filename=self.filename,
                    ) from e

                # If topojson library is available, convert to GeoJSON
                if HAS_TOPOJSON:
                    try:
                        # topojson library provides conversion utilities
                        # We'll extract features from all objects
                        self.features = []
                        objects = self.data.get("objects", {})
                        for obj_name, _obj_data in objects.items():
                            # Convert TopoJSON to GeoJSON using the library
                            topo = topojson.Topology(self.data)
                            geojson_data = topo.to_geojson(obj_name)
                            if geojson_data.get("type") == "FeatureCollection":
                                self.features.extend(geojson_data.get("features", []))
                            else:
                                self.features.append(geojson_data)
                    except Exception:
                        # If library conversion fails, fall back to raw data
                        self.features = [self.data]
                else:
                    # Without library, just return the raw TopoJSON structure
                    self.features = [self.data]

                self.iterator = iter(self.features)

    @staticmethod
    def id() -> str:
        return "topojson"

    @staticmethod
    def is_flatonly() -> bool:
        return False

    @staticmethod
    def has_totals() -> bool:
        return True

    def totals(self):
        if hasattr(self, "features"):
            return len(self.features)
        return 0

    def is_streaming(self) -> bool:
        """Returns True if using streaming parser."""
        return self._streaming

    def read(self, skip_empty: bool = True) -> dict:
        if self._streaming:
            # Use streaming parser
            if self._items_buffer:
                item = self._items_buffer.pop(0)
            else:
                try:
                    item = next(self._parser)
                except StopIteration as err:
                    raise StopIteration from err
            self.pos += 1
            # Return the object as-is (streaming doesn't support full TopoJSON->GeoJSON conversion)
            # For full conversion, the entire topology is needed, which requires loading everything
            return item
        else:
            # Use non-streaming iterator
            feature = next(self.iterator)
            self.pos += 1
            return feature

    def write(self, record: Row) -> None:
        """Write single TopoJSON record (buffered; emitted as part of Topology on close)."""
        if self._validation_hooks:
            validated = self._apply_validation_hooks(record)
            if validated is None:
                return
            record = validated
        self.write_bulk([record])

    def write_bulk(self, records: list[Row]) -> None:
        """Write bulk TopoJSON records (buffered; single Topology written on close)."""
        if self._validation_hooks:
            validated_records = []
            for record in records:
                validated = self._apply_validation_hooks(record)
                if validated is not None:
                    validated_records.append(validated)
            records = validated_records
        if not records:
            return
        # Buffer geometries; a single valid Topology is written in close()
        if not hasattr(self, "_write_buffer"):
            self._write_buffer = []
        self._write_buffer.extend(records)

    def close(self):
        """Close and write a single valid TopoJSON Topology if write buffer has data."""
        if self.mode in ["w", "wr"] and getattr(self, "_write_buffer", None):
            buf = self._write_buffer
            topo_data = {
                "type": "Topology",
                "objects": {"collection": {"type": "GeometryCollection", "geometries": buf}},
                "arcs": [],
            }
            if self.fobj is not None:
                json.dump(topo_data, self.fobj, ensure_ascii=False)
            self._write_buffer = []
        super().close()
