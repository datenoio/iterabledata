from __future__ import annotations

import typing

try:
    from icalendar import Calendar, Event

    HAS_ICALENDAR = True
except ImportError:
    try:
        import ics

        HAS_ICS = True
        HAS_ICALENDAR = False
    except ImportError:
        HAS_ICS = False
        HAS_ICALENDAR = False

from typing import Any

from ..base import BaseCodec, BaseFileIterable
from ..types import Row

_ICALENDAR_KEY_MAP = {
    "dtstart": "dtstart",
    "start": "dtstart",
    "dtend": "dtend",
    "end": "dtend",
    "summary": "summary",
    "name": "summary",
    "description": "description",
    "location": "location",
    "uid": "uid",
}


def _record_to_icalendar_event(record: Row):
    """Build an icalendar.Event from a record dict."""
    event = Event()
    for key, value in record.items():
        prop = _ICALENDAR_KEY_MAP.get(key.lower(), key.upper())
        event.add(prop, value)
    return event


def _parse_ics_datetime(dt_str: str):
    """Parse an ISO datetime string for the ics library."""
    from datetime import datetime

    return datetime.fromisoformat(dt_str.replace("Z", "+00:00"))


def _record_to_ics_event(record: Row):
    """Build an ics.Event from a record dict."""
    event = ics.Event()
    if "name" in record or "summary" in record:
        event.name = record.get("name") or record.get("summary")
    if "begin" in record or "dtstart" in record or "start" in record:
        dt_str = record.get("begin") or record.get("dtstart") or record.get("start")
        event.begin = _parse_ics_datetime(dt_str)
    if "end" in record or "dtend" in record:
        dt_str = record.get("end") or record.get("dtend")
        event.end = _parse_ics_datetime(dt_str)
    if "description" in record:
        event.description = record["description"]
    if "location" in record:
        event.location = record["location"]
    return event


class ICALIterable(BaseFileIterable):
    def __init__(
        self,
        filename: str | None = None,
        stream: typing.IO[Any] | None = None,
        codec: BaseCodec | None = None,
        mode: str = "r",
        encoding: str = "utf8",
        options: dict[str, Any] | None = None,
    ):
        if options is None:
            options = {}
        if not HAS_ICALENDAR and not HAS_ICS:
            raise ImportError("iCal support requires 'icalendar' or 'ics' package")
        super().__init__(filename, stream, codec=codec, binary=False, mode=mode, encoding=encoding, options=options)
        self.reset()
        pass

    def reset(self):
        """Reset iterable"""
        super().reset()
        self.pos = 0
        if self.mode == "r":
            content = self.fobj.read()

            if HAS_ICALENDAR:
                # icalendar library
                cal = Calendar.from_ical(content)
                self.entries = []
                for component in cal.walk():
                    if component.name == "VEVENT":
                        entry = {}
                        for prop in component.property_items():
                            key = prop[0].lower()
                            value = prop[1]
                            if hasattr(value, "dt"):
                                value = value.dt.isoformat() if hasattr(value.dt, "isoformat") else str(value.dt)
                            else:
                                value = str(value)

                            if key in entry:
                                if not isinstance(entry[key], list):
                                    entry[key] = [entry[key]]
                                entry[key].append(value)
                            else:
                                entry[key] = value
                        self.entries.append(entry)
            else:
                # ics library
                cal = ics.Calendar(content)
                self.entries = []
                for event in cal.events:
                    entry = {
                        "uid": str(event.uid) if event.uid else None,
                        "name": str(event.name) if event.name else None,
                        "begin": event.begin.isoformat() if event.begin else None,
                        "end": event.end.isoformat() if event.end else None,
                        "description": str(event.description) if event.description else None,
                        "location": str(event.location) if event.location else None,
                        "url": str(event.url) if event.url else None,
                    }
                    # Remove None values
                    entry = {k: v for k, v in entry.items() if v is not None}
                    self.entries.append(entry)

            self.iterator = iter(self.entries)
        else:
            self.entries = []

    @staticmethod
    def id() -> str:
        return "ical"

    @staticmethod
    def is_flatonly() -> bool:
        return False

    def read(self, skip_empty: bool = True) -> dict:
        """Read single iCal record"""
        row = next(self.iterator)
        self.pos += 1
        return row

    def write(self, record: Row) -> None:
        """Write single iCal record"""
        if HAS_ICALENDAR:
            cal = Calendar()
            cal.add_component(_record_to_icalendar_event(record))
            self.fobj.write(cal.to_ical().decode("utf-8"))
        else:
            # ics library
            cal = ics.Calendar()
            cal.events.add(_record_to_ics_event(record))
            self.fobj.write(str(cal))

    def write_bulk(self, records: list[Row]) -> None:
        """Write bulk iCal records"""
        if HAS_ICALENDAR:
            cal = Calendar()
            for record in records:
                cal.add_component(_record_to_icalendar_event(record))
            self.fobj.write(cal.to_ical().decode("utf-8"))
        else:
            cal = ics.Calendar()
            for record in records:
                cal.events.add(_record_to_ics_event(record))
            self.fobj.write(str(cal))
