from __future__ import annotations

import typing

try:
    import shapefile

    HAS_SHAPEFILE = True
except ImportError:
    HAS_SHAPEFILE = False

import codecs
import os
import re
import zipfile
from typing import Any

from ..base import BaseCodec, BaseFileIterable
from ..exceptions import ReadError
from ..types import Row

# pyshp 3 reads the ``.cpg`` file for the DBF encoding; older versions default to UTF-8.
_PYSHP_READS_CPG = HAS_SHAPEFILE and int(str(getattr(shapefile, "__version__", "0")).split(".")[0]) >= 3


def cpg_encoding(text: str) -> str | None:
    """Python codec for the content of a ``.cpg`` file (``UTF-8``, ``1252``, ``ANSI 1251``, ``ISO 8859-1``)."""
    value = text.replace("\x00", "").strip()
    if not value:
        return None
    compact = value.lower().replace(" ", "").replace("_", "-")
    number = re.fullmatch(r"(?:ansi|cp|windows-?|oem|ibm)?(\d{3,5})", compact)
    if number:
        candidate = "utf-8" if number.group(1) == "65001" else f"cp{number.group(1)}"
    else:
        iso = re.fullmatch(r"(?:iso)?-?8859-?(\d{1,2})", compact)
        candidate = f"iso-8859-{iso.group(1)}" if iso else value
    try:
        return codecs.lookup(candidate).name
    except LookupError:
        return None


def shapefiles_in_zip(path: str) -> list[str]:
    """Paths of the ``.shp`` members of a zip archive (empty when it is not a readable zip)."""
    try:
        with zipfile.ZipFile(path) as archive:
            return [name for name in archive.namelist() if name.lower().endswith(".shp")]
    except (OSError, zipfile.BadZipFile):
        return []


def _read_cpg(path: str, member: str | None) -> str | None:
    """Text of the ``.cpg`` next to a ``.shp`` file or archive member, if there is one."""
    if member is not None:
        stem = member[: -len(".shp")]
        with zipfile.ZipFile(path) as archive:
            names = {name.lower(): name for name in archive.namelist()}
            name = names.get(stem.lower() + ".cpg")
            return archive.read(name).decode("ascii", "replace") if name else None
    cpg = path[: -len(".shp")] + ".cpg" if path.lower().endswith(".shp") else None
    if cpg is None or not os.path.exists(cpg):
        return None
    with open(cpg, encoding="ascii", errors="replace") as handle:
        return handle.read()


def _pyshp_decodes_cpg(text: str) -> bool:
    """Whether pyshp >= 3, which reads the ``.cpg`` itself, can use its text as a codec name."""
    if not _PYSHP_READS_CPG:
        return False
    try:
        codecs.lookup(text.lower().replace("-", "_").strip())
    except LookupError:
        return False
    return True


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


def _shape_type_for_geometry(geom_type):
    """Map a GeoJSON geometry type to a shapefile shape type (default POINT)."""
    if geom_type == "LineString":
        return shapefile.POLYLINE
    if geom_type == "Polygon":
        return shapefile.POLYGON
    if geom_type == "MultiPoint":
        return shapefile.MULTIPOINT
    return shapefile.POINT


def _field_defs(properties):
    """Build shapefile field definitions from a properties dict."""
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
    return fields


