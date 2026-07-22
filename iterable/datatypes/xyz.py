"""XYZ molecular/point coordinate table format (stdlib-only)."""

from __future__ import annotations

import typing
from typing import Any

from ..base import BaseCodec, BaseFileIterable
from ..types import Row


def _parse_float(token: str) -> float:
    return float(token)


class XYZIterable(BaseFileIterable):
    """XYZ point/molecular coordinates: optional atom count + comment, then rows.

    Each yielded record contains ``element``, ``x``, ``y``, ``z``. Extra
    whitespace-separated fields become ``extra_0``, ``extra_1``, …
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
        self._write_buffer: list[Row] = []
        self.pos = 0
        self.reset()

    def reset(self) -> None:
        """Reset and (re)build coordinate iterator."""
        super().reset()
        self.pos = 0
        self._write_buffer = []
        if self.mode != "r":
            self._iterator = iter([])
            return
        self._iterator = self._yield_atoms()

    def _lines(self) -> typing.Iterable[str]:
        if self.fobj is not None:
            if hasattr(self.fobj, "seek"):
                try:
                    self.fobj.seek(0)
                except OSError:
                    pass
            return self.fobj
        if self.filename is not None:
            return open(self.filename, encoding=self.encoding)
        return []

    def _yield_atoms(self) -> typing.Iterator[Row]:
        source = self._lines()
        close_after = self.fobj is None and self.filename is not None
        try:
            lines = iter(source)
            first = next(lines, None)
            if first is None:
                return
            first = first.rstrip("\r\n")
            remaining: list[str] | None = None
            # Optional atom-count header
            if first.strip().isdigit():
                comment = next(lines, None)
                if comment is not None:
                    # Comment line is skipped (not yielded)
                    pass
            else:
                # No count line — first line may be a coordinate row
                remaining = [first]

            def _iter_body() -> typing.Iterator[str]:
                if remaining:
                    yield from remaining
                yield from lines

            for line in _iter_body():
                line = line.rstrip("\r\n")
                if not line.strip():
                    continue
                parts = line.split()
                if len(parts) < 4:
                    continue
                element = parts[0]
                try:
                    x = _parse_float(parts[1])
                    y = _parse_float(parts[2])
                    z = _parse_float(parts[3])
                except ValueError:
                    # Likely a comment/title line without a preceding count
                    continue
                row: Row = {"element": element, "x": x, "y": y, "z": z}
                for i, extra in enumerate(parts[4:]):
                    try:
                        row[f"extra_{i}"] = _parse_float(extra)
                    except ValueError:
                        row[f"extra_{i}"] = extra
                yield row
        finally:
            if close_after and hasattr(source, "close"):
                source.close()

    @staticmethod
    def id() -> str:
        return "xyz"

    @staticmethod
    def is_flatonly() -> bool:
        return True

    def is_streaming(self) -> bool:
        return True

    def read(self, skip_empty: bool = True) -> Row:
        """Read a single XYZ atom/point record."""
        try:
            row = next(self._iterator)  # type: ignore[arg-type]
            self.pos += 1
            return row
        except (StopIteration, TypeError):
            raise StopIteration from None

    def write(self, record: Row) -> None:
        """Buffer a single XYZ record (flushed on close)."""
        self.write_bulk([record])

    def write_bulk(self, records: list[Row]) -> None:
        """Buffer XYZ records; header is written on close once count is known."""
        self._write_buffer.extend(records)

    def _format_line(self, record: Row) -> str:
        element = record.get("element", "X")
        x = float(record.get("x", 0.0))
        y = float(record.get("y", 0.0))
        z = float(record.get("z", 0.0))
        extras: list[str] = []
        i = 0
        while f"extra_{i}" in record:
            extras.append(str(record[f"extra_{i}"]))
            i += 1
        # Also accept any leftover keys beyond element/xyz as extras in insertion order
        known = {"element", "x", "y", "z"} | {f"extra_{j}" for j in range(i)}
        for key, value in record.items():
            if key not in known:
                extras.append(str(value))
        parts = [str(element), f"{x:.10g}", f"{y:.10g}", f"{z:.10g}", *extras]
        return " ".join(parts) + "\n"

    def close(self) -> None:
        """Flush buffered XYZ rows with atom count and comment header."""
        if self.mode == "w" and self._write_buffer:
            lines = [f"{len(self._write_buffer)}\n", "generated by iterabledata\n"]
            lines.extend(self._format_line(rec) for rec in self._write_buffer)
            text = "".join(lines)
            if self.fobj is not None:
                self.fobj.write(text)
            elif self.filename is not None:
                with open(self.filename, "w", encoding=self.encoding) as f:
                    f.write(text)
            self._write_buffer = []
        super().close()
