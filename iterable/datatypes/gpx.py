"""GPX (GPS Exchange Format) 1.0/1.1 support: waypoints, route points, track points."""

from __future__ import annotations

import typing
from typing import Any

from ..base import BaseFileIterable
from ..helpers.xmlsec import safe_parse
from ..types import Row

try:
    import lxml.etree as etree  # noqa: F401 - dependency availability probe
except ImportError as e:
    raise ImportError("GPX support requires lxml. Install with: pip install iterabledata[xml]") from e


def _tag_local(elem) -> str:
    """Return local name (no namespace)."""
    if elem is None:
        return ""
    if callable(getattr(elem, "tag", None)):
        tag = elem.tag
    else:
        tag = getattr(elem, "tag", "")
    if isinstance(tag, str) and "}" in tag:
        return tag.rsplit("}", 1)[-1]
    return tag


def _text(elem) -> str | None:
    """Return trimmed text of element or None."""
    if elem is None:
        return None
    t = elem.text
    return t.strip() if t else None


def _point_to_record(elem, point_type: str) -> Row | None:
    """Build a record from a wpt, rtept, or trkpt element."""
    lat = elem.get("lat")
    lon = elem.get("lon")
    if lat is None or lon is None:
        return None
    try:
        lat_f = float(lat)
        lon_f = float(lon)
    except (TypeError, ValueError):
        return None

    rec: Row = {
        "lat": lat_f,
        "lon": lon_f,
        "point_type": point_type,
    }

    for child in elem:
        local = _tag_local(child)
        if local == "ele":
            t = _text(child)
            if t is not None:
                try:
                    rec["ele"] = float(t)
                except ValueError:
                    rec["ele"] = t
        elif local == "time":
            rec["time"] = _text(child) or ""
        elif local == "name":
            rec["name"] = _text(child) or ""
        elif local == "desc":
            rec["description"] = _text(child) or ""
        elif local == "type":
            rec["type"] = _text(child) or ""
        elif local in ("cmt", "src", "sym", "fix", "sat", "hdop", "vdop", "pdop", "ageofdgpsdata", "dgpsid"):
            rec[local] = _text(child) or ""

    return rec


def _collect_points(root) -> list[Row]:
    """Collect all wpt, rtept, trkpt from GPX root into a list of records (namespace-agnostic)."""
    records: list[Row] = []
    point_types = (("wpt", "waypoint"), ("rtept", "route"), ("trkpt", "track"))
    for elem in root.iter():
        local = _tag_local(elem)
        for tag, ptype in point_types:
            if local == tag:
                r = _point_to_record(elem, ptype)
                if r is not None:
                    records.append(r)
                break
    return records


class GPXIterable(BaseFileIterable):
    """Read GPX 1.0/1.1 files; yields records for waypoints, route points, and track points."""

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
            raise ValueError("GPX format supports read-only mode")
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
        self.records: list[Row] = []
        self.pos = 0

        if self.mode != "r":
            self.iterator = iter(self.records)
            return

        try:
            if self.fobj is not None and getattr(self.fobj, "seekable", lambda: False)():
                self.fobj.seek(0)
            tree = safe_parse(self.fobj)
            root = tree.getroot()
            self.records = _collect_points(root)
        except Exception:
            self.records = []
        self.iterator = iter(self.records)

    @staticmethod
    def id() -> str:
        return "gpx"

    @staticmethod
    def is_flatonly() -> bool:
        return False

    @staticmethod
    def has_totals() -> bool:
        return True

    def totals(self) -> int:
        if hasattr(self, "records"):
            return len(self.records)
        return 0

    def read(self, skip_empty: bool = True) -> Row:
        return next(self.iterator)
