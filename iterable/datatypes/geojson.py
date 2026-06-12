from __future__ import annotations

import json
import os
import typing

try:
    import geojson

    HAS_GEOJSON = True
except ImportError:
    HAS_GEOJSON = False

try:
    import ijson

    HAS_IJSON = True
except ImportError:
    HAS_IJSON = False

from typing import Any

from ..base import DEFAULT_BULK_NUMBER, BaseCodec, BaseFileIterable
from ..types import Row


class GeoJSONIterable(BaseFileIterable):
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
        pass

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
        if self.mode == "r":
            # Determine if we should use streaming parser
            if self._should_use_streaming():
                # Use streaming parser
                self._streaming = True
                self.fobj.seek(0)
                # Try to stream features from FeatureCollection
                try:
                    # First, try to detect if it's a FeatureCollection
                    # We'll try to stream "features.item" path
                    self._parser = ijson.items(self.fobj, "features.item")
                    # Pre-fetch first item to check if parser works
                    try:
                        self._first_item = next(self._parser)
                        self._items_buffer = [self._first_item]
                    except StopIteration:
                        # Maybe it's a single Feature or different structure
                        # Reset and try as single feature
                        self.fobj.seek(0)
                        try:
                            # Try streaming as single object
                            self._parser = ijson.items(self.fobj, "item")
                            self._first_item = next(self._parser)
                            self._items_buffer = [self._first_item]
                        except StopIteration:
                            self._items_buffer = []
                except Exception:
                    # Fallback to non-streaming
                    self._streaming = False
                    self._parser = None
                    self.fobj.seek(0)
                    # Continue with non-streaming approach below
                    self._streaming = False
            else:
                self._streaming = False

            if not self._streaming:
                # Try to parse as a single JSON document first
                try:
                    # Save current position
                    self.fobj.tell()
                    self.fobj.seek(0)
                    data = json.load(self.fobj)
                    # GeoJSON can be FeatureCollection or single Feature
                    if data.get("type") == "FeatureCollection":
                        self.features = data.get("features", [])
                    elif data.get("type") == "Feature":
                        self.features = [data]
                    else:
                        # Try to find features in the data
                        self.features = data if isinstance(data, list) else []
                    self.iterator = iter(self.features)
                except (json.JSONDecodeError, ValueError):
                    # If single JSON parse fails, try JSONL format (one JSON object per line)
                    self.fobj.seek(0)
                    self.features = []
                    for line in self.fobj:
                        line = line.strip()
                        if line:
                            try:
                                feature = json.loads(line)
                                self.features.append(feature)
                            except json.JSONDecodeError:
                                # Skip invalid JSON lines
                                continue
                    self.iterator = iter(self.features)

    @staticmethod
    def id() -> str:
        return "geojson"

    @staticmethod
    def is_flatonly() -> bool:
        return False

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
        """Read single GeoJSON feature"""
        if self._streaming:
            # Use streaming parser
            if self._items_buffer:
                # Return buffered item
                item = self._items_buffer.pop(0)
                self.pos += 1
                return item
            # Try to get next item from parser
            try:
                item = next(self._parser)
                self.pos += 1
                return item
            except StopIteration:
                raise StopIteration from None
        else:
            # Use loaded data
            feature = next(self.iterator)
            self.pos += 1
            # Return feature as dict (it already is)
            return feature

    def read_bulk(self, num: int = DEFAULT_BULK_NUMBER) -> list[dict]:
        """Read bulk GeoJSON features"""
        chunk = []
        if self._streaming:
            # For streaming, read from buffer first, then parser
            while len(chunk) < num:
                if self._items_buffer:
                    chunk.append(self._items_buffer.pop(0))
                    self.pos += 1
                else:
                    try:
                        item = next(self._parser)
                        chunk.append(item)
                        self.pos += 1
                    except StopIteration:
                        break
        else:
            # For non-streaming, use iterator
            for _n in range(0, num):
                try:
                    chunk.append(self.read())
                except StopIteration:
                    break
        return chunk

    def is_streaming(self) -> bool:
        """Returns True if using streaming parser"""
        return self._streaming

    def write(self, record: Row) -> None:
        """Write single GeoJSON feature"""
        # Ensure it's a valid GeoJSON feature
        if "type" not in record:
            record["type"] = "Feature"
        if HAS_GEOJSON:
            feature = geojson.Feature(**record)
            geojson.dump(feature, self.fobj, ensure_ascii=False)
        else:
            json.dump(record, self.fobj, ensure_ascii=False)
        self.fobj.write("\n")

    def write_bulk(self, records: list[Row]) -> None:
        """Write bulk GeoJSON features"""
        # Write as FeatureCollection
        if HAS_GEOJSON:
            features = [geojson.Feature(**r) for r in records]
            fc = geojson.FeatureCollection(features)
            geojson.dump(fc, self.fobj, ensure_ascii=False)
        else:
            fc = {"type": "FeatureCollection", "features": records}
            json.dump(fc, self.fobj, ensure_ascii=False)
