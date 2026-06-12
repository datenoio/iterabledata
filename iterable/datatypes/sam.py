"""SAM (Sequence Alignment/Map) format support using pysam."""

from __future__ import annotations

import typing

try:
    import pysam

    HAS_PYSAM = True
except ImportError:
    pysam = None  # type: ignore[misc, assignment]
    HAS_PYSAM = False

from ..base import BaseCodec, BaseFileIterable
from ..types import Row


def _segment_to_dict(seg) -> Row:
    """Convert pysam AlignedSegment to dict of common fields."""
    qual = seg.query_qualities
    qual_str = "".join(chr(q + 33) for q in qual) if qual is not None else ""
    return {
        "query_name": seg.query_name,
        "flag": seg.flag,
        "reference_id": seg.reference_id,
        "reference_start": seg.reference_start,
        "mapping_quality": seg.mapping_quality,
        "cigarstring": seg.cigarstring,
        "next_reference_id": seg.next_reference_id,
        "next_reference_start": seg.next_reference_start,
        "template_length": seg.template_length,
        "query_sequence": seg.query_sequence,
        "query_qualities": qual_str,
    }


class SAMIterable(BaseFileIterable):
    """SAM format: yields one dict per alignment (query_name, reference_*, cigar, etc.)."""

    datamode = "binary"

    def __init__(
        self,
        filename: str | None = None,
        stream: typing.IO[typing.Any] | None = None,
        codec: BaseCodec | None = None,
        mode: str = "r",
        options: dict[str, typing.Any] | None = None,
    ):
        if options is None:
            options = {}
        if not HAS_PYSAM:
            raise ImportError(
                "SAM support requires 'pysam'. Install with: pip install iterabledata[alignment]"
            ) from None
        if filename is None and stream is None:
            raise ValueError("SAM format requires a filename (stream not supported)")
        super().__init__(
            filename,
            stream,
            codec=codec,
            mode=mode,
            binary=False,
            noopen=True,
            options=options,
        )
        self._aln_file = None
        self._iterator = None
        self.pos = 0
        self.reset()

    def reset(self) -> None:
        """Reopen SAM file and rewind."""
        super().reset()
        self.pos = 0
        if self.mode == "r" and self.filename is not None:
            self._aln_file = pysam.AlignmentFile(self.filename, "r")
            self._iterator = iter(self._aln_file)
        else:
            self._iterator = iter([])

    @staticmethod
    def id() -> str:
        return "sam"

    @staticmethod
    def is_flatonly() -> bool:
        return True

    def read(self, skip_empty: bool = True) -> Row:
        """Read single alignment record."""
        try:
            seg = next(self._iterator)
            self.pos += 1
            return _segment_to_dict(seg)
        except (StopIteration, EOFError, ValueError):
            raise StopIteration from None

    def close(self) -> None:
        """Close alignment file."""
        if self._aln_file is not None:
            try:
                self._aln_file.close()
            except Exception:
                pass
            self._aln_file = None
        super().close()
