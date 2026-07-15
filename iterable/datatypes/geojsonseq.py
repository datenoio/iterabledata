"""GeoJSON Text Sequences (RFC 8142).

One GeoJSON Feature object per line, optionally prefixed with the ASCII
record-separator control character ``\\x1e``. This is the streaming-friendly
counterpart to the ``geojson`` format: reading and writing handle one feature
at a time, so memory use is bounded by a single feature.
"""

from __future__ import annotations

from json import loads

from ..base import DEFAULT_BULK_NUMBER
from ..exceptions import FormatParseError
from .jsonl import JSONLinesIterable

# RFC 8142 record separator that may precede each JSON text.
RECORD_SEPARATOR = "\x1e"


class GeoJSONSeqIterable(JSONLinesIterable):
    """GeoJSON Text Sequence reader/writer (one Feature per line)."""

    @staticmethod
    def id() -> str:
        return "geojsonseq"

    def read(self, skip_empty: bool = True) -> dict:
        """Read a single GeoJSON feature from the sequence."""
        while True:
            line = next(self.fobj)
            self._current_line_number += 1
            line = line.lstrip(RECORD_SEPARATOR)
            if skip_empty and not line.strip():
                continue
            original_line = line.rstrip("\n\r")
            try:
                result = loads(line)
            except (ValueError, TypeError) as e:
                error = FormatParseError(
                    format_id="geojsonseq",
                    message=str(e),
                    filename=self.filename,
                    row_number=self._current_line_number,
                    original_line=original_line,
                )
                self._handle_error(error, row_number=self._current_line_number, original_line=original_line)
                continue
            self.pos += 1
            return result

    def read_bulk(self, num: int = DEFAULT_BULK_NUMBER) -> list[dict]:
        """Read a bulk of GeoJSON features from the sequence."""
        chunk: list[dict] = []
        while len(chunk) < num:
            line = self.fobj.readline()
            if not line:
                break
            self._current_line_number += 1
            line = line.lstrip(RECORD_SEPARATOR).strip()
            if not line:
                continue
            try:
                chunk.append(loads(line))
                self.pos += 1
            except (ValueError, TypeError) as e:
                error = FormatParseError(
                    format_id="geojsonseq",
                    message=str(e),
                    filename=self.filename,
                    row_number=self._current_line_number,
                    original_line=line,
                )
                self._handle_error(error, row_number=self._current_line_number, original_line=line)
                continue
        return chunk

    # write()/write_bulk() are inherited from JSONLinesIterable: features are
    # serialized as one JSON object per line, which is valid RFC 8142 output
    # (the record separator is optional for parsers that tolerate plain lines).
