"""CRAM alignment support using pysam with explicit reference configuration."""

from __future__ import annotations

import typing

try:
    import pysam
except ImportError:
    pysam = None

from ..base import BaseCodec, BaseFileIterable
from ..types import Row
from .sam import _segment_to_dict


class CRAMIterable(BaseFileIterable):
    datamode = "binary"

    def __init__(
        self,
        filename: str | None = None,
        stream: typing.IO[typing.Any] | None = None,
        codec: BaseCodec | None = None,
        mode: str = "r",
        reference_filename: str | None = None,
        options: dict[str, typing.Any] | None = None,
    ):
        if pysam is None:
            raise ImportError("CRAM support requires pysam. Install with: pip install iterabledata[alignment]")
        if filename is None:
            raise ValueError("CRAM format requires a filename")
        self.reference_filename = reference_filename
        self._aln_file = None
        self._iterator = iter(())
        super().__init__(filename, stream, codec=codec, mode=mode, binary=True, noopen=True, options=options or {})
        self.reset()

    @staticmethod
    def id() -> str:
        return "cram"

    @staticmethod
    def is_flatonly() -> bool:
        return True

    def reset(self) -> None:
        super().reset()
        self.pos = 0
        if self._aln_file is not None:
            self._aln_file.close()
        if self.mode == "r":
            try:
                kwargs = {"reference_filename": self.reference_filename} if self.reference_filename else {}
                self._aln_file = pysam.AlignmentFile(self.filename, "rc", **kwargs)
                self._iterator = iter(self._aln_file)
            except (OSError, ValueError) as exc:
                raise ValueError(f"Unable to open CRAM; provide reference_filename when required: {exc}") from exc

    def read(self, skip_empty: bool = True) -> Row:
        try:
            row = _segment_to_dict(next(self._iterator))
        except (StopIteration, EOFError, ValueError):
            raise StopIteration from None
        self.pos += 1
        return row

    def read_bulk(self, num: int = 100) -> list[Row]:
        rows: list[Row] = []
        for _ in range(num):
            try:
                rows.append(self.read())
            except StopIteration:
                break
        return rows

    def close(self) -> None:
        if self._aln_file is not None:
            self._aln_file.close()
            self._aln_file = None
        super().close()