def _extract_shape_coords(geometry):
    """Convert a GeoJSON-like geometry dict to shapefile coordinates."""
    geom_type = geometry.get("type")
    coords = geometry.get("coordinates", [])

    if geom_type == "Polygon":
        # Polygon coordinates are nested
        if isinstance(coords[0], list) and isinstance(coords[0][0], list):
            return geom_type, coords[0]  # Outer ring
        return geom_type, coords
    if geom_type in ("Point", "LineString", "MultiPoint"):
        return geom_type, coords
    return geom_type, []


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

        # A zipped Shapefile (``x.shp.zip``, or ``x.zip`` holding one ``.shp``) arrives as a zip
        # codec from open_iterable(); pyshp reads the archive from its path.
        codec_path = getattr(codec, "filename", None)
        if filename is None and codec is not None and str(codec_path or "").lower().endswith(".zip"):
            filename, codec = codec_path, None
        self.archive = bool(filename) and str(filename).lower().endswith(".zip")
        # ``member`` picks one ``.shp`` of an archive that holds several.
        self.member = options.get("member")
        # ``encoding`` is the DBF encoding; by default the ``.cpg`` file decides, else UTF-8.
        self.dbf_encoding = options.get("encoding")

        # Shapefile requires .shp extension, but we accept the base filename
        if filename and not self.archive and not filename.endswith(".shp"):
            # Try to find .shp file
            base = filename.rsplit(".", 1)[0]
            shp_file = base + ".shp"
            if os.path.exists(shp_file):
                filename = shp_file
            else:
                filename = shp_file  # Will be created if writing

        super().__init__(filename, stream, codec=codec, mode=mode, binary=True, encoding="utf8", options=options)
        try:
            self.reset()
        except Exception:
            self.close()
            raise

    def _reader_target(self) -> tuple[str, str | None]:
        """Path for ``shapefile.Reader`` and the archive member it reads (None for a plain .shp)."""
        if not self.archive:
            return self.filename, None
        members = shapefiles_in_zip(self.filename)
        if self.member is not None:
            chosen = [m for m in members if m == self.member or os.path.basename(m) == self.member]
        else:
            chosen = members
        if len(chosen) != 1:
            found = ", ".join(members) or "none"
            raise ReadError(
                f"Zip archive must hold exactly one .shp file (or pass member=...); found: {found}",
                filename=self.filename,
                error_code="RESOURCE_REQUIREMENT_NOT_MET",
            )
        member = chosen[0]
        target = self.filename if len(members) == 1 else f"{self.filename}/{member}"
        return target, member

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
            target, member = self._reader_target()
            cpg_text = None if self.dbf_encoding else _read_cpg(self.filename, member)
            cpg = cpg_encoding(cpg_text) if cpg_text else None
            encoding = self.dbf_encoding or cpg or "utf-8"
            kwargs: dict[str, Any] = {"encoding": encoding}
            if cpg_text is not None and _pyshp_decodes_cpg(cpg_text):
                # pyshp >= 3 reads this .cpg itself, and warns when its text (``1252``) differs
                # from a codec name passed in (``cp1252``).
                kwargs = {}
            try:
                self.reader = shapefile.Reader(target, **kwargs)
            except Exception as e:
                raise ReadError(
                    f"Cannot read Shapefile {target}: {e}", filename=self.filename, error_code="READ_FAILED"
                ) from e
            self.encoding = encoding
            self.iterator = self.__iterator()
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

    def _init_writer(self, record: Row) -> None:
        """Initialize the shapefile writer using the first record's schema."""
        # Determine shape type from first record
        geometry = record.get("geometry", {})
        geom_type = geometry.get("type") if geometry else None
        shape_type = _shape_type_for_geometry(geom_type)

        # Get field names from properties
        properties = record.get("properties", {})

        # Create writer
        base_name = self.filename.rsplit(".", 1)[0]
        self.writer = shapefile.Writer(base_name, shapeType=shape_type)

        # Store field names for later use
        self.field_names = list(properties.keys())

        # Add field definitions
        for field in _field_defs(properties):
            self.writer.field(*field)

        self.writer_initialized = True

    def _write_geometry(self, geom_type, shape_coords) -> None:
        """Write the geometry part of a feature to the shapefile writer."""
        if not shape_coords:
            return
        if geom_type == "Point":
            self.writer.point(*shape_coords)
        elif geom_type == "LineString":
            self.writer.line([shape_coords])
        elif geom_type == "Polygon":
            self.writer.poly([shape_coords])
        elif geom_type == "MultiPoint":
            self.writer.multipoint(shape_coords)

    def write(self, record: Row) -> None:
        """Write single shapefile feature"""
        # Apply validation hooks if configured
        if self._validation_hooks:
            validated = self._apply_validation_hooks(record)
            if validated is None:  # Skipped
                return  # Don't write invalid row
            record = validated

        if not HAS_SHAPEFILE:
            raise ImportError("pyshp library is required for Shapefile support")

        # Initialize writer on first write
        if not hasattr(self, "writer_initialized") or not self.writer_initialized:
            self._init_writer(record)

        # Extract geometry and properties
        geometry = record.get("geometry", {})
        properties = record.get("properties", {})

        # Convert geometry to shapefile format and write it
        geom_type, shape_coords = _extract_shape_coords(geometry)
        self._write_geometry(geom_type, shape_coords)

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
