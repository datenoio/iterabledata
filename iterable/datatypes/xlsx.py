from __future__ import annotations

import typing
from typing import Any

from openpyxl import load_workbook

from ..base import DEFAULT_BULK_NUMBER, BaseCodec, BaseFileIterable


def read_row_keys(rownum, ncols, sheet):
    """Read single row by row num"""
    tmp = list()
    for i in range(0, ncols):
        sheet.cell_type(rownum, i)
        cell_value = sheet.cell_value(rownum, i)
        get_col = str(cell_value)
        tmp.append(get_col)
    return tmp


class XLSXIterable(BaseFileIterable):
    datamode = "binary"

    def __init__(
        self,
        filename: str | None = None,
        stream: typing.IO[Any] | None = None,
        codec: BaseCodec | None = None,
        mode="r",
        keys: list[str] | None = None,
        page: int = 0,
        start_line: int = 0,
        options: dict[str, Any] | None = None,
    ):
        if options is None:
            options = {}
        super().__init__(filename, stream, codec=codec, mode=mode, binary=True, noopen=True, options=options)
        self.keys = keys
        self.start_line = start_line + 1
        self.page = page
        if "page" in options.keys():
            self.page = int(options["page"])
        self.pos = self.start_line
        self.extracted_keys = keys is None
        self.reset()
        pass

    def reset(self):
        super().reset()
        self.workbook = load_workbook(self.filename)
        self.sheet = self.workbook[self.workbook.sheetnames[self.page]]
        self.pos = self.start_line
        self.cursor = self.sheet.iter_rows()
        if self.pos > 1:
            self.skip(self.pos - 1)
        if self.extracted_keys:
            self.keys = list()
            try:
                row = next(self.cursor)
                for cell in row:
                    self.keys.append(str(cell.value))
                self.pos += 1
            except StopIteration:
                # Empty sheet, use empty keys
                self.keys = []

    def skip(self, num: int = 1):
        while num > 0:
            num -= 1
            next(self.cursor)

    @staticmethod
    def has_totals() -> bool:
        """Has totals indicator"""
        return True

    def totals(self):
        """Returns file totals"""
        return self.sheet.max_row

    @staticmethod
    def id() -> str:
        return "xlsx"

    @staticmethod
    def is_flatonly() -> bool:
        return True

    @staticmethod
    def has_tables() -> bool:
        """Indicates if this format supports multiple tables/sheets."""
        return True

    def list_tables(self, filename: str | None = None) -> list[str] | None:
        """List available sheet names in the Excel file.

        Can be called as:
        - Instance method: `iterable.list_tables()` - reuses open workbook
        - With filename: `iterable.list_tables(filename)` - opens file temporarily

        Args:
            filename: Optional filename. If None, uses instance's filename and reuses open workbook.

        Returns:
            list[str]: List of sheet names, or empty list if no sheets.
        """
        # If workbook is already open, reuse it
        if filename is None and hasattr(self, "workbook") and self.workbook is not None:
            return self.workbook.sheetnames

        # Otherwise, open temporarily
        target_filename = filename if filename is not None else self.filename
        if target_filename is None:
            return None

        workbook = load_workbook(target_filename, read_only=True)
        try:
            return workbook.sheetnames
        finally:
            workbook.close()

    def read(self, skip_empty: bool = True) -> dict:
        """Read single XLSX record"""
        row = next(self.cursor)
        tmp = list()
        for cell in row:
            tmp.append(str(cell.value))
        result = dict(zip(self.keys, tmp, strict=False))
        self.pos += 1
        return result

    def read_bulk(self, num: int = DEFAULT_BULK_NUMBER) -> list[dict]:
        """Read bulk XLSX records"""
        chunk = []
        for _n in range(0, num):
            try:
                row = next(self.cursor)
            except StopIteration:
                break
            tmp = list()
            for cell in row:
                tmp.append(str(cell.value))
            result = dict(zip(self.keys, tmp, strict=False))
            chunk.append(result)
            self.pos += 1
        return chunk
