"""Shared DataFrame conversion logic for ``BaseIterable``."""

from __future__ import annotations

from collections.abc import Callable, Iterable, Iterator
from typing import Any

from .types import Row


def _chunked_frames(
    row_source: Iterable[Row],
    chunksize: int,
    build_frame: Callable[[list[Row]], Any],
) -> Iterator[Any]:
    chunk: list[Row] = []
    for row in row_source:
        chunk.append(row)
        if len(chunk) >= chunksize:
            yield build_frame(chunk)
            chunk = []
    if chunk:
        yield build_frame(chunk)


def iterable_to_pandas(row_source: Iterable[Row], chunksize: int | None = None) -> Any:
    """Convert row iterator to pandas DataFrame(s)."""
    try:
        import pandas as pd  # type: ignore[import-untyped]
    except ImportError:
        raise ImportError("pandas is required for to_pandas(). Install it with: pip install pandas") from None

    if chunksize is None:
        rows = list(row_source)
        if not rows:
            return pd.DataFrame()
        return pd.DataFrame(rows)
    return _chunked_frames(row_source, chunksize, pd.DataFrame)


def iterable_to_polars(row_source: Iterable[Row], chunksize: int | None = None) -> Any:
    """Convert row iterator to Polars DataFrame(s)."""
    try:
        import polars as pl  # type: ignore[import-not-found]
    except ImportError:
        raise ImportError("polars is required for to_polars(). Install it with: pip install polars") from None

    if chunksize is None:
        rows = list(row_source)
        if not rows:
            return pl.DataFrame()
        return pl.DataFrame(rows)
    return _chunked_frames(row_source, chunksize, pl.DataFrame)


def iterable_to_dask(row_source: Iterable[Row], chunksize: int = 1000000) -> Any:
    """Convert row iterator to a Dask DataFrame."""
    try:
        import dask.dataframe as dd  # type: ignore[import-not-found]
        import pandas as pd
    except ImportError as e:
        if "dask" in str(e).lower():
            raise ImportError(
                "dask[dataframe] is required for to_dask(). Install it with: pip install 'dask[dataframe]'"
            ) from None
        raise ImportError("pandas is required for to_dask(). Install it with: pip install pandas") from None

    rows = list(row_source)
    if not rows:
        return dd.from_pandas(pd.DataFrame(), npartitions=1)
    df = pd.DataFrame(rows)
    return dd.from_pandas(df, npartitions=max(1, len(df) // chunksize))
