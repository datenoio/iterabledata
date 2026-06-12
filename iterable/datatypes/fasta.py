"""FASTA sequence format support (stdlib-only)."""

from __future__ import annotations

import typing

from ..base import BaseCodec, BaseFileIterable
from ..types import Row


class FASTAIterable(BaseFileIterable):
    """FASTA format: yields one record per sequence with id, description, sequence."""

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
        """Reset and (re)build sequence iterator."""
        super().reset()
        self.pos = 0
        if self.mode != "r":
            self._iterator = iter([])
            return
        self._iterator = self._yield_sequences()

    def _yield_sequences(self) -> typing.Iterator[Row]:
        """Yield one dict per FASTA sequence (id, description, sequence)."""
        if self.fobj is not None:
            if hasattr(self.fobj, "seek"):
                self.fobj.seek(0)
            for rec in self._parse_fasta_lines(self.fobj):
                yield rec
        elif self.filename is not None:
            with open(self.filename, encoding=self.encoding) as f:
                for rec in self._parse_fasta_lines(f):
                    yield rec

    def _parse_fasta_lines(self, lines: typing.Iterable[str]) -> typing.Iterator[Row]:
        """Parse FASTA lines into (id, description, sequence) records."""
        current_id = None
        current_desc = None
        current_seq: list[str] = []
        for line in lines:
            line = line.rstrip("\r\n")
            if not line:
                continue
            if line.startswith(">"):
                if current_id is not None:
                    yield {
                        "id": current_id,
                        "description": current_desc or "",
                        "sequence": "".join(current_seq),
                    }
                parts = line[1:].split(None, 1)
                current_id = parts[0] if parts else ""
                current_desc = parts[1] if len(parts) > 1 else ""
                current_seq = []
            else:
                current_seq.append(line)
        if current_id is not None:
            yield {
                "id": current_id,
                "description": current_desc or "",
                "sequence": "".join(current_seq),
            }

    @staticmethod
    def id() -> str:
        return "fasta"

    @staticmethod
    def is_flatonly() -> bool:
        return True

    def read(self, skip_empty: bool = True) -> Row:
        """Read single FASTA record."""
        try:
            row = next(self._iterator)
            self.pos += 1
            return row
        except (StopIteration, EOFError, ValueError):
            raise StopIteration from None
