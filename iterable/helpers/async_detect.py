"""
Async version of detect module for async/await support.

Provides aopen_iterable() function and async format detection.
"""

from __future__ import annotations

import asyncio
from typing import Any

from ..async_base import AsyncBaseFileIterable, AsyncBaseIterable
from ..base import BaseIterable
from .detect import open_iterable


async def aopen_iterable(
    filename: str,
    mode: str = "r",
    engine: str = "internal",
    iterableargs: dict[str, Any] | None = None,
    codecargs: dict[str, Any] | None = None,
    debug: bool = False,
    **kwargs: Any,
) -> AsyncBaseIterable:
    """Open an iterable data source asynchronously.

    Async counterpart of open_iterable(): the blocking open/detection runs in
    a worker thread and the returned AsyncBaseIterable offloads each read to
    the default executor, so concurrent sources share the event loop.

    Args:
        filename: Path to file or connection string
        mode: File mode ('r' for read, 'w' for write, 'rb'/'wb' for binary)
        engine: Processing engine ('internal', 'duckdb', or database engine)
        iterableargs: Format-specific arguments
        codecargs: Codec-specific arguments
        debug: If True, enable verbose debug logging
        **kwargs: Additional arguments (currently not used)

    Returns:
        AsyncBaseIterable instance

    Examples:
        >>> async def main():  # doctest: +SKIP
        ...     source = await aopen_iterable('data.csv')
        ...     async with source:
        ...         async for row in source:
        ...             print(row)
        ...
        >>> import asyncio
        >>> asyncio.run(main())  # doctest: +SKIP

    Note:
        Detection, file open, and iteration run in the default thread-pool
        executor (`asyncio.to_thread` / `run_in_executor`), so the event loop
        stays responsive; underlying file and codec I/O remains synchronous
        inside the worker thread. The `stream` parameter is not supported for
        async operations.
    """
    # Detection and open are blocking (leading-byte sniffing, codec wrapping),
    # so offload them to a worker thread instead of stalling the event loop.
    sync_iterable = await asyncio.to_thread(
        lambda: open_iterable(
            filename=filename,
            mode=mode,
            engine=engine,
            iterableargs=iterableargs,
            codecargs=codecargs,
            debug=debug,
        )
    )

    # Wrap in async iterable
    if isinstance(sync_iterable, BaseIterable):
        # For file-based iterables, use AsyncBaseFileIterable
        return AsyncBaseFileIterable(sync_iterable=sync_iterable)
    else:
        # For other iterables, create a generic async wrapper
        # This is a fallback - most iterables should be BaseFileIterable
        return AsyncBaseFileIterable(sync_iterable=sync_iterable)
