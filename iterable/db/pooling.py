"""
Connection pooling for database drivers.

Provides thread-safe connection pooling to improve performance when
processing multiple queries or files from the same database.
"""

from __future__ import annotations

import logging
import time
from abc import ABC, abstractmethod
from collections.abc import Callable
from queue import Empty, Queue
from threading import Lock
from typing import Any

logger = logging.getLogger(__name__)

# Global pool registry
_pools: dict[str, ConnectionPool] = {}
_pools_lock = Lock()


class ConnectionPool(ABC):
    """Base class for connection pools."""

    @abstractmethod
    def acquire(self) -> tuple[Any, float]:
        """Acquire a connection from the pool.

        Returns:
            Tuple of (connection, created_time)

        Raises:
            TimeoutError: If connection cannot be acquired within timeout
        """
        pass

    @abstractmethod
    def release(self, conn: Any, created_time: float) -> None:
        """Release a connection back to the pool.

        Args:
            conn: Connection object to release
            created_time: Time when connection was created
        """
        pass

    @abstractmethod
    def close_all(self) -> None:
        """Close all connections in the pool."""
        pass


class SimpleConnectionPool(ConnectionPool):
    """Simple thread-safe connection pool.

    Manages a pool of database connections with configurable size limits,
    idle timeout, and connection validation.
    """

    def __init__(
        self,
        factory: Callable[[], Any],
        min_size: int = 1,
        max_size: int = 10,
        timeout: float = 30.0,
        max_idle: float = 300.0,
        validate: Callable[[Any], bool] | None = None,
    ):
        """Initialize connection pool.

        Args:
            factory: Callable that creates a new connection
            min_size: Minimum number of connections to maintain
            max_size: Maximum number of connections in pool
            timeout: Maximum time (seconds) to wait for connection
            max_idle: Maximum time (seconds) a connection can be idle before being closed
            validate: Optional callable to validate connection health
        """
        self._factory = factory
        self._min_size = min_size
        self._max_size = max_size
        self._timeout = timeout
        self._max_idle = max_idle
        self._validate = validate or (lambda conn: True)

        self._pool: Queue[tuple[Any, float]] = Queue()
        self._created = 0
        self._lock = Lock()

        # Pre-populate pool with min_size connections
        for _ in range(min_size):
            self._create_and_add()

    def _create_and_add(self) -> None:
        """Create a new connection and add to pool."""
        try:
            conn = self._factory()
            self._pool.put((conn, time.time()))
            with self._lock:
                self._created += 1
        except Exception as e:
            logger.warning(f"Failed to create connection: {e}")

    def _close_connection(self, conn: Any) -> None:
        """Close a connection (database-specific)."""
        try:
            if hasattr(conn, "close"):
                conn.close()
        except Exception as e:
            logger.debug(f"Error closing connection: {e}")

    def acquire(self) -> tuple[Any, float]:
        """Acquire a connection from the pool.

        Returns:
            Tuple of (connection, created_time)

        Raises:
            TimeoutError: If connection cannot be acquired within timeout
        """
        deadline = time.time() + self._timeout

        while time.time() < deadline:
            try:
                conn, created_time = self._pool.get_nowait()

                # Check if connection is stale
                if time.time() - created_time > self._max_idle:
                    try:
                        self._close_connection(conn)
                    except Exception:
                        pass
                    conn = self._factory()
                    created_time = time.time()

                # Validate connection
                if not self._validate(conn):
                    try:
                        self._close_connection(conn)
                    except Exception:
                        pass
                    conn = self._factory()
                    created_time = time.time()

                return conn, created_time
            except Empty:
                # No connection available, create new one if under max_size.
                # Reserve the slot under the lock, then build the connection
                # OUTSIDE the lock: self._factory() can allocate and trigger GC,
                # whose __del__ -> close() -> release() re-enters this same
                # (non-reentrant) lock on the same thread and would deadlock.
                reserved = False
                with self._lock:
                    if self._created < self._max_size:
                        self._created += 1
                        reserved = True

                if reserved:
                    try:
                        conn = self._factory()
                    except Exception:
                        # Creation failed: give the reserved slot back.
                        with self._lock:
                            self._created -= 1
                        raise
                    return conn, time.time()

                # Wait a bit and retry
                time.sleep(0.1)

        raise TimeoutError(f"Failed to acquire connection within {self._timeout}s")

    def release(self, conn: Any, created_time: float) -> None:
        """Release a connection back to the pool.

        Args:
            conn: Connection object to release
            created_time: Time when connection was created
        """
        if self._validate(conn):
            self._pool.put((conn, created_time))
        else:
            # Connection invalid, don't return to pool
            with self._lock:
                self._created -= 1
            try:
                self._close_connection(conn)
            except Exception:
                pass

    def close_all(self) -> None:
        """Close all connections in the pool."""
        while not self._pool.empty():
            try:
                conn, _ = self._pool.get_nowait()
                self._close_connection(conn)
            except Exception:
                pass
        with self._lock:
            self._created = 0


def get_pool(
    pool_key: str,
    factory: Callable[[], Any],
    pool_config: dict[str, Any] | None = None,
) -> ConnectionPool:
    """Get or create a connection pool.

    Args:
        pool_key: Unique key identifying the pool (e.g., "postgres:postgresql://...")
        factory: Callable that creates a new connection
        pool_config: Optional pool configuration dict with keys:
            - min_size: Minimum pool size (default: 1)
            - max_size: Maximum pool size (default: 10)
            - timeout: Connection acquisition timeout in seconds (default: 30.0)
            - max_idle: Maximum idle time in seconds (default: 300.0)
            - validate: Optional connection validation function

    Returns:
        ConnectionPool instance
    """
    if pool_config is None:
        pool_config = {}

    with _pools_lock:
        if pool_key not in _pools:
            _pools[pool_key] = SimpleConnectionPool(
                factory,
                min_size=pool_config.get("min_size", 1),
                max_size=pool_config.get("max_size", 10),
                timeout=pool_config.get("timeout", 30.0),
                max_idle=pool_config.get("max_idle", 300.0),
                validate=pool_config.get("validate"),
            )
        return _pools[pool_key]


def close_pool(pool_key: str) -> None:
    """Close a specific connection pool.

    Args:
        pool_key: Key identifying the pool to close
    """
    with _pools_lock:
        if pool_key in _pools:
            _pools[pool_key].close_all()
            del _pools[pool_key]


def close_all_pools() -> None:
    """Close all connection pools."""
    with _pools_lock:
        for pool in _pools.values():
            pool.close_all()
        _pools.clear()


def get_pool_stats() -> dict[str, Any]:
    """Get statistics about all connection pools.

    Returns:
        Dictionary mapping pool keys to pool statistics
    """
    stats = {}
    with _pools_lock:
        for pool_key, pool in _pools.items():
            if isinstance(pool, SimpleConnectionPool):
                stats[pool_key] = {
                    "created": pool._created,
                    "available": pool._pool.qsize(),
                    "min_size": pool._min_size,
                    "max_size": pool._max_size,
                }
    return stats
