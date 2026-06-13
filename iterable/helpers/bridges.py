"""Helper functions for DataFrame bridges (Pandas, Polars, Dask)."""

from __future__ import annotations

import typing

from ..helpers.detect import open_iterable


def to_dask(
    files: str | list[str],
    chunksize: int = 1000000,
    **iterableargs,
) -> typing.Any:
    """Convert multiple files to a unified Dask DataFrame.

    Automatically detects the format of each file using open_iterable() and
    builds a Dask computation graph that combines all files.

    Args:
        files: Single file path (str) or list of file paths to convert.
        chunksize: Number of rows per partition. Default: 1000000.
        **iterableargs: Additional arguments to pass to open_iterable() for each file.

    Returns:
        Dask DataFrame containing data from all files.

    Raises:
        ImportError: If dask or pandas is not installed. Message includes installation instructions.
        ValueError: If files is empty or invalid.

    Example:
        >>> df = to_dask(['file1.csv', 'file2.jsonl', 'file3.parquet'])  # doctest: +SKIP
        >>> result = df.groupby('category').sum().compute()  # doctest: +SKIP
    """
    try:
        import dask.dataframe as dd
        import pandas as pd
    except ImportError as e:
        if "dask" in str(e).lower():
            raise ImportError(
                "dask[dataframe] is required for to_dask(). Install it with: pip install 'dask[dataframe]'"
            ) from None
        else:
            raise ImportError("pandas is required for to_dask(). Install it with: pip install pandas") from None

    # Normalize input to list
    if isinstance(files, str):
        file_list = [files]
    elif isinstance(files, (list, tuple)):
        file_list = list(files)
    else:
        raise ValueError(f"files must be a string or list of strings, got {type(files).__name__}")

    if not file_list:
        raise ValueError("files list cannot be empty")

    # Convert each file to a Dask DataFrame
    dask_dataframes = []
    for file_path in file_list:
        with open_iterable(file_path, **iterableargs) as source:
            # Collect rows from this file
            rows = list(source)
            if rows:
                df = pd.DataFrame(rows)
                ddf = dd.from_pandas(df, npartitions=max(1, len(df) // chunksize))
                dask_dataframes.append(ddf)

    if not dask_dataframes:
        # All files were empty, return empty Dask DataFrame
        return dd.from_pandas(pd.DataFrame(), npartitions=1)

    # Concatenate all Dask DataFrames
    if len(dask_dataframes) == 1:
        return dask_dataframes[0]
    else:
        return dd.concat(dask_dataframes, ignore_index=True)
