from __future__ import annotations

import typing
from collections import defaultdict
from typing import Any

from ..base import BaseCodec, BaseFileIterable
from ..exceptions import FormatParseError
from ..helpers.xmlsec import safe_iterparse

PREFIX_STRIP = False
PREFIX = ""


def etree_to_dict(t, prefix_strip=True):
    """Converts tree of XML elements from lxml to python dictionary"""
    tag = t.tag if not prefix_strip else t.tag.rsplit("}", 1)[-1]
    d = {tag: {} if t.attrib else None}
    children = list(t)
    if children:
        dd = defaultdict(list)
        for dc in map(etree_to_dict, children):
            #            print(dir(dc))
            for k, v in dc.items():
                if prefix_strip:
                    k = k.rsplit("}", 1)[-1]
                dd[k].append(v)
        d = {tag: {k: v[0] if len(v) == 1 else v for k, v in dd.items()}}
    if t.attrib:
        d[tag].update(("@" + k.rsplit("}", 1)[-1], v) for k, v in t.attrib.items())
    if t.text:
        text = t.text.strip()
        if children or t.attrib:
            tag = tag.rsplit("}", 1)[-1]
            if text:
                d[tag]["#text"] = text
        else:
            d[tag] = text
    return d


class XMLIterable(BaseFileIterable):
    datamode = "binary"

    def __init__(
        self,
        filename: str | None = None,
        stream: typing.IO[Any] | None = None,
        codec: BaseCodec | None = None,
        mode="r",
        tagname: str | None = None,
        prefix_strip: bool = True,
        options: dict[str, Any] | None = None,
    ):
        if options is None:
            options = {}
        super().__init__(filename, stream, codec=codec, mode=mode, binary=True, encoding="utf8", options=options)
        if tagname is not None:
            self.tagname = tagname
        self.prefix_strip = prefix_strip
        self.reset()

    def reset(self):
        super().reset()
        self.reader = safe_iterparse(self.fobj)
        self.pos = 0
        # Track position for error context
        self._current_element_number = 0
        self._current_byte_offset = 0

    @staticmethod
    def id() -> str:
        return "xml"

    @staticmethod
    def is_flatonly() -> bool:
        return False

    @staticmethod
    def has_tables() -> bool:
        """Indicates if this format supports multiple tables/tags."""
        return True

    def is_streaming(self) -> bool:
        """Returns True - XML uses iterparse for streaming"""
        return True

    def list_tables(self, filename: str | None = None) -> list[str] | None:
        """List available tag names in the XML file.

        Can be called as:
        - Instance method: `iterable.list_tables()` - reuses open file if possible
        - With filename: `iterable.list_tables(filename)` - opens file temporarily

        Args:
            filename: Optional filename. If None, uses instance's filename.

        Returns:
            list[str]: List of unique tag names found in the document, or empty list if no elements.
        """
        target_filename = filename if filename is not None else self.filename
        if target_filename is None:
            # Try to use open file if available
            if hasattr(self, "fobj") and self.fobj is not None:
                try:
                    current_pos = self.fobj.tell()
                    self.fobj.seek(0)
                    # Parse to get tag names
                    tag_names = set()
                    for _event, elem in safe_iterparse(self.fobj, events=("start",)):
                        if elem.tag:
                            # Strip namespace if prefix_strip is True
                            shorttag = elem.tag.rsplit("}", 1)[-1]
                            tag_names.add(shorttag)
                    self.fobj.seek(current_pos)
                    return sorted(list(tag_names))
                except (AttributeError, OSError):
                    return None
            return None

        # Parse file to get unique tag names
        tag_names = set()
        try:
            with open(target_filename, "rb") as f:
                for _event, elem in safe_iterparse(f, events=("start",)):
                    if elem.tag:
                        # Strip namespace if prefix_strip is True (default behavior)
                        shorttag = elem.tag.rsplit("}", 1)[-1]
                        tag_names.add(shorttag)
        except Exception:
            return None

        return sorted(list(tag_names)) if tag_names else []

    def read(self, skip_empty: bool = True) -> dict:
        """Read single XML record"""
        row = None
        while not row:
            try:
                # Get byte offset before reading if possible
                if hasattr(self.fobj, "tell"):
                    try:
                        self._current_byte_offset = self.fobj.tell()
                    except (OSError, AttributeError):
                        pass

                event, elem = next(self.reader)
                self._current_element_number += 1
                shorttag = elem.tag.rsplit("}", 1)[-1]
                if shorttag == self.tagname:
                    try:
                        if self.prefix_strip:
                            row = etree_to_dict(elem, self.prefix_strip)
                        else:
                            row = etree_to_dict(elem)
                        # Free memory: clear processed element and prune older siblings.
                        elem.clear()
                        parent = elem.getparent()
                        if parent is not None:
                            while elem.getprevious() is not None:
                                del parent[0]
                    except Exception as e:
                        # Handle parse errors according to error policy
                        error = FormatParseError(
                            format_id="xml",
                            message=str(e),
                            filename=self.filename,
                            row_number=self._current_element_number,
                            byte_offset=self._current_byte_offset if self._current_byte_offset > 0 else None,
                            original_line=None,  # XML is binary, no original line
                        )
                        self._handle_error(
                            error,
                            row_number=self._current_element_number,
                            byte_offset=self._current_byte_offset if self._current_byte_offset > 0 else None,
                            original_line=None,
                        )
                        # If we get here, error was handled (skip/warn), continue to next element
                        continue
            except StopIteration:
                # No more elements to read
                raise
            except Exception as e:
                # Handle XML parsing errors
                error = FormatParseError(
                    format_id="xml",
                    message=str(e),
                    filename=self.filename,
                    row_number=self._current_element_number,
                    byte_offset=self._current_byte_offset if self._current_byte_offset > 0 else None,
                    original_line=None,
                )
                self._handle_error(
                    error,
                    row_number=self._current_element_number,
                    byte_offset=self._current_byte_offset if self._current_byte_offset > 0 else None,
                    original_line=None,
                )
                # If we get here, error was handled (skip/warn), continue to next element
                continue

        self.pos += 1
        return row[self.tagname]
