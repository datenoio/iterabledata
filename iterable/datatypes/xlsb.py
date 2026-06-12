"""Excel Binary (.xlsb) format support using pyxlsb."""

from __future__ import annotations

import typing

try:
    from pyxlsb import open_workbook

    HAS_PYXLSB = True
except ImportError:
    open_workbook = None  # type: ignore[misc, assignment]
    HAS_PYXLSB = False

from ..base import BaseCodec, BaseFileIterable
from ..types import Row


class XLSBIterable(BaseFileIterable):
    """XLSB (Excel Binary) format: yields one dict per row, keys from first row."""

    datamode = "binary"

    def __init__(
        self,
        filename: str | None = None,
        stream: typing.IO[typing.Any] | None = None,
        codec: BaseCodec | None = None,
        mode: str = "r",
        keys: list[str] | None = None,
        page: int = 0,
        start_line: int = 0,
        options: dict[str, typing.Any] | None = None,
    ):
        if options is None:
            options = {}
        if not HAS_PYXLSB:
            raise ImportError("XLSB support requires 'pyxlsb'. Install with: pip install iterabledata[xlsb]") from None
        super().__init__(
            filename,
            stream,
            codec=codec,
            mode=mode,
            binary=True,
            noopen=True,
            options=options,
        )
        self.keys = keys
        self.page = options.get("page", page)
        self.start_line = start_line + 1
        self.pos = self.start_line
        self.extracted_keys = keys is None
        self.workbook = None
        self._sheet = None
        self._row_iter = None
        self.reset()

    def reset(self) -> None:
        """Reopen workbook and rewind to start."""
        super().reset()
        if self.filename is None:
            raise ValueError("XLSB requires a filename; stream is not supported")
        self.workbook = open_workbook(self.filename)
        # get_sheet uses 1-based index
        self._sheet = self.workbook.get_sheet(self.page + 1)
        self._row_iter = self._sheet.rows()
        self.pos = self.start_line
        if self.extracted_keys:
            self.keys = []
            try:
                first_row = next(self._row_iter)
                # first_row may be sparse; sort by column index
                cells = sorted(first_row, key=lambda c: getattr(c, "col", getattr(c, "c", 0)))
                self.keys = [str(cell.value) if cell.value is not None else "" for cell in cells]
                self.pos += 1
            except StopIteration:
                self.keys = []
        # Skip rows before start_line
        for _ in range(self.start_line - 1):
            try:
                next(self._row_iter)
            except StopIteration:
                break

    @staticmethod
    def id() -> str:
        return "xlsb"

    @staticmethod
    def is_flatonly() -> bool:
        return True

    @staticmethod
    def has_tables() -> bool:
        return True

    def list_tables(self, filename: str | None = None) -> list[str] | None:
        """List sheet names. Requires filename (XLSB does not support stream)."""
        target = filename or self.filename
        if target is None:
            return None
        try:
            with open_workbook(target) as wb:
                return list(wb.sheets)
        except Exception:
            return None

    def read(self, skip_empty: bool = True) -> Row:
        """Read single row as dict."""
        row_cells = next(self._row_iter)
        cells = sorted(row_cells, key=lambda c: getattr(c, "col", getattr(c, "c", 0)))
        values = [str(cell.value) if cell.value is not None else "" for cell in cells]
        n = len(self.keys)
        # Pad or trim to match keys
        if len(values) < n:
            values.extend([""] * (n - len(values)))
        elif len(values) > n:
            values = values[:n]
        self.pos += 1
        return dict(zip(self.keys, values, strict=False))

    def close(self) -> None:
        """Close workbook."""
        if self.workbook is not None:
            try:
                self.workbook.close()
            except Exception:
                pass
            self.workbook = None
        super().close()
