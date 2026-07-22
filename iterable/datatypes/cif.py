"""CIF crystallographic/chemical format subset (stdlib-only, read-only)."""

from __future__ import annotations

import typing
from typing import Any

from ..base import BaseCodec, BaseFileIterable
from ..exceptions import WriteNotSupportedError
from ..types import Row

_ATOM_SITE_PREFIX = "_atom_site."


class CIFIterable(BaseFileIterable):
    """Minimal CIF reader focused on ``loop_`` / ``_atom_site.*`` columns.

    Yields one dict per data row with column names stripped of the
    ``_atom_site.`` prefix. Raises ``ValueError`` when no such loop exists.
    """

    datamode = "text"

    def __init__(
        self,
        filename: str | None = None,
        stream: typing.IO[Any] | None = None,
        codec: BaseCodec | None = None,
        mode: str = "r",
        encoding: str = "utf-8",
        options: dict[str, Any] | None = None,
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
        self._iterator: typing.Iterator[Row] | None = None
        self.pos = 0
        self.reset()

    def reset(self) -> None:
        """Reset and parse atom_site loop."""
        super().reset()
        self.pos = 0
        if self.mode != "r":
            raise WriteNotSupportedError("cif", "CIF file writing is not supported")
        self._iterator = iter(self._parse_atom_site_rows())

    def _iter_lines(self) -> typing.Iterator[str]:
        if self.fobj is not None:
            if hasattr(self.fobj, "seek"):
                try:
                    self.fobj.seek(0)
                except OSError:
                    pass
            for line in self.fobj:
                yield line.rstrip("\r\n")
        elif self.filename is not None:
            with open(self.filename, encoding=self.encoding) as f:
                for line in f:
                    yield line.rstrip("\r\n")

    def _parse_atom_site_rows(self) -> list[Row]:
        lines = list(self._iter_lines())
        i = 0
        rows: list[Row] = []
        found = False
        while i < len(lines):
            stripped = lines[i].strip()
            if stripped.lower() != "loop_":
                i += 1
                continue
            i += 1
            columns: list[str] = []
            while i < len(lines):
                tag = lines[i].strip()
                if not tag or tag.startswith("#"):
                    i += 1
                    continue
                if tag.startswith("_"):
                    columns.append(tag)
                    i += 1
                    continue
                break
            is_atom_site = bool(columns) and all(c.lower().startswith(_ATOM_SITE_PREFIX) for c in columns)
            if not is_atom_site:
                # Skip data rows of unrelated loops
                while i < len(lines):
                    row_line = lines[i].strip()
                    if row_line.lower() == "loop_" or row_line.lower().startswith("data_"):
                        break
                    if row_line.startswith("_"):
                        break
                    i += 1
                continue

            found = True
            keys = [c[len(_ATOM_SITE_PREFIX) :] for c in columns]
            n = len(keys)
            while i < len(lines):
                row_line = lines[i].strip()
                if not row_line:
                    i += 1
                    break
                if row_line.startswith("#"):
                    i += 1
                    continue
                if row_line.lower() == "loop_" or row_line.lower().startswith("data_") or row_line.startswith("_"):
                    break
                tokens = self._tokenize(row_line)
                while len(tokens) < n and i + 1 < len(lines):
                    nxt = lines[i + 1].strip()
                    if not nxt or nxt.startswith("#") or nxt.startswith("_") or nxt.lower() == "loop_":
                        break
                    i += 1
                    tokens.extend(self._tokenize(nxt))
                if len(tokens) >= n:
                    values = tokens[:n]
                    rows.append({keys[j]: self._coerce(values[j]) for j in range(n)})
                i += 1

        if not found:
            raise ValueError(
                "CIF file contains no loop_ with _atom_site.* columns; "
                "only atom_site loops are supported by this reader"
            )
        return rows

    @staticmethod
    def _tokenize(line: str) -> list[str]:
        """Split a CIF data line into tokens, respecting quoted strings."""
        tokens: list[str] = []
        i = 0
        n = len(line)
        while i < n:
            while i < n and line[i].isspace():
                i += 1
            if i >= n:
                break
            if line[i] in ("'", '"'):
                quote = line[i]
                i += 1
                start = i
                while i < n and line[i] != quote:
                    i += 1
                tokens.append(line[start:i])
                if i < n:
                    i += 1
            else:
                start = i
                while i < n and not line[i].isspace():
                    i += 1
                tokens.append(line[start:i])
        return tokens

    @staticmethod
    def _coerce(value: str) -> Any:
        if value in {".", "?"}:
            return None
        try:
            if any(c in value for c in ".eE"):
                return float(value)
            return int(value)
        except ValueError:
            return value

    @staticmethod
    def id() -> str:
        return "cif"

    @staticmethod
    def is_flatonly() -> bool:
        return True

    def is_streaming(self) -> bool:
        return True

    def read(self, skip_empty: bool = True) -> Row:
        """Read a single atom_site row."""
        try:
            row = next(self._iterator)  # type: ignore[arg-type]
            self.pos += 1
            return row
        except (StopIteration, TypeError):
            raise StopIteration from None

    def write(self, record: Row) -> None:
        raise WriteNotSupportedError("cif", "CIF file writing is not supported")

    def write_bulk(self, records: list[Row]) -> None:
        raise WriteNotSupportedError("cif", "CIF file writing is not supported")
