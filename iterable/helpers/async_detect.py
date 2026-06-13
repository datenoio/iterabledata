"""
Async version of detect module for async/await support.

Provides aopen_iterable() function and async format detection.
"""

from __future__ import annotations

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

    This is the async version of open_iterable(). It wraps the synchronous
    open_iterable() function and provides async interface.

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
        Currently uses thread pool executor to wrap synchronous operations.
        Native async I/O support is planned for Phase 2.
        Stream parameter is not yet supported for async operations.
    """
    # Create synchronous iterable
    sync_iterable = open_iterable(
        filename=filename,
        mode=mode,
        engine=engine,
        iterableargs=iterableargs,
        codecargs=codecargs,
        debug=debug,
    )

    # Wrap in async iterable
    if isinstance(sync_iterable, BaseIterable):
        # For file-based iterables, use AsyncBaseFileIterable
        return AsyncBaseFileIterable(sync_iterable=sync_iterable)
    else:
        # For other iterables, create a generic async wrapper
        # This is a fallback - most iterables should be BaseFileIterable
        return AsyncBaseFileIterable(sync_iterable=sync_iterable)
