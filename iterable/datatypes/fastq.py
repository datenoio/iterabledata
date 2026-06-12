"""FASTQ sequence format support (stdlib-only)."""

from __future__ import annotations

import typing

from ..base import BaseCodec, BaseFileIterable
from ..types import Row


class FASTQIterable(BaseFileIterable):
    """FASTQ format: yields one record per read with id, sequence, quality, optional description."""

    datamode = "text"

    def __init__(
        self,
        filename: str | None = None,
        stream: typing.IO[typing.Any] | None = None,
        codec: BaseCodec | None = None,
        mode: str = "r",
        encoding: str = "utf-8",
        options: dict[str, typing.Any] | None = None,
    ):
        if options is None:
            options = {}
        super().__init__(
            filename,
            stream,
            codec=codec,
            binary=False,
            mode=mode,
            encoding=encoding,
            options=options,
        )
        self._iterator = None
        self.pos = 0
        self.reset()

    def reset(self) -> None:
        """Reset and (re)build read iterator."""
        super().reset()
        self.pos = 0
        if self.mode != "r":
            self._iterator = iter([])
            return
        self._iterator = self._yield_reads()

    def _yield_reads(self) -> typing.Iterator[Row]:
        """Yield one dict per FASTQ read (id, sequence, quality, description)."""
        if self.fobj is not None:
            if hasattr(self.fobj, "seek"):
                self.fobj.seek(0)
            for rec in self._parse_fastq_lines(self.fobj):
                yield rec
        elif self.filename is not None:
            with open(self.filename, encoding=self.encoding) as f:
                for rec in self._parse_fastq_lines(f):
                    yield rec

    def _parse_fastq_lines(self, lines: typing.Iterable[str]) -> typing.Iterator[Row]:
        """Parse FASTQ four-line blocks into records."""
        line_iter = iter(lines)
        while True:
            try:
                id_line = next(line_iter)
            except StopIteration:
                break
            id_line = id_line.rstrip("\r\n")
            if not id_line or not id_line.startswith("@"):
                continue
            parts = id_line[1:].split(None, 1)
            rec_id = parts[0] if parts else ""
            description = parts[1] if len(parts) > 1 else ""
            try:
                sequence = next(line_iter).rstrip("\r\n")
                next(line_iter)  # plus line
                quality = next(line_iter).rstrip("\r\n")
            except StopIteration:
                break
            yield {
                "id": rec_id,
                "description": description,
                "sequence": sequence,
                "quality": quality,
            }

    @staticmethod
    def id() -> str:
        return "fastq"

    @staticmethod
    def is_flatonly() -> bool:
        return True

    def read(self, skip_empty: bool = True) -> Row:
        """Read single FASTQ record."""
        try:
            row = next(self._iterator)
            self.pos += 1
            return row
        except (StopIteration, EOFError, ValueError):
            raise StopIteration from None
