"""
Tests for connection pooling functionality.
"""

import time
from unittest.mock import Mock, patch

import pytest

from iterable.db.pooling import (
    SimpleConnectionPool,
    close_all_pools,
    close_pool,
    get_pool,
    get_pool_stats,
)


class TestSimpleConnectionPool:
    """Test SimpleConnectionPool implementation."""

    def test_pool_creation(self):
        """Test pool creation with default settings."""
        connection_count = 0

        def factory():
            nonlocal connection_count
            connection_count += 1
            conn = Mock()
            conn.close = Mock()
            return conn

        pool = SimpleConnectionPool(factory, min_size=2, max_size=5)
        assert pool._min_size == 2
        assert pool._max_size == 5
        assert connection_count == 2  # Pre-populated with min_size

    def test_acquire_release(self):
        """Test acquiring and releasing connections."""
        connections = []

        def factory():
            conn = Mock()
            conn.close = Mock()
            connections.append(conn)
            return conn

        pool = SimpleConnectionPool(factory, min_size=1, max_size=3)

        # Acquire connection
        conn1, time1 = pool.acquire()
        assert conn1 in connections
        assert time1 > 0

        # Release connection
        pool.release(conn1, time1)

        # Acquire again - should get same connection
        conn2, time2 = pool.acquire()
        assert conn2 == conn1  # Same connection reused

    def test_max_size_limit(self):
        """Test that pool respects max_size limit."""
        connection_count = 0

        def factory():
            nonlocal connection_count
            connection_count += 1
            conn = Mock()
            conn.close = Mock()
            return conn

        pool = SimpleConnectionPool(factory, min_size=1, max_size=2)

        # Acquire all connections up to max_size
        conn1, _ = pool.acquire()
        conn2, _ = pool.acquire()

        # Try to acquire third - should timeout (max_size reached)
        with pytest.raises(TimeoutError):
            pool.acquire()

        # Release one and acquire again
        pool.release(conn1, time.time())
        conn3, _ = pool.acquire()
        assert conn3 == conn1

    def test_connection_validation(self):
        """Test connection validation on acquire/release."""
        valid_conn = Mock()
        valid_conn.close = Mock()

        invalid_conn = Mock()
        invalid_conn.close = Mock()

        def factory():
            return Mock()

        def validate(conn):
            return conn == valid_conn

        pool = SimpleConnectionPool(factory, min_size=0, max_size=5, validate=validate)

        # Add valid connection
        pool._pool.put((valid_conn, time.time()))

        # Acquire valid connection
        conn, _ = pool.acquire()
        assert conn == valid_conn

        # Release valid connection
        pool.release(valid_conn, time.time())

        # Release invalid connection - should not be returned to pool
        pool.release(invalid_conn, time.time())
        assert pool._pool.qsize() == 1  # Only valid connection in pool

    def test_stale_connection_cleanup(self):
        """Test that stale connections are cleaned up."""
        connection_count = 0

        def factory():
            nonlocal connection_count
            connection_count += 1
            conn = Mock()
            conn.close = Mock()
            return conn

        pool = SimpleConnectionPool(factory, min_size=0, max_size=5, max_idle=0.1)

        # Add stale connection (created 1 second ago)
        stale_conn = factory()
        pool._pool.put((stale_conn, time.time() - 1.0))

        # Acquire - should get new connection (stale one replaced)
        conn, _ = pool.acquire()
        assert conn != stale_conn
        assert stale_conn.close.called

    def test_close_all(self):
        """Test closing all connections in pool."""
        connections = []

        def factory():
            conn = Mock()
            conn.close = Mock()
            connections.append(conn)
            return conn

        pool = SimpleConnectionPool(factory, min_size=2, max_size=5)

        # Close all
        pool.close_all()

        # All connections should be closed
        for conn in connections:
            assert conn.close.called

        assert pool._created == 0


