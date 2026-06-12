"""KMZ (KML Zipped) format support: read KML from a ZIP archive."""

from __future__ import annotations

import io
import typing
import zipfile
from typing import Any

from ..base import BaseFileIterable
from ..types import Row

try:
    import lxml.etree as etree
except ImportError as e:
    raise ImportError("KMZ support requires lxml. Install with: pip install iterabledata[xml]") from e

from .kml import kml_to_geojson


def _find_kml_in_zip(zf: zipfile.ZipFile) -> str:
    """Return the name of the root KML entry (doc.kml or first .kml)."""
    candidates = []
    for name in zf.namelist():
        if name.lower().endswith(".kml"):
            if name.lower() in ("doc.kml", "kml.kml"):
                return name
            candidates.append(name)
    if candidates:
        return candidates[0]
    raise ValueError("No KML document found in KMZ archive")


class KMZIterable(BaseFileIterable):
    """Read KMZ (ZIP containing KML) files; yields GeoJSON-like features per Placemark."""

    datamode = "binary"

    def __init__(
        self,
        filename: str | None = None,
        stream: typing.IO[Any] | None = None,
        codec=None,
        mode: str = "r",
        options: dict[str, Any] | None = None,
    ):
        if options is None:
            options = {}
        if mode != "r":
            raise ValueError("KMZ format supports read-only mode")
        if mode == "r" and filename is None and stream is not None:
            # Support stream: read into bytes and open as ZIP
            try:
                data = stream.read()
                self._kmz_bytes = data
                self._use_stream = True
            except Exception:
                self._kmz_bytes = None
                self._use_stream = False
        else:
            self._kmz_bytes = None
            self._use_stream = False
        super().__init__(
            filename=filename,
            stream=stream,
            codec=codec,
            mode=mode,
            binary=True,
            encoding="utf8",
            options=options,
        )
        self.reset()

    def reset(self) -> None:
        super().reset()
        self.features: list[Row] = []
        self.pos = 0

        if self.mode != "r":
            self.iterator = iter(self.features)
            return

        if self._use_stream and getattr(self, "_kmz_bytes", None):
            zip_src: str | io.BytesIO = io.BytesIO(self._kmz_bytes)
        elif self.filename:
            zip_src = self.filename
        else:
            self.iterator = iter(self.features)
            return

        try:
            with zipfile.ZipFile(zip_src, "r") as zf:
                kml_name = _find_kml_in_zip(zf)
                with zf.open(kml_name) as kml_file:
                    kml_bytes = kml_file.read()
        except zipfile.BadZipFile as e:
            src = self.filename or "stream"
            raise ValueError(f"Invalid KMZ file (not a valid ZIP): {src}") from e

        if not kml_bytes:
            self.iterator = iter(self.features)
            return

        buf = io.BytesIO(kml_bytes)
        tree = etree.parse(buf)
        root = tree.getroot()
        ns = {"kml": "http://www.opengis.net/kml/2.2"}
        placemarks = root.findall(".//kml:Placemark", ns)
        if not placemarks:
            placemarks = root.findall(".//Placemark")

        for placemark in placemarks:
            feature = kml_to_geojson(placemark)
            if feature.get("geometry") is not None:
                self.features.append(feature)

        self.iterator = iter(self.features)

    @staticmethod
    def id() -> str:
        return "kmz"

    @staticmethod
    def is_flatonly() -> bool:
        return False

    @staticmethod
    def has_totals() -> bool:
        return True

    def totals(self) -> int:
        if hasattr(self, "features"):
            return len(self.features)
        return 0

    def read(self, skip_empty: bool = True) -> Row:
        return next(self.iterator)
