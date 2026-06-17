from __future__ import annotations

import datetime
import typing
from typing import Any

import xlrd
from xlrd import open_workbook

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


def read_single_row(rownum, ncols, datemode, keys, sheet):
    """Read single row by row num"""
    tmp = list()
    for i in range(0, ncols):
        ct = sheet.cell_type(rownum, i)
        cell_value = sheet.cell_value(rownum, i)
        if ct == xlrd.XL_CELL_DATE:
            # Returns a tuple.
            dt_tuple = xlrd.xldate_as_tuple(cell_value, datemode)
            # Create datetime object from this tuple.
            get_col = str(
                datetime.datetime(dt_tuple[0], dt_tuple[1], dt_tuple[2], dt_tuple[3], dt_tuple[4], dt_tuple[5])
            )
        elif ct == xlrd.XL_CELL_NUMBER:
            get_col = int(cell_value)
        else:
            get_col = str(cell_value)
        tmp.append(get_col)
    row = dict(zip(keys, tmp, strict=False))
    return row


class XLSIterable(BaseFileIterable):
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
        super().__init__(filename, stream, codec=codec, binary=True, mode=mode, noopen=True, options=options)
        self.page = page
        self.start_line = start_line
        self.pos = start_line
        self.keys = keys
        self.extracted_keys = keys is None
        self.reset()
        pass

    def reset(self):
        """Reopen file and open sheet"""
        super().reset()
        self.pos = self.start_line
        self.workbook = open_workbook(self.filename)
        self.sheet = self.workbook.sheet_by_index(self.page)
        if self.extracted_keys:
            self.keys = read_row_keys(self.pos, self.sheet.ncols, self.sheet)
            self.pos += 1

    @staticmethod
    def id() -> str:
        """ID of the data source type"""
        return "xls"

    @staticmethod
    def is_flatonly() -> bool:
        """Flag that data is flat"""
        return True

    @staticmethod
    def has_tables() -> bool:
        """Indicates if this format supports multiple tables/sheets."""
        return True

    def list_tables(self, filename: str | None = None) -> list[str] | None:
        """List available sheet names in the Excel file.

        Args:
            filename: Optional filename. If None, uses instance's filename and reuses open workbook.

        Returns:
            list[str]: List of sheet names, or empty list if no sheets.
        """
        # If workbook is already open, reuse it
        if filename is None and hasattr(self, "workbook") and self.workbook is not None:
            return self.workbook.sheet_names()

        # Otherwise, open temporarily
        target_filename = filename if filename is not None else self.filename
        if target_filename is None:
            return None

        workbook = open_workbook(target_filename)
        try:
            return workbook.sheet_names()
        finally:
            workbook.release_resources()

    @staticmethod
    def has_totals() -> bool:
        """Has totals indicator"""
        return True

    def totals(self):
        """Returns file totals"""
        return self.sheet.nrows

    def read(self, skip_empty: bool = True) -> dict:
        """Read single XLS record"""
        if self.pos >= self.sheet.nrows:
            raise StopIteration
        row = read_single_row(self.pos, self.sheet.ncols, self.workbook.datemode, self.keys, self.sheet)
        self.pos += 1
        return row

    def read_bulk(self, num: int = DEFAULT_BULK_NUMBER) -> list[dict]:
        """Read bulk XLS records"""
        chunk = []
        ncols = self.sheet.ncols
        datemode = self.workbook.datemode
        for _n in range(0, num):
            if self.pos >= self.sheet.nrows:
                break
            row = read_single_row(self.pos, ncols, datemode, self.keys, self.sheet)
            chunk.append(row)
            self.pos += 1
        return chunk
