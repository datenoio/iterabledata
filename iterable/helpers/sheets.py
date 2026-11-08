"""Options shared by the spreadsheet readers (XLSX, XLS, ODS)."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any


def sheet_options(
    keys: list[str] | None, page: int | str, start_line: int, options: dict[str, Any]
) -> tuple[list[str] | None, int | str, int]:
    """``keys``, ``page`` and ``start_line`` from the constructor, else from ``options``.

    ``page`` is a sheet index or a sheet name; :func:`resolve_page` turns it into an index
    once the sheet names are known. ``start_line`` is the number of rows above the header
    (title rows of a statistics table).
    """
    if keys is None and options.get("keys") is not None:
        keys = list(options["keys"])
    if "page" in options:
        page = options["page"]
    if not start_line and options.get("start_line") is not None:
        start_line = int(options["start_line"])
    if start_line < 0:
        raise ValueError(f"start_line must be a non-negative integer, got {start_line!r}")
    return keys, page, start_line


def resolve_page(page: int | str, sheet_names: Sequence[str]) -> int:
    """Index of the sheet ``page`` names: an index, a sheet name, or an index as a string.

    A name wins over an index written as a string ("2" is the sheet named "2" if there is
    one). An unknown name raises ``ValueError`` listing the sheets.
    """
    if isinstance(page, bool):
        raise TypeError(f"page must be a sheet index or name, got {page!r}")
    if isinstance(page, int):
        return page
    name = str(page)
    names = list(sheet_names)
    if name in names:
        return names.index(name)
    text = name.strip()
    if text.lstrip("-").isdigit():
        return int(text)
    raise ValueError(f"Sheet {name!r} not found. Available sheets: {', '.join(repr(n) for n in names)}")


def row_with_rest(keys: Sequence[Any] | None, values: list[Any], empty: Any = None) -> dict[Any, Any]:
    """Record of one sheet row; cells beyond the header go to a list under the ``None`` key.

    Trailing ``empty`` cells beyond the header are padding and are dropped. Rows shorter than
    the header have only the keys of their cells, as before.
    """
    keys = keys or []
    record: dict[Any, Any] = dict(zip(keys, values, strict=False))
    rest = values[len(keys) :]
    while rest and rest[-1] == empty:
        rest.pop()
    if rest:
        record[None] = rest
    return record
