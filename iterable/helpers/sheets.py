"""Options shared by the spreadsheet readers (XLSX, XLS, ODS)."""

from __future__ import annotations

from typing import Any


def sheet_options(
    keys: list[str] | None, page: int, start_line: int, options: dict[str, Any]
) -> tuple[list[str] | None, int, int]:
    """``keys``, ``page`` and ``start_line`` from the constructor, else from ``options``.

    ``start_line`` is the number of rows above the header (title rows of a statistics table).
    """
    if keys is None and options.get("keys") is not None:
        keys = list(options["keys"])
    if "page" in options:
        page = int(options["page"])
    if not start_line and options.get("start_line") is not None:
        start_line = int(options["start_line"])
    if start_line < 0:
        raise ValueError(f"start_line must be a non-negative integer, got {start_line!r}")
    return keys, page, start_line
