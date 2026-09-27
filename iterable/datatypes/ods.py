from __future__ import annotations

import typing

try:
    from odf.opendocument import OpenDocumentSpreadsheet, load
    from odf.table import Table, TableCell, TableRow
    from odf.text import P

    HAS_ODF = True
except ImportError:
    try:
        import pyexcel_ods3

        HAS_PYEXCEL_ODS = True
        HAS_ODF = False
    except ImportError:
        HAS_PYEXCEL_ODS = False
        HAS_ODF = False

from typing import Any

from ..base import BaseCodec, BaseFileIterable
from ..exceptions import ReadError
from ..types import Row


class ODSIterable(BaseFileIterable):
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
        if not HAS_ODF and not HAS_PYEXCEL_ODS:
            raise ImportError("ODS file support requires 'odfpy' or 'pyexcel-ods3' package")
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
        """Reset iterable"""
        super().reset()
        self.pos = self.start_line
        if self.mode in ("w", "wr"):
            # Buffered writer: rows accumulate until close() materializes the
            # spreadsheet document (ODS is a single-file container).
            self._write_rows: list[Row] = []
            self._write_keys: list[str] = list(self.keys) if self.keys else []
            return

        if HAS_ODF:
            # Using odfpy library
            self.doc = load(self.filename)
            self.sheets = [sheet for sheet in self.doc.spreadsheet.getElementsByType(Table)]
            if self.page >= len(self.sheets):
                raise ReadError(
                    f"Sheet index {self.page} out of range. Available sheets: {len(self.sheets)}",
                    filename=self.filename,
                    error_code="INVALID_PARAMETER",
                )
            self.sheet = self.sheets[self.page]
            self.rows = self.sheet.getElementsByType(TableRow)
            self.row_index = 0

            if self.extracted_keys and len(self.rows) > 0:
                # Extract keys from first row
                first_row = self.rows[0]
                cells = first_row.getElementsByType(TableCell)
                self.keys = []
                for cell in cells:
                    text_content = ""
                    paragraphs = cell.getElementsByType(P)
                    for p in paragraphs:
                        text_content += p.firstChild.data if p.firstChild else ""
                    self.keys.append(text_content if text_content else "")
                self.row_index = 1
                self.pos += 1
        else:
            # Using pyexcel_ods3 library
            self.data = pyexcel_ods3.get_data(self.filename)
            sheet_names = list(self.data.keys())
            if self.page >= len(sheet_names):
                raise ReadError(
                    f"Sheet index {self.page} out of range. Available sheets: {len(sheet_names)}",
                    filename=self.filename,
                    error_code="INVALID_PARAMETER",
                )
            self.sheet_name = sheet_names[self.page]
            self.rows = self.data[self.sheet_name]
            self.row_index = 0

            if self.extracted_keys and len(self.rows) > 0:
                # Extract keys from first row
                self.keys = [str(cell) for cell in self.rows[0]]
                self.row_index = 1
                self.pos += 1

    @staticmethod
    def has_totals() -> bool:
        """Has totals indicator"""
        return True

    def totals(self):
        """Returns file totals"""
        if HAS_ODF:
            return len(self.rows)
        else:
            return len(self.rows)

    @staticmethod
    def id() -> str:
        return "ods"

    @staticmethod
    def is_flatonly() -> bool:
        return True

    @staticmethod
    def has_tables() -> bool:
        """Indicates if this format supports multiple tables/sheets."""
        return True

    def list_tables(self, filename: str | None = None) -> list[str] | None:
        """List available sheet names in the ODS file.

        Args:
            filename: Optional filename. If None, uses instance's filename and reuses open document.

        Returns:
            list[str]: List of sheet names, or empty list if no sheets.
        """
        target_filename = filename if filename is not None else self.filename
        if target_filename is None:
            return None

        # If document is already open and using same file, reuse it
        if filename is None and hasattr(self, "doc") and self.doc is not None:
            if HAS_ODF:
                return [
                    sheet.getAttribute("name") or f"Sheet{i}"
                    for i, sheet in enumerate(self.doc.spreadsheet.getElementsByType(Table))
                ]
            elif HAS_PYEXCEL_ODS:
                return list(self.data.keys()) if hasattr(self, "data") else []

        # Otherwise, open temporarily
        if HAS_ODF:
            doc = load(target_filename)
            try:
                sheets = doc.spreadsheet.getElementsByType(Table)
                return [sheet.getAttribute("name") or f"Sheet{i}" for i, sheet in enumerate(sheets)]
            finally:
                # odfpy doesn't have explicit close, but we can clear reference
                del doc
        elif HAS_PYEXCEL_ODS:
            data = pyexcel_ods3.get_data(target_filename)
            return list(data.keys())
        else:
            return None

    def read(self, skip_empty: bool = True) -> dict:
        """Read single ODS record"""
        if HAS_ODF:
            if self.row_index >= len(self.rows):
                raise StopIteration
            row = self.rows[self.row_index]
            cells = row.getElementsByType(TableCell)
            values = []
            for cell in cells:
                text_content = ""
                paragraphs = cell.getElementsByType(P)
                for p in paragraphs:
                    text_content += p.firstChild.data if p.firstChild else ""
                values.append(text_content)
            # Pad values if needed
            while len(values) < len(self.keys):
                values.append("")
            result = dict(zip(self.keys, values, strict=False))
            self.row_index += 1
            self.pos += 1
            return result
        else:
            if self.row_index >= len(self.rows):
                raise StopIteration
            row = self.rows[self.row_index]
            # Convert to strings and pad if needed
            values = [str(cell) for cell in row]
            while len(values) < len(self.keys):
                values.append("")
            result = dict(zip(self.keys, values, strict=False))
            self.row_index += 1
            self.pos += 1
            return result

    def _buffer_row(self, record: Row) -> None:
        """Buffer one record for the document materialized on close()."""
        for key in record:
            if key not in self._write_keys:
                self._write_keys.append(key)
        self._write_rows.append(dict(record))

    def _materialize_document(self) -> None:
        """Write the buffered rows to an .ods document and save it."""
        if HAS_ODF:
            doc = OpenDocumentSpreadsheet()
            table = Table(name="Sheet1")
            doc.spreadsheet.addElement(table)
            if self._write_keys:
                header = TableRow()
                table.addElement(header)
                for key in self._write_keys:
                    cell = TableCell(valuetype="string")
                    cell.addElement(P(text=str(key)))
                    header.addElement(cell)
            for record in self._write_rows:
                row = TableRow()
                table.addElement(row)
                for key in self._write_keys:
                    row.addElement(self._make_cell(record.get(key)))
            target = self.filename if self.filename is not None else self.fobj
            doc.save(target)
        else:
            # pyexcel_ods3 fallback: string cells only
            rows = [list(self._write_keys)] if self._write_keys else []
            for record in self._write_rows:
                rows.append([record.get(key) for key in self._write_keys])
            pyexcel_ods3.save_data(self.filename, {"Sheet1": rows})

    @staticmethod
    def _make_cell(value: Any) -> TableCell:
        """Build a typed ODS cell; text paragraphs keep own-reader round-trips."""
        if value is None:
            return TableCell(valuetype="string")
        if isinstance(value, bool):
            cell = TableCell(valuetype="boolean", booleanvalue=value)
            cell.addElement(P(text="TRUE" if value else "FALSE"))
            return cell
        if isinstance(value, (int, float)):
            cell = TableCell(valuetype="float", value=value)
            cell.addElement(P(text=str(value)))
            return cell
        if hasattr(value, "isoformat"):
            cell = TableCell(valuetype="date", datevalue=value.isoformat())
            cell.addElement(P(text=value.isoformat()))
            return cell
        cell = TableCell(valuetype="string")
        cell.addElement(P(text=str(value)))
        return cell

    def write(self, record: Row) -> None:
        """Write single ODS record (buffered until close)."""
        if self._validation_hooks:
            validated = self._apply_validation_hooks(record)
            if validated is None:  # Skipped
                return
            record = validated
        self._buffer_row(record)

    def write_bulk(self, records: list[Row]) -> None:
        """Write bulk ODS records (buffered until close)."""
        if records is None:
            raise TypeError("write_bulk() requires a list of records, got None")
        if self._validation_hooks:
            validated_records = []
            for record in records:
                validated = self._apply_validation_hooks(record)
                if validated is not None:  # Not skipped
                    validated_records.append(validated)
            records = validated_records
        for record in records:
            self._buffer_row(record)

    def close(self):
        """Materialize buffered writes, then close the underlying file."""
        if self.mode in ("w", "wr") and getattr(self, "_write_rows", None) is not None:
            self._materialize_document()
            self._write_rows = None
        super().close()
