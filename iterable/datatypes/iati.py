"""IATI activity XML reader.

Streams ``iati-activity`` elements via lxml ``iterparse`` and yields simplified
dicts with ``iati-identifier``, ``title``, attributes, and flattened children.

Requires lxml (``pip install iterabledata[xml]``).

Read-only. Format id: ``iati``.
"""

from __future__ import annotations

import typing
from typing import Any

from ..base import BaseCodec, BaseFileIterable
from ..exceptions import WriteNotSupportedError
from ..helpers.xmlsec import safe_iterparse
from ..types import Row

try:
    from lxml import etree  # noqa: F401

    HAS_LXML = True
except ImportError:
    HAS_LXML = False

_IMPORT_ERROR = "IATI support requires 'lxml'. Install with: pip install iterabledata[xml]"


def _local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1] if tag else tag


def _text_of(elem: Any) -> str | None:
    if elem is None:
        return None
    # Prefer narrative child text when present (IATI v2).
    for child in elem:
        if _local(child.tag) == "narrative" and (child.text or "").strip():
            return (child.text or "").strip()
    text = (elem.text or "").strip()
    return text or None


def _activity_to_dict(elem: Any) -> dict[str, Any]:
    record: dict[str, Any] = {}
    # Attributes on iati-activity
    for k, v in elem.attrib.items():
        record[f"@{_local(k)}"] = v

    identifier = None
    title = None
    children: dict[str, Any] = {}

    for child in elem:
        name = _local(child.tag)
        if name == "iati-identifier":
            identifier = (child.text or "").strip() or None
        elif name == "title":
            title = _text_of(child)
        else:
            value: Any
            if len(child) == 0 and not child.attrib:
                value = (child.text or "").strip() or None
            else:
                value = {}
                for ak, av in child.attrib.items():
                    value[f"@{_local(ak)}"] = av
                text = _text_of(child)
                if text is not None:
                    value["#text"] = text
                # Collect simple nested narratives / texts
                nested: dict[str, Any] = {}
                for sub in child:
                    sn = _local(sub.tag)
                    st = _text_of(sub)
                    if st is None and not sub.attrib:
                        continue
                    entry: Any = st
                    if sub.attrib:
                        entry = {f"@{_local(ak)}": av for ak, av in sub.attrib.items()}
                        if st is not None:
                            entry["#text"] = st
                    if sn in nested:
                        if not isinstance(nested[sn], list):
                            nested[sn] = [nested[sn]]
                        nested[sn].append(entry)
                    else:
                        nested[sn] = entry
                if nested:
                    value.update(nested)
            if name in children:
                if not isinstance(children[name], list):
                    children[name] = [children[name]]
                children[name].append(value)
            else:
                children[name] = value

    record["iati-identifier"] = identifier
    record["title"] = title
    record.update(children)
    return record


class IATIIterable(BaseFileIterable):
    """Read-only IATI activity XML iterable."""

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
        if not HAS_LXML:
            raise ImportError(_IMPORT_ERROR)
        if mode not in ("r", "rb"):
            raise WriteNotSupportedError("iati", "IATI is read-only")
        self._tag = options.pop("tagname", "iati-activity")
        super().__init__(
            filename=filename,
            stream=stream,
            codec=codec,
            binary=True,
            mode="r",
            encoding="utf8",
            options=options,
        )
        self.reset()

    def reset(self) -> None:
        super().reset()
        self.pos = 0
        self._parser = safe_iterparse(self.fobj, events=("end",))

    @staticmethod
    def id() -> str:
        return "iati"

    @staticmethod
    def is_flatonly() -> bool:
        return False

    def is_streaming(self) -> bool:
        return True

    def read(self, skip_empty: bool = True) -> Row:
        while True:
            _event, elem = next(self._parser)
            if _local(elem.tag) != self._tag:
                # Do not clear unmatched elements — that would wipe child text
                # before the parent iati-activity end event is reached.
                continue
            record = _activity_to_dict(elem)
            # Free memory after the activity is fully built.
            elem.clear()
            parent = elem.getparent()
            if parent is not None:
                while elem.getprevious() is not None:
                    del parent[0]
            self.pos += 1
            return record

    def write(self, record: Row) -> None:
        raise WriteNotSupportedError("iati", "IATI is read-only")

    def write_bulk(self, records: list[Row]) -> None:
        raise WriteNotSupportedError("iati", "IATI is read-only")