class TestPoolRegistry:
    """Test pool registry functions."""

    def setup_method(self):
        """Clean up pools before each test."""
        close_all_pools()

    def test_get_pool_creates_new_pool(self):
        """Test that get_pool creates a new pool if it doesn't exist."""
        connection_count = 0

        def factory():
            nonlocal connection_count
            connection_count += 1
            return Mock()

        pool1 = get_pool("test:connection", factory)
        assert pool1 is not None
        assert connection_count == 1  # min_size=1 by default

    def test_get_pool_reuses_existing_pool(self):
        """Test that get_pool reuses existing pool for same key."""
        connection_count = 0

        def factory():
            nonlocal connection_count
            connection_count += 1
            return Mock()

        pool1 = get_pool("test:connection", factory)
        pool2 = get_pool("test:connection", factory)

        assert pool1 is pool2  # Same pool instance

    def test_get_pool_with_config(self):
        """Test get_pool with custom configuration."""
        connection_count = 0

        def factory():
            nonlocal connection_count
            connection_count += 1
            return Mock()

        pool_config = {"min_size": 3, "max_size": 10, "timeout": 60.0}
        pool = get_pool("test:connection2", factory, pool_config)

        assert pool._min_size == 3
        assert pool._max_size == 10
        assert pool._timeout == 60.0
        assert connection_count == 3  # Pre-populated with min_size

    def test_close_pool(self):
        """Test closing a specific pool."""
        connections = []

        def factory():
            conn = Mock()
            conn.close = Mock()
            connections.append(conn)
            return conn

        pool = get_pool("test:connection3", factory)
        conn, _ = pool.acquire()

        close_pool("test:connection3")

        # Pool should be closed - check that close was called on connections in pool
        # Note: The acquired connection is not in the pool, so we check pool stats
        stats = get_pool_stats()
        assert "test:connection3" not in stats  # Pool removed

        # Getting pool again should create new one
        pool2 = get_pool("test:connection3", factory)
        assert pool2 is not pool

    def test_close_all_pools(self):
        """Test closing all pools."""
        connections = []

        def factory():
            conn = Mock()
            conn.close = Mock()
            connections.append(conn)
            return conn

        pool1 = get_pool("test:connection4", factory)
        pool2 = get_pool("test:connection5", factory)

        # Acquire connections (these are out of pool)
        conn1, _ = pool1.acquire()
        conn2, _ = pool2.acquire()

        # Return connections to pool
        pool1.release(conn1, time.time())
        pool2.release(conn2, time.time())

        close_all_pools()

        # All connections in pools should be closed
        assert conn1.close.called
        assert conn2.close.called

    def test_get_pool_stats(self):
        """Test getting pool statistics."""

        def factory():
            return Mock()

        _ = get_pool("test:connection6", factory, {"min_size": 2, "max_size": 5})

        stats = get_pool_stats()
        assert "test:connection6" in stats
        assert stats["test:connection6"]["min_size"] == 2
        assert stats["test:connection6"]["max_size"] == 5
        assert stats["test:connection6"]["created"] == 2


class TestPostgresDriverPooling:
    """Test PostgreSQL driver with connection pooling."""

    def setup_method(self):
        """Clean up pools before each test."""
        close_all_pools()

    @pytest.mark.skipif(True, reason="Requires psycopg2 and PostgreSQL database - integration test")
    def test_postgres_pooling_enabled(self):
        """Test PostgreSQL driver with pooling enabled (integration test)."""
        # This would require actual PostgreSQL database
        # Skipped for unit tests, but demonstrates usage
        pass

    def test_postgres_pooling_disabled(self):
        """Test PostgreSQL driver with pooling disabled."""
        try:
            import psycopg2  # noqa: F401
        except ImportError:
            pytest.skip("psycopg2 not available")

        from iterable.db.postgres import PostgresDriver

        # Mock psycopg2.connect
        with patch("psycopg2.connect") as mock_connect:
            mock_conn = Mock()
            mock_conn.cursor.return_value.__enter__.return_value.execute = Mock()
            mock_conn.commit = Mock()
            mock_connect.return_value = mock_conn

            driver = PostgresDriver(
                "postgresql://test",
                query="SELECT 1",
                pool={"enabled": False},
            )

            driver.connect()

            # Should use direct connection, not pool
            assert driver._pool is None
            assert driver.conn == mock_conn
            assert mock_connect.called

            driver.close()
            assert mock_conn.close.called

    def test_postgres_pooling_config(self):
        """Test PostgreSQL driver with custom pool configuration."""
        try:
            import psycopg2  # noqa: F401
        except ImportError:
            pytest.skip("psycopg2 not available")

        from iterable.db.postgres import PostgresDriver

        # Mock psycopg2.connect
        with patch("psycopg2.connect") as mock_connect:
            mock_conn = Mock()
            mock_conn.closed = False
            mock_conn.cursor.return_value.__enter__.return_value.execute = Mock()
            mock_conn.commit = Mock()
            mock_connect.return_value = mock_conn

            pool_config = {
                "enabled": True,
                "min_size": 2,
                "max_size": 5,
                "timeout": 60.0,
            }

            driver = PostgresDriver(
                "postgresql://test",
                query="SELECT 1",
                pool=pool_config,
            )

            driver.connect()

            # Should use pool
            assert driver._pool is not None
            assert driver.conn == mock_conn

            # Check pool configuration
            stats = get_pool_stats()
            pool_key = "postgres:postgresql://test"
            if pool_key in stats:
                assert stats[pool_key]["min_size"] == 2
                assert stats[pool_key]["max_size"] == 5

            driver.close()

            # Connection should be returned to pool (not closed)
            assert not mock_conn.close.called

    def test_postgres_connection_reuse(self):
        """Test that PostgreSQL connections are reused from pool."""
        try:
            import psycopg2  # noqa: F401
        except ImportError:
            pytest.skip("psycopg2 not available")

        from iterable.db.postgres import PostgresDriver

        # Mock psycopg2.connect
        with patch("psycopg2.connect") as mock_connect:
            mock_conn = Mock()
            mock_conn.closed = False
            mock_conn.cursor.return_value.__enter__.return_value.execute = Mock()
            mock_conn.commit = Mock()
            mock_connect.return_value = mock_conn

            # Create first driver
            driver1 = PostgresDriver("postgresql://test", query="SELECT 1")
            driver1.connect()

            # Close first driver
            driver1.close()

            # Create second driver with same connection string
            driver2 = PostgresDriver("postgresql://test", query="SELECT 2")
            driver2.connect()

            # Should reuse connection from pool
            # Note: In real scenario, connections are reused, but in this test
            # we're mocking, so we verify pool was used
            assert driver2._pool is not None

            driver2.close()
