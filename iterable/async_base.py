"""
Async base classes for IterableData.

Provides async versions of BaseIterable and BaseFileIterable for
asynchronous I/O operations.
"""

from __future__ import annotations

import asyncio
from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from typing import Any, cast

from .base import BaseFileIterable
from .types import Row

# Sentinel returned by executor workers when the wrapped sync source is
# exhausted: StopIteration cannot be raised through a Future (asyncio
# converts it to RuntimeError), so it is caught in the worker thread.
_EXHAUSTED = object()


class AsyncBaseIterable(ABC):
    """Base class for async iterable data sources.

    Provides async iterator protocol and async context manager support.
    This is the async equivalent of BaseIterable.
    """

    def __init__(self) -> None:
        """Initialize async iterable."""
        self._closed = False

    @abstractmethod
    async def aread(self, skip_empty: bool = True) -> Row:
        """Read a single row asynchronously.

        Args:
            skip_empty: Whether to skip empty rows

        Returns:
            Dictionary representing a row

        Raises:
            StopAsyncIteration: When no more rows are available
        """
        raise NotImplementedError

    async def aread_bulk(self, num: int = 1000) -> list[Row]:
        """Read multiple rows asynchronously.

        Args:
            num: Number of rows to read

        Returns:
            List of row dictionaries
        """
        rows = []
        for _ in range(num):
            try:
                row = await self.aread()
                rows.append(row)
            except StopAsyncIteration:
                break
        return rows

    async def awrite(self, record: Row) -> None:
        """Write a single row asynchronously.

        Args:
            record: Row dictionary to write

        Raises:
            WriteNotSupportedError: If write is not supported
        """
        raise NotImplementedError("Write not supported")

    async def awrite_bulk(self, records: list[Row]) -> None:
        """Write multiple rows asynchronously.

        Args:
            records: List of row dictionaries to write

        Raises:
            WriteNotSupportedError: If write is not supported
        """
        for record in records:
            await self.awrite(record)

    async def areset(self) -> None:
        """Reset the iterator asynchronously.

        Raises:
            NotImplementedError: If reset is not supported
        """
        raise NotImplementedError("Reset not supported")

    async def aclose(self) -> None:
        """Close the iterable asynchronously."""
        self._closed = True

    async def __aenter__(self) -> AsyncBaseIterable:
        """Async context manager entry."""
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: Any,
    ) -> None:
        """Async context manager exit."""
        await self.aclose()

    def __aiter__(self) -> AsyncIterator[Row]:
        """Return async iterator."""
        return self

    async def __anext__(self) -> Row:
        """Get next row asynchronously.

        StopIteration from a wrapped synchronous source is converted to
        StopAsyncIteration; all other exceptions (parse errors, I/O errors)
        propagate to the caller instead of silently ending iteration.
        """
        if self._closed:
            raise StopAsyncIteration

        try:
            return await self.aread()
        except StopIteration as err:
            raise StopAsyncIteration from err


class AsyncBaseFileIterable(AsyncBaseIterable):
    """Base class for async file-based iterables.

    Provides async file I/O operations. This is the async equivalent
    of BaseFileIterable.
    """

    def __init__(self, sync_iterable: BaseFileIterable | None = None) -> None:
        """Initialize async file iterable.

        Args:
            sync_iterable: Optional synchronous iterable to wrap
        """
        super().__init__()
        self._sync = sync_iterable
        self._loop: asyncio.AbstractEventLoop | None = None

    def _get_loop(self) -> asyncio.AbstractEventLoop:
        """Get or create event loop."""
        if self._loop is None:
            try:
                self._loop = asyncio.get_running_loop()
            except RuntimeError:
                # No running loop, create new one (shouldn't happen in normal usage)
                self._loop = asyncio.new_event_loop()
        return self._loop

    async def aopen(self) -> None:
        """Open the file asynchronously."""
        if self._sync is not None:
            loop = self._get_loop()
            await loop.run_in_executor(None, self._sync.open)

    async def aread(self, skip_empty: bool = True) -> Row:
        """Read a single row asynchronously.

        Args:
            skip_empty: Whether to skip empty rows

        Returns:
            Dictionary representing a row

        Raises:
            StopAsyncIteration: When no more rows are available
        """
        if self._sync is None:
            raise RuntimeError("No synchronous iterable available")

        loop = self._get_loop()
        sync = self._sync

        def _read() -> Row | object:
            try:
                return sync.read(skip_empty=skip_empty)
            except StopIteration:
                return _EXHAUSTED

        result = await loop.run_in_executor(None, _read)
        if result is _EXHAUSTED:
            raise StopAsyncIteration
        return cast(Row, result)

    async def aread_bulk(self, num: int = 1000) -> list[Row]:
        """Read multiple rows asynchronously.

        Args:
            num: Number of rows to read

        Returns:
            List of row dictionaries
        """
        if self._sync is None:
            raise RuntimeError("No synchronous iterable available")

        loop = self._get_loop()
        sync = self._sync

        def _read_bulk() -> list[Row]:
            return sync.read_bulk(num)

        return await loop.run_in_executor(None, _read_bulk)

    async def awrite(self, record: Row) -> None:
        """Write a single row asynchronously.

        Args:
            record: Row dictionary to write

        Raises:
            WriteNotSupportedError: If write is not supported
        """
        if self._sync is None:
            raise RuntimeError("No synchronous iterable available")

        loop = self._get_loop()
        sync = self._sync

        def _write() -> None:
            sync.write(record)

        await loop.run_in_executor(None, _write)

    async def awrite_bulk(self, records: list[Row]) -> None:
        """Write multiple rows asynchronously.

        Args:
            records: List of row dictionaries to write

        Raises:
            WriteNotSupportedError: If write is not supported
        """
        if self._sync is None:
            raise RuntimeError("No synchronous iterable available")

        loop = self._get_loop()
        sync = self._sync

        def _write_bulk() -> None:
            sync.write_bulk(records)

        await loop.run_in_executor(None, _write_bulk)

    async def areset(self) -> None:
        """Reset the iterator asynchronously.

        Raises:
            NotImplementedError: If reset is not supported
        """
        if self._sync is None:
            raise RuntimeError("No synchronous iterable available")

        loop = self._get_loop()
        sync = self._sync

        def _reset() -> None:
            sync.reset()

        await loop.run_in_executor(None, _reset)

    async def aclose(self) -> None:
        """Close the file asynchronously."""
        if self._sync is not None:
            loop = self._get_loop()
            sync = self._sync

            def _close() -> None:
                sync.close()

            await loop.run_in_executor(None, _close)

        await super().aclose()

    async def __aenter__(self) -> AsyncBaseFileIterable:
        """Async context manager entry."""
        await self.aopen()
        return self
