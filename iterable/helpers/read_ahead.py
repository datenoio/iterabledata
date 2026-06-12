"""Read-ahead caching support for IterableData.

This module provides read-ahead buffering to prefetch data from file sources,
reducing I/O wait time during sequential row processing.
"""

from collections.abc import Iterator

from ..types import Row


class ReadAheadBuffer:
    """Buffer for prefetched rows with automatic refilling.

    This class maintains a buffer of prefetched rows from a source iterator,
    automatically refilling the buffer when it drops below a threshold.
    This reduces I/O wait time by prefetching data ahead of consumption.

    Example:
        >>> source = iter([1, 2, 3, 4, 5])
        >>> buffer = ReadAheadBuffer(source, buffer_size=3, refill_threshold=0.3)
        >>> list(buffer)  # Prefetches 3 items, refills when buffer drops to 1
        [1, 2, 3, 4, 5]
    """

    def __init__(self, source: Iterator[Row], buffer_size: int = 10, refill_threshold: float = 0.3):
        """Initialize read-ahead buffer.

        Args:
            source: Source iterator to prefetch from
            buffer_size: Maximum number of rows to prefetch (default: 10)
            refill_threshold: Refill when buffer drops below this fraction (0.0-1.0, default: 0.3)
        """
        self.source = source
        self.buffer_size = buffer_size
        self.refill_threshold = int(buffer_size * refill_threshold)
        self.buffer: list[Row] = []
        self.exhausted = False

    def __iter__(self) -> Iterator[Row]:
        """Return iterator interface."""
        return self

    def __next__(self) -> Row:
        """Get next row from buffer, refilling if needed.

        Returns:
            Next row from the source

        Raises:
            StopIteration: When source is exhausted and buffer is empty
        """
        # Refill buffer if needed
        if len(self.buffer) <= self.refill_threshold and not self.exhausted:
            self._refill()

        # Return from buffer
        if self.buffer:
            return self.buffer.pop(0)

        # Buffer empty and source exhausted
        raise StopIteration

    def _refill(self) -> None:
        """Refill buffer from source."""
        target_size = self.buffer_size - len(self.buffer)
        for _ in range(target_size):
            try:
                row = next(self.source)
                self.buffer.append(row)
            except StopIteration:
                self.exhausted = True
                break

    def peek(self, n: int = 1) -> list[Row]:
        """Peek at next N rows without consuming them.

        Args:
            n: Number of rows to peek at (default: 1)

        Returns:
            List of next N rows (may be fewer if source is exhausted)
        """
        # Refill if needed
        if len(self.buffer) < n and not self.exhausted:
            self._refill()
        return self.buffer[:n]

    def clear(self) -> None:
        """Clear buffer (for reset operations)."""
        self.buffer.clear()
        self.exhausted = False

    def __len__(self) -> int:
        """Return current buffer size."""
        return len(self.buffer)
