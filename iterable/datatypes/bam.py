"""BAM (Binary SAM) format support using pysam."""

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

# Reuse segment-to-dict from sam module to avoid duplication
from .sam import _segment_to_dict


class BAMIterable(BaseFileIterable):
    """BAM format: yields one dict per alignment (query_name, reference_*, cigar, etc.)."""

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
                "BAM support requires 'pysam'. Install with: pip install iterabledata[alignment]"
            ) from None
        if filename is None and stream is None:
            raise ValueError("BAM format requires a filename (stream not supported)")
        super().__init__(
            filename,
            stream,
            codec=codec,
            mode=mode,
            binary=True,
            noopen=True,
            options=options,
        )
        self._aln_file = None
        self._iterator = None
        self.pos = 0
        self.reset()

    def reset(self) -> None:
        """Reopen BAM file and rewind."""
        super().reset()
        self.pos = 0
        if self.mode == "r" and self.filename is not None:
            self._aln_file = pysam.AlignmentFile(self.filename, "rb")
            self._iterator = iter(self._aln_file)
        else:
            self._iterator = iter([])

    @staticmethod
    def id() -> str:
        return "bam"

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
