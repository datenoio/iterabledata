from __future__ import annotations

import typing
from typing import Any

from ..base import BaseCodec, BaseFileIterable
from ..exceptions import WriteNotSupportedError
from ..types import Row

try:
    from bs4 import BeautifulSoup

    HAS_BS4 = True
except ImportError:
    HAS_BS4 = False


class HTMLIterable(BaseFileIterable):
    """HTML table extraction iterable"""

    def __init__(
        self,
        filename: str = None,
        stream: typing.IO[Any] | None = None,
        codec: BaseCodec | None = None,
        mode: str = "r",
        encoding: str = "utf8",
        table_index: int = None,
        options: dict[str, Any] | None = None,
    ):
        if options is None:
            options = {}
        if not HAS_BS4:
            raise ImportError(
                "HTML format requires 'beautifulsoup4' package. "
                "Install it with: pip install iterabledata[html] or pip install beautifulsoup4"
            )
        self.table_index = table_index or options.get("table_index")
        super().__init__(filename, stream, codec=codec, mode=mode, binary=False, encoding=encoding, options=options)
        self.reset()
        pass

    def reset(self):
        """Reset iterable"""
        super().reset()
        self.pos = 0
        if self.mode == "r":
            # Read entire HTML content
            content = self.fobj.read()

            # Parse HTML with BeautifulSoup
            soup = BeautifulSoup(content, "html.parser")

            # Find all tables
            tables = soup.find_all("table")

            if not tables:
                self.rows = []
                self.keys = []
                return

            # If table_index is specified, use that table; otherwise use first table
            target_table = (
                tables[self.table_index]
                if self.table_index is not None and self.table_index < len(tables)
                else tables[0]
            )

            # Extract headers from <th> elements only
            headers = []
            header_row = target_table.find("tr")
            has_th_headers = False

            if header_row:
                # Check for <th> elements first
                th_cells = header_row.find_all("th")
                if th_cells:
                    headers = [cell.get_text(strip=True) for cell in th_cells]
                    has_th_headers = True

            # If no <th> headers found, generate column names from first data row
            if not has_th_headers:
                # Try to get column count from first data row
                first_data_row = target_table.find("tr")
                if first_data_row:
                    cells = first_data_row.find_all("td")
                    headers = [f"column_{i}" for i in range(len(cells))]
                else:
                    headers = []

            self.keys = headers

            # Extract all data rows
            self.rows = []
            data_rows = target_table.find_all("tr")

            # Skip header row if it contains <th> elements, otherwise process all rows
            start_idx = 1 if has_th_headers else 0

            for row in data_rows[start_idx:]:
                cells = row.find_all("td")
                if cells:  # Only process rows with data cells
                    values = [cell.get_text(strip=True) for cell in cells]
                    # Pad or truncate to match header count
                    while len(values) < len(headers):
                        values.append("")
                    if len(values) > len(headers):
                        values = values[: len(headers)]
                    self.rows.append(values)
        else:
            self.rows = []
            self.keys = []

    @staticmethod
    def id() -> str:
        return "html"

    @staticmethod
    def is_flatonly() -> bool:
        return True

    @staticmethod
    def has_tables() -> bool:
        """Indicates if this format supports multiple tables."""
        return True

    def list_tables(self, filename: str | None = None) -> list[str] | None:
        """List available table identifiers in the HTML file.

        Can be called as:
        - Instance method: `iterable.list_tables()` - reuses parsed HTML if available
        - With filename: `iterable.list_tables(filename)` - opens file temporarily

        Args:
            filename: Optional filename. If None, uses instance's filename.

        Returns:
            list[str]: List of table identifiers (IDs, captions, or indices), or empty list if no tables.
        """
        # If we need to read from file
        target_filename = filename if filename is not None else self.filename
        if target_filename is None:
            # Try to use open file if available
            if hasattr(self, "fobj") and self.fobj is not None:
                try:
                    current_pos = self.fobj.tell()
                    self.fobj.seek(0)
                    content = self.fobj.read()
                    self.fobj.seek(current_pos)
                except (AttributeError, OSError):
                    return None
            else:
                return None
        else:
            # Read from file
            encoding = self.encoding if hasattr(self, "encoding") else "utf8"
            try:
                with open(target_filename, encoding=encoding) as f:
                    content = f.read()
            except Exception:
                return None

        # Parse HTML
        soup = BeautifulSoup(content, "html.parser")
        tables = soup.find_all("table")

        if not tables:
            return []

        # Build list of identifiers, preferring ID, then caption, then index
        identifiers = []
        for idx, table in enumerate(tables):
            # Prefer ID attribute
            table_id = table.get("id")
            if table_id:
                identifiers.append(table_id)
            else:
                # Try caption
                caption = table.find("caption")
                if caption:
                    caption_text = caption.get_text(strip=True)
                    if caption_text:
                        identifiers.append(caption_text)
                    else:
                        identifiers.append(str(idx))
                else:
                    # Fall back to index
                    identifiers.append(str(idx))

        return identifiers

    def read(self, skip_empty: bool = True) -> dict:
        """Read single HTML table row"""
        if self.pos >= len(self.rows):
            raise StopIteration

        row_values = self.rows[self.pos]
        result = dict(zip(self.keys, row_values, strict=False))
        self.pos += 1
        return result

    def write(self, record: Row) -> None:
        """Write single HTML record (not supported)"""
        raise WriteNotSupportedError("html", "HTML write mode is not currently supported")

    def write_bulk(self, records: list[Row]) -> None:
        """Write bulk HTML records (not supported)"""
        raise WriteNotSupportedError("html", "HTML write mode is not currently supported")
