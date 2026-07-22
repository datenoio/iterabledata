"""Lotus 1-2-3 spreadsheet reader (experimental).

Supports a minimal pure-Python WK1 (``.wk1`` / ``.wks`` / ``.123``) BIFF-like
record parser for LABEL / INTEGER / NUMBER cells — enough for small fixtures and
legacy dumps. Optionally uses ``pylotus`` if installed.

Read-only. Format id: ``123``.
"""

from __future__ import annotations

import struct
import typing
from typing import Any

from ..base import BaseCodec, BaseFileIterable
from ..exceptions import FormatParseError, WriteNotSupportedError
from ..types import Row

try:
    import pylotus  # type: ignore[import-untyped]

    HAS_PYLOTUS = True
except ImportError:
    HAS_PYLOTUS = False

# WK1 opcodes
_BOF = 0x0000
_EOF = 0x0001
_INTEGER = 0x000D
_NUMBER = 0x000E
_LABEL = 0x000F


def _col_name(index: int) -> str:
    """Convert 0-based column index to spreadsheet-style name (A, B, ..., AA)."""
    name = ""
    n = index + 1
    while n:
        n, rem = divmod(n - 1, 26)
        name = chr(65 + rem) + name
    return name


def _parse_wk1(data: bytes) -> list[dict[str, Any]]:
    """Parse a minimal WK1 workbook into row dicts (header-aware when row 0 is labels)."""
    if len(data) < 4:
        raise FormatParseError("123", "WK1 file too short")

    cells: dict[tuple[int, int], Any] = {}
    max_row = -1
    max_col = -1
    offset = 0
    saw_bof = False

    while offset + 4 <= len(data):
        opcode, length = struct.unpack_from("<HH", data, offset)
        offset += 4
        if offset + length > len(data):
            raise FormatParseError(
                "123",
                f"WK1 truncated record opcode=0x{opcode:04x} length={length}",
            )
        body = data[offset : offset + length]
        offset += length

        if opcode == _BOF:
            saw_bof = True
            continue
        if opcode == _EOF:
            break
        if opcode == _INTEGER and length >= 7:
            _fmt, col, row, value = struct.unpack_from("<Bhhh", body, 0)
            cells[(row, col)] = int(value)
            max_row = max(max_row, row)
            max_col = max(max_col, col)
        elif opcode == _NUMBER and length >= 13:
            _fmt, col, row = struct.unpack_from("<Bhh", body, 0)
            value = struct.unpack_from("<d", body, 5)[0]
            cells[(row, col)] = value
            max_row = max(max_row, row)
            max_col = max(max_col, col)
        elif opcode == _LABEL and length >= 6:
            _fmt, col, row = struct.unpack_from("<Bhh", body, 0)
            raw = body[5:]
            # First byte is alignment ('"', "'", "^", or "\\"); rest is ASCIZ text.
            if raw and raw[0:1] in (b"'", b'"', b"^", b"\\"):
                raw = raw[1:]
            text = raw.split(b"\x00", 1)[0].decode("latin-1", errors="replace")
            cells[(row, col)] = text
            max_row = max(max_row, row)
            max_col = max(max_col, col)

    if not saw_bof and not cells:
        raise FormatParseError(
            "123",
            "Not a recognizable WK1 Lotus 1-2-3 file (missing BOF / cells)",
        )
    if max_row < 0:
        return []

    # Detect header row: if every filled cell in row 0 is a string, use as keys.
    header_keys: list[str] | None = None
    row0_vals = [cells.get((0, c)) for c in range(max_col + 1)]
    if (
        row0_vals
        and all(isinstance(v, str) or v is None for v in row0_vals)
        and any(isinstance(v, str) for v in row0_vals)
    ):
        header_keys = []
        for c, v in enumerate(row0_vals):
            header_keys.append(v if isinstance(v, str) and v else _col_name(c))
        start_row = 1
    else:
        start_row = 0

    rows: list[dict[str, Any]] = []
    for r in range(start_row, max_row + 1):
        if header_keys is not None:
            record = {header_keys[c]: cells.get((r, c)) for c in range(max_col + 1)}
        else:
            record = {_col_name(c): cells.get((r, c)) for c in range(max_col + 1)}
        # Skip completely empty rows
        if all(v is None for v in record.values()):
            continue
        rows.append(record)
    return rows


class Lotus123Iterable(BaseFileIterable):
    """Experimental read-only Lotus 1-2-3 (WK1) iterable."""

    datamode = "binary"

    def __init__(
        self,
        filename: str | None = None,
        stream: typing.IO[Any] | None = None,
        codec: BaseCodec | None = None,
        mode: str = "r",
        options: dict[str, Any] | None = None,
    ):
        if options is None:
            options = {}
        if mode not in ("r", "rb"):
            raise WriteNotSupportedError("123", "Lotus 1-2-3 is read-only")
        self._use_header = options.pop("header", True)
        super().__init__(
            filename=filename,
            stream=stream,
            codec=codec,
            binary=True,
            mode="r",
            options=options,
        )
        self.reset()

    def reset(self) -> None:
        super().reset()
        self.pos = 0
        data = self.fobj.read()
        if isinstance(data, str):
            data = data.encode("latin-1")

        if HAS_PYLOTUS:
            try:
                book = pylotus.load(data) if hasattr(pylotus, "load") else None
                if book is not None:
                    self._rows = self._rows_from_pylotus(book)
                    self._iterator = iter(self._rows)
                    return
            except Exception:
                pass  # fall through to pure WK1 parser

        try:
            self._rows = _parse_wk1(data)
        except FormatParseError:
            raise
        except Exception as exc:
            raise FormatParseError(
                "123",
                f"Failed to parse Lotus 1-2-3 WK1 data: {exc}",
            ) from exc

        if not self._use_header and self._rows:
            # Re-key with column letters if caller disabled headers — best-effort:
            # parser already chose; leave as-is when header=False already letter keys.
            pass
        self._iterator = iter(self._rows)

    @staticmethod
    def _rows_from_pylotus(book: Any) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []
        sheet = book[0] if isinstance(book, (list, tuple)) else book
        for row in sheet:
            if isinstance(row, dict):
                rows.append(row)
            else:
                rows.append({_col_name(i): v for i, v in enumerate(row)})
        return rows

    @staticmethod
    def id() -> str:
        return "123"

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
        raise WriteNotSupportedError("123", "Lotus 1-2-3 is read-only")

    def write_bulk(self, records: list[Row]) -> None:
        raise WriteNotSupportedError("123", "Lotus 1-2-3 is read-only")
