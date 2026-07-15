import importlib

import pytest

from iterable.datatypes import (
    CSVIterable,
    JSONIterable,
    JSONLinesIterable,
    XLSIterable,
    XLSXIterable,
)


def _optional_param(class_name, dep, path, kwargs, header_may_affect_totals):
    """Build a parametrize entry that skips when the optional dependency is absent.

    The datatype class is resolved lazily so that a missing optional dependency
    skips the single parameter instead of erroring at collection time.
    """
    cls = None
    marks = ()
    if importlib.util.find_spec(dep) is not None:
        cls = getattr(importlib.import_module("iterable.datatypes"), class_name, None)
    if cls is None:
        marks = (pytest.mark.skip(reason=f"{dep} is required for {class_name}"),)
        cls = class_name  # placeholder; test body is skipped before use
    return pytest.param(cls, path, kwargs, header_may_affect_totals, marks=marks)


@pytest.mark.parametrize(
    "iterable_cls, path, kwargs, header_may_affect_totals",
    [
        pytest.param(CSVIterable, "fixtures/2cols6rows.csv", {}, True),
        pytest.param(JSONIterable, "fixtures/2cols6rows_tag.json", {"tagname": "persons"}, True),
        pytest.param(JSONLinesIterable, "fixtures/2cols6rows_flat.jsonl", {}, True),
        pytest.param(XLSIterable, "fixtures/2cols6rows.xls", {}, True),
        pytest.param(XLSXIterable, "fixtures/2cols6rows.xlsx", {}, True),
        _optional_param("ORCIterable", "pyorc", "fixtures/2cols6rows.orc", {}, True),
        _optional_param("ParquetIterable", "pyarrow", "fixtures/2cols6rows.parquet", {}, True),
        _optional_param("DBFIterable", "dbfread", "fixtures/2cols6rows.dbf", {}, False),
    ],
)
def test_totals_match_record_count(iterable_cls, path, kwargs, header_may_affect_totals):
    it = iterable_cls(path, **kwargs)

    # Some classes may not expose has_totals; default is False on base
    has_totals = False
    if hasattr(iterable_cls, "has_totals") and callable(iterable_cls.has_totals):
        has_totals = iterable_cls.has_totals()

    assert has_totals is True

    totals_value = it.totals()

    # Normalize Parquet's scan_contents dict
    if isinstance(totals_value, dict):
        totals_normalized = totals_value.get("num_rows") or totals_value.get("rows")
    else:
        totals_normalized = totals_value

    assert isinstance(totals_normalized, int)

    # Count actual iterated records
    n = 0
    for _ in it:
        n += 1

    it.close()

    if header_may_affect_totals:
        # Some spreadsheet formats report total rows including header.
        assert totals_normalized in (n, n + 1)
    else:
        assert totals_normalized == n
