"""Progress tracking helpers for direct iteration."""

import time
from collections.abc import Callable, Iterator
from typing import Any, TypeVar

from ..base import BaseIterable
from ..types import Row

T = TypeVar("T", bound=BaseIterable)


def with_progress(
    iterable: T,
    callback: Callable[[dict[str, Any]], None],
    interval: int = 1000,
    start_time: float | None = None,
) -> Iterator[Row]:
    """
    Wrap an iterable with progress tracking for direct iteration.

    This helper function allows you to track progress while iterating over
    an iterable directly, without using convert() or pipeline().

    Args:
        iterable: The iterable to wrap with progress tracking
        callback: Progress callback function that receives stats dictionary
                 with keys: rows_read, elapsed, estimated_time_remaining
        interval: Number of rows between progress callback invocations.
                 Default: 1000.
        start_time: Optional start time for elapsed calculation.
                   If None, uses current time when iteration starts.

    Yields:
        Row: Rows from the iterable, same as iterating directly

    Examples:
        >>> from iterable.helpers.detect import open_iterable
        >>> from iterable.helpers.progress import with_progress
        >>>
        >>> def progress_callback(stats):
        ...     print(f"Processed {stats['rows_read']} rows in {stats['elapsed']:.2f}s")
        >>>
        >>> with open_iterable('large_file.csv') as source:
        ...     for row in with_progress(source, callback=progress_callback):
        ...         process(row)
    """
    if start_time is None:
        start_time = time.time()

    rows_read = 0

    for row in iterable:
        rows_read += 1

        # Invoke progress callback periodically
        if rows_read % interval == 0:
            elapsed = time.time() - start_time
            rate = rows_read / elapsed if elapsed > 0 else None

            try:
                callback(
                    {
                        "rows_read": rows_read,
                        "elapsed": elapsed,
                        "throughput": rate,
                    }
                )
            except Exception:
                # Silently ignore callback errors to prevent breaking iteration
                pass

        yield row

    # Final progress callback
    elapsed = time.time() - start_time
    rate = rows_read / elapsed if elapsed > 0 else None

    try:
        callback(
            {
                "rows_read": rows_read,
                "elapsed": elapsed,
                "throughput": rate,
            }
        )
    except Exception:
        pass
