"""EDI (X12 / EDIFACT) segment reader.

Pure-Python, read-only parser for common interchange conventions. Detects the
segment terminator (``~`` or newline) and element separator (``*`` or ``+``)
from the document prefix, then yields one dict per segment::

    {"segment_id": "ISA", "elements": ["00", "          ", ...]}

This is a pragmatic subset suitable for streaming inspection — not a full EDI
mapping / HIPAA validation suite.
"""

from __future__ import annotations

import typing
from typing import Any

from ..base import BaseCodec, BaseFileIterable
from ..exceptions import FormatParseError, WriteNotSupportedError
from ..types import Row


def _detect_separators(sample: str) -> tuple[str, str]:
    """Detect (segment_terminator, element_separator) from a document prefix."""
    sample = sample.lstrip("\ufeff")
    if not sample:
        raise FormatParseError("edi", "Empty EDI document")

    # X12 ISA: element separator is character at index 3; segment terminator
    # usually follows the fixed-width ISA segment (after ~106 chars) or is '~'.
    if sample.upper().startswith("ISA") and len(sample) > 3:
        element_sep = sample[3]
        # Prefer '~' if present early; else newline-terminated dialects.
        tilde = sample.find("~", 0, 512)
        if tilde != -1:
            return "~", element_sep
        if "\n" in sample[:512] or "\r" in sample[:512]:
            return "\n", element_sep
        return "~", element_sep

    # EDIFACT UNA service string advice: UNA:+.? '
    if sample.upper().startswith("UNA") and len(sample) >= 9:
        element_sep = sample[4]
        segment_term = sample[8]
        return segment_term, element_sep

    # Heuristics for other EDIFACT / generic text EDI.
    for candidate in ("*", "+"):
        if candidate in sample[:200]:
            element_sep = candidate
            break
    else:
        element_sep = "*"

    if "~" in sample[:512]:
        return "~", element_sep
    if "\n" in sample or "\r" in sample:
        return "\n", element_sep
    return "~", element_sep


def _split_segments(text: str, segment_term: str) -> list[str]:
    if segment_term == "\n":
        # Treat CRLF / CR / LF uniformly.
        text = text.replace("\r\n", "\n").replace("\r", "\n")
        parts = text.split("\n")
    else:
        parts = text.split(segment_term)
    return [p.strip("\r\n") for p in parts if p.strip("\r\n")]


class EDIIterable(BaseFileIterable):
    """Read-only EDI segment iterable (X12 / EDIFACT pragmatic subset)."""

    datamode = "text"

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
        if mode not in ("r", "rb"):
            raise WriteNotSupportedError("edi", "EDI is read-only")
        self._segment_term: str | None = options.pop("segment_terminator", None)
        self._element_sep: str | None = options.pop("element_separator", None)
        super().__init__(
            filename=filename,
            stream=stream,
            codec=codec,
            binary=False,
            mode="r",
            encoding=encoding,
            options=options,
        )
        self.reset()

    def reset(self) -> None:
        super().reset()
        self.pos = 0
        text = self.fobj.read()
        if isinstance(text, bytes):
            text = text.decode(self.encoding, errors="replace")
        if not text.strip():
            self._segments: list[dict[str, Any]] = []
            self._iterator = iter(self._segments)
            return

        if self._segment_term is None or self._element_sep is None:
            segment_term, element_sep = _detect_separators(text)
        else:
            segment_term, element_sep = self._segment_term, self._element_sep
        self._segment_term = segment_term
        self._element_sep = element_sep

        raw_segments = _split_segments(text, segment_term)
        parsed: list[dict[str, Any]] = []
        for raw in raw_segments:
            if not raw.strip():
                continue
            # Strip EDIFACT optional trailing "'" already handled by split;
            # also strip trailing whitespace.
            body = raw.strip()
            if not body:
                continue
            parts = body.split(element_sep)
            segment_id = parts[0].strip()
            if not segment_id:
                continue
            elements = [p for p in parts[1:]]
            parsed.append({"segment_id": segment_id, "elements": elements})
        self._segments = parsed
        self._iterator = iter(self._segments)

    @staticmethod
    def id() -> str:
        return "edi"

    @staticmethod
    def is_flatonly() -> bool:
        return True

    def is_streaming(self) -> bool:
        return False

    def read(self, skip_empty: bool = True) -> Row:
        row = next(self._iterator)
        self.pos += 1
        return row

    def write(self, record: Row) -> None:
        raise WriteNotSupportedError("edi", "EDI is read-only")

    def write_bulk(self, records: list[Row]) -> None:
        raise WriteNotSupportedError("edi", "EDI is read-only")
