"""Esri ASCII Grid (``.asc``) reader/writer (stdlib-only)."""

from __future__ import annotations

import typing
from typing import Any

from ..base import DEFAULT_BULK_NUMBER, BaseCodec, BaseFileIterable
from ..exceptions import WriteNotSupportedError
from ..types import Row

_HEADER_KEYS = {
    "ncols",
    "nrows",
    "xllcorner",
    "yllcorner",
    "xllcenter",
    "yllcenter",
    "cellsize",
    "nodata_value",
}


class ASCIIGridIterable(BaseFileIterable):
    """Esri ASCII Grid iterable.

    Default ``mode="cell"`` yields ``{row, col, x, y, value}`` (nodata skipped).
    ``options["mode"]="row"`` yields ``{row, values: [...]}`` including nodata cells.
    Write support is available for cell mode only.
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
        # Copy options and pop grid mode so BaseFileIterable._apply_options
        # does not overwrite the file open mode ("r"/"w").
        options = dict(options or {})
        self.cell_mode = str(options.pop("mode", "cell")).lower()
        self.header: dict[str, Any] = {}
        self._iterator: typing.Iterator[Row] | None = None
        self._write_buffer: list[Row] = []
        super().__init__(
            filename,
            stream,
            codec=codec,
            binary=False,
            mode=mode,
            encoding=encoding,
            options=options,
        )
        self.reset()

    def reset(self) -> None:
        super().reset()
        self.pos = 0
        self.header = {}
        self._write_buffer = []
        if self.mode == "r":
            self._iterator = self._yield_records()
        else:
            self._iterator = iter([])

    def _parse_header(self, lines: typing.Iterator[str]) -> list[float]:
        """Parse header lines; return numeric tokens from the first data line if any."""
        leftover: list[float] = []
        while True:
            try:
                raw = next(lines)
            except StopIteration:
                break
            line = raw.strip()
            if not line:
                continue
            parts = line.split()
            key = parts[0].lower()
            if key in _HEADER_KEYS and len(parts) >= 2:
                value: Any
                if key in ("ncols", "nrows"):
                    value = int(float(parts[1]))
                else:
                    value = float(parts[1])
                self.header[key] = value
                continue
            leftover = [float(p) for p in parts]
            break

        required = {"ncols", "nrows", "cellsize"}
        missing = required - set(self.header)
        if missing:
            raise ValueError(f"Invalid Esri ASCII Grid header; missing: {sorted(missing)}")
        if "xllcorner" not in self.header and "xllcenter" not in self.header:
            raise ValueError("Invalid Esri ASCII Grid header; need xllcorner or xllcenter")
        if "yllcorner" not in self.header and "yllcenter" not in self.header:
            raise ValueError("Invalid Esri ASCII Grid header; need yllcorner or yllcenter")
        return leftover

    def _origin(self) -> tuple[float, float]:
        cellsize = float(self.header["cellsize"])
        if "xllcorner" in self.header:
            x0 = float(self.header["xllcorner"]) + cellsize / 2.0
        else:
            x0 = float(self.header["xllcenter"])
        if "yllcorner" in self.header:
            # Row 0 is the northernmost row in Esri ASCII Grid
            y_top = float(self.header["yllcorner"]) + float(self.header["nrows"]) * cellsize - cellsize / 2.0
        else:
            y_center_bottom = float(self.header["yllcenter"])
            y_top = y_center_bottom + (float(self.header["nrows"]) - 1) * cellsize
        return x0, y_top

    def _token_stream(self, lines: typing.Iterator[str], initial: list[float]) -> typing.Iterator[float]:
        yield from initial
        for raw in lines:
            parts = raw.split()
            if not parts:
                continue
            for p in parts:
                yield float(p)

    def _yield_records(self) -> typing.Iterator[Row]:
        if self.fobj is not None:
            if hasattr(self.fobj, "seek"):
                self.fobj.seek(0)
            lines = iter(self.fobj)
        elif self.filename is not None:
            lines = open(self.filename, encoding=self.encoding)
        else:
            raise ValueError("ASCII Grid requires a filename or stream")

        close_after = self.fobj is None and self.filename is not None
        try:
            leftover = self._parse_header(lines)
            ncols = int(self.header["ncols"])
            nrows = int(self.header["nrows"])
            cellsize = float(self.header["cellsize"])
            nodata = self.header.get("nodata_value")
            x0, y_top = self._origin()
            tokens = self._token_stream(lines, leftover)

            for row in range(nrows):
                row_vals: list[float] = []
                for _ in range(ncols):
                    try:
                        row_vals.append(next(tokens))
                    except StopIteration as exc:
                        raise ValueError(
                            f"ASCII Grid data incomplete at row {row}: expected {ncols} columns, got {len(row_vals)}"
                        ) from exc
                if self.cell_mode == "row":
                    yield {"row": row, "values": row_vals}
                    continue
                y = y_top - row * cellsize
                for col, value in enumerate(row_vals):
                    if nodata is not None and value == nodata:
                        continue
                    x = x0 + col * cellsize
                    yield {"row": row, "col": col, "x": x, "y": y, "value": value}
        finally:
            if close_after and hasattr(lines, "close"):
                lines.close()

    @staticmethod
    def id() -> str:
        return "asc"

    @staticmethod
    def is_flatonly() -> bool:
        return True

    def is_streaming(self) -> bool:
        return True

    def read(self, skip_empty: bool = True) -> Row:
        assert self._iterator is not None
        row = next(self._iterator)
        self.pos += 1
        return row

    def read_bulk(self, num: int = DEFAULT_BULK_NUMBER) -> list[Row]:
        rows: list[Row] = []
        for _ in range(num):
            try:
                rows.append(self.read())
            except StopIteration:
                break
        return rows

    def write(self, record: Row) -> None:
        if self.mode == "r":
            raise WriteNotSupportedError("asc", "Opened in read mode")
        if self.cell_mode != "cell":
            raise WriteNotSupportedError("asc", "Write support is only available for cell mode")
        self._write_buffer.append(record)

    def write_bulk(self, records: list[Row]) -> None:
        for record in records:
            self.write(record)

    def close(self) -> None:
        if self.mode in ("w", "wr") and self._write_buffer:
            self._flush_write()
        super().close()

    def _flush_write(self) -> None:
        """Write buffered cell records as an Esri ASCII Grid."""
        cells = self._write_buffer
        if not cells:
            return
        rows = [int(c["row"]) for c in cells]
        cols = [int(c["col"]) for c in cells]
        nrows = max(rows) + 1
        ncols = max(cols) + 1
        # Infer cellsize / origin from adjacent cells when possible
        cellsize = 1.0
        xs = [float(c["x"]) for c in cells if "x" in c]
        ys = [float(c["y"]) for c in cells if "y" in c]
        if len({(r, c) for r, c in zip(rows, cols, strict=False)}) > 1 and xs and ys:
            # Prefer delta between col 0 and col 1 in same row
            by_row: dict[int, list[tuple[int, float]]] = {}
            for c in cells:
                by_row.setdefault(int(c["row"]), []).append((int(c["col"]), float(c["x"])))
            for entries in by_row.values():
                entries.sort()
                if len(entries) >= 2:
                    cellsize = entries[1][1] - entries[0][1]
                    break
        nodata = -9999.0
        grid = [[nodata for _ in range(ncols)] for _ in range(nrows)]
        xll = None
        yll = None
        for c in cells:
            r, col = int(c["row"]), int(c["col"])
            grid[r][col] = float(c["value"])
            if "x" in c and "y" in c:
                # Store lower-left corner using cell centers
                cx, cy = float(c["x"]), float(c["y"])
                candidate_xll = cx - col * cellsize - cellsize / 2.0
                candidate_yll = cy - (nrows - 1 - r) * cellsize - cellsize / 2.0
                if xll is None:
                    xll, yll = candidate_xll, candidate_yll
        if xll is None:
            xll, yll = 0.0, 0.0

        lines = [
            f"ncols         {ncols}",
            f"nrows         {nrows}",
            f"xllcorner     {xll}",
            f"yllcorner     {yll}",
            f"cellsize      {cellsize}",
            f"NODATA_value  {nodata}",
        ]
        for row_vals in grid:
            lines.append(" ".join(str(v) for v in row_vals))
        text = "\n".join(lines) + "\n"
        if self.fobj is not None:
            if hasattr(self.fobj, "seek"):
                self.fobj.seek(0)
                if hasattr(self.fobj, "truncate"):
                    self.fobj.truncate(0)
            self.fobj.write(text)
        elif self.filename is not None:
            with open(self.filename, "w", encoding=self.encoding) as f:
                f.write(text)
        self._write_buffer = []
