"""
Tests for database engine support.

Tests database drivers, integration with open_iterable(), convert(), and pipeline().
"""

from __future__ import annotations

import os
from collections.abc import Iterator
from unittest.mock import MagicMock, patch

import pytest

import iterable.db.clickhouse as clickhouse_mod
import iterable.db.elasticsearch as elasticsearch_mod
import iterable.db.mongo as mongo_mod
import iterable.db.mssql as mssql_mod
import iterable.db.mysql as mysql_mod
import iterable.db.postgres as postgres_mod
from iterable.db import get_driver, is_database_engine, list_drivers, register_driver
from iterable.db.base import DBDriver
from iterable.db.iterable import DatabaseIterable
from iterable.db.postgres import PostgresDriver

try:
    from iterable.db.clickhouse import ClickHouseDriver
except ImportError:
    ClickHouseDriver = None  # type: ignore

try:
    from iterable.db.mysql import MySQLDriver
except ImportError:
    MySQLDriver = None  # type: ignore

try:
    from iterable.db.mssql import MSSQLDriver
except ImportError:
    MSSQLDriver = None  # type: ignore

try:
    from iterable.db.sqlite import SQLiteDriver
except ImportError:
    SQLiteDriver = None  # type: ignore

try:
    from iterable.db.mongo import MongoDriver
except ImportError:
    MongoDriver = None  # type: ignore

try:
    from iterable.db.elasticsearch import ElasticsearchDriver
except ImportError:
    ElasticsearchDriver = None  # type: ignore


def _close_iterables_and_unlink(path: str, *iterables: object) -> None:
    """Close write handles before deleting so Windows can unlink the temp file."""
    for obj in iterables:
        closer = getattr(obj, "close", None)
        if closer is None:
            continue
        try:
            closer()
        except Exception:
            pass
    if os.path.exists(path):
        try:
            os.unlink(path)
        except OSError:
            pass


class TestPostgresDriver:
    """Test PostgreSQL driver implementation."""

    def test_connect_with_connection_string(self):
        """Test connection with connection string."""
        with patch.object(postgres_mod, "psycopg2") as mock_psycopg2:
            mock_conn = MagicMock()
            mock_psycopg2.connect.return_value = mock_conn

            # Disable pooling so the connection is created directly and once.
            driver = PostgresDriver("postgresql://user:pass@localhost/db", query="SELECT 1", pool={"enabled": False})
            driver.connect()

            assert driver.is_connected
            assert driver.conn == mock_conn
            mock_psycopg2.connect.assert_called_with("postgresql://user:pass@localhost/db", **{})
            assert mock_psycopg2.connect.call_count >= 1

    def test_connect_with_existing_connection(self):
        """Test connection with existing connection object."""
        mock_conn = MagicMock()
        mock_conn.cursor = MagicMock()
        mock_conn.close = MagicMock()

        driver = PostgresDriver(mock_conn, query="SELECT 1")
        driver.connect()

        assert driver.is_connected
        assert driver.conn == mock_conn

    def test_connect_import_error(self):
        """Test ImportError when psycopg2 not installed."""
        with patch.dict("sys.modules", {"psycopg2": None}):
            # Force reimport to trigger ImportError
            import sys

            if "iterable.db.postgres" in sys.modules:
                del sys.modules["iterable.db.postgres"]

            from iterable.db.postgres import PostgresDriver

            driver = PostgresDriver("postgresql://localhost/db", query="SELECT 1")
            with pytest.raises(ImportError, match="psycopg2-binary is required"):
                driver.connect()

    def test_connect_with_connect_args(self):
        """Test connection with additional connect_args."""
        with patch.object(postgres_mod, "psycopg2") as mock_psycopg2:
            mock_conn = MagicMock()
            mock_psycopg2.connect.return_value = mock_conn
            mock_cursor = MagicMock()
            mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

            driver = PostgresDriver(
                "postgresql://localhost/db",
                query="SELECT 1",
                connect_args={"sslmode": "require"},
                pool={"enabled": False},
            )
            driver.connect()

            mock_psycopg2.connect.assert_called_once_with("postgresql://localhost/db", sslmode="require")

    def test_read_only_transaction(self):
        """Test read-only transaction is set."""
        with patch.object(postgres_mod, "psycopg2") as mock_psycopg2:
            isolation_level = mock_psycopg2.extensions.ISOLATION_LEVEL_READ_COMMITTED

            mock_conn = MagicMock()
            mock_psycopg2.connect.return_value = mock_conn
            mock_cursor = MagicMock()
            mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

            # Disable pooling so the connection is created directly and once.
            driver = PostgresDriver(
                "postgresql://localhost/db", query="SELECT 1", read_only=True, pool={"enabled": False}
            )
            driver.connect()

            mock_conn.set_isolation_level.assert_called_once_with(isolation_level)
            mock_conn.cursor.assert_called()
            mock_conn.commit.assert_called_once()

    def test_build_query_from_table_name(self):
        """Test auto-building SELECT query from table name."""
        driver = PostgresDriver("postgresql://localhost/db", query="users")
        query = driver._build_query()
        assert query == 'SELECT * FROM "users"'

    def test_build_query_with_schema(self):
        """Test query building with schema."""
        driver = PostgresDriver("postgresql://localhost/db", query="users", schema="public")
        query = driver._build_query()
        assert query == 'SELECT * FROM "public"."users"'

    def test_build_query_with_columns(self):
        """Test query building with column projection."""
        driver = PostgresDriver("postgresql://localhost/db", query="users", columns=["id", "name"])
        query = driver._build_query()
        assert '"id"' in query
        assert '"name"' in query
        assert "*" not in query

    def test_build_query_with_filter(self):
        """Test query building with WHERE clause."""
        driver = PostgresDriver("postgresql://localhost/db", query="users", filter="active = TRUE")
        query = driver._build_query()
        assert "WHERE active = TRUE" in query

    def test_build_query_with_sql_string(self):
        """Test query building with SQL string."""
        sql = "SELECT id, name FROM users WHERE age > 18"
        driver = PostgresDriver("postgresql://localhost/db", query=sql)
        query = driver._build_query()
        assert query == sql

    def test_quote_identifier(self):
        """Test identifier quoting."""
        driver = PostgresDriver("postgresql://localhost/db", query="test")
        assert driver._quote_identifier("user") == '"user"'
        assert driver._quote_identifier('user"name') == '"user""name"'

    def test_iterate_with_server_side_cursor(self):
        """Test streaming iteration with server-side cursor."""
        with patch.object(postgres_mod, "psycopg2") as mock_psycopg2:
            mock_conn = MagicMock()
            mock_psycopg2.connect.return_value = mock_conn
            mock_cursor = MagicMock()
            mock_cursor.description = [("id",), ("name",)]
            mock_cursor.fetchmany.side_effect = [
                [(1, "Alice"), (2, "Bob")],
                [],
            ]
            mock_conn.cursor.return_value = mock_cursor

            driver = PostgresDriver("postgresql://localhost/db", query="users", batch_size=2)
            driver.connect()

            rows = list(driver.iterate())
            assert len(rows) == 2
            assert rows[0] == {"id": 1, "name": "Alice"}
            assert rows[1] == {"id": 2, "name": "Bob"}
            assert mock_cursor.itersize == 2
            mock_cursor.execute.assert_called_once()

    def test_iterate_with_regular_cursor(self):
        """Test iteration with regular cursor (no server-side)."""
        with patch.object(postgres_mod, "psycopg2") as mock_psycopg2:
            mock_conn = MagicMock()
            mock_psycopg2.connect.return_value = mock_conn
            mock_cursor = MagicMock()
            mock_cursor.description = [("id",), ("name",)]
            mock_cursor.__iter__.return_value = iter([(1, "Alice"), (2, "Bob")])
            mock_conn.cursor.return_value = mock_cursor

            driver = PostgresDriver("postgresql://localhost/db", query="users", server_side_cursor=False)
            driver.connect()

            rows = list(driver.iterate())
            assert len(rows) == 2
            assert rows[0] == {"id": 1, "name": "Alice"}
            assert rows[1] == {"id": 2, "name": "Bob"}

    def test_iterate_empty_result_set(self):
        """Test iteration with empty result set."""
        with patch.object(postgres_mod, "psycopg2") as mock_psycopg2:
            mock_conn = MagicMock()
            mock_psycopg2.connect.return_value = mock_conn
            mock_cursor = MagicMock()
            mock_cursor.description = [("id",)]
            mock_cursor.fetchmany.return_value = []
            mock_conn.cursor.return_value = mock_cursor

            driver = PostgresDriver("postgresql://localhost/db", query="users")
            driver.connect()

            rows = list(driver.iterate())
            assert len(rows) == 0

    def test_iterate_no_columns(self):
        """Test iteration with no column description."""
        with patch.object(postgres_mod, "psycopg2") as mock_psycopg2:
            mock_conn = MagicMock()
            mock_psycopg2.connect.return_value = mock_conn
            mock_cursor = MagicMock()
            mock_cursor.description = None
            mock_cursor.fetchmany.side_effect = [[()], []]
            mock_conn.cursor.return_value = mock_cursor

            driver = PostgresDriver("postgresql://localhost/db", query="INSERT INTO users VALUES (1)")
            driver.connect()

            rows = list(driver.iterate())
            assert len(rows) == 1
            assert rows[0] == {}

    def test_metrics_tracking(self):
        """Test metrics are tracked during iteration."""
        with patch.object(postgres_mod, "psycopg2") as mock_psycopg2:
            mock_conn = MagicMock()
            mock_psycopg2.connect.return_value = mock_conn
            mock_cursor = MagicMock()
            mock_cursor.description = [("id",)]
            mock_cursor.fetchmany.side_effect = [
                [(1,), (2,), (3,)],
                [],
            ]
            mock_conn.cursor.return_value = mock_cursor

            driver = PostgresDriver("postgresql://localhost/db", query="users")
            driver.connect()

            list(driver.iterate())
            metrics = driver.metrics
            assert metrics["rows_read"] == 3
            assert metrics["elapsed_seconds"] >= 0

    def test_list_tables(self):
        """Test list_tables() helper function."""
        with patch.object(postgres_mod, "psycopg2") as mock_psycopg2:
            mock_conn = MagicMock()
            mock_psycopg2.connect.return_value = mock_conn
            mock_cursor = MagicMock()
            mock_cursor.fetchall.return_value = [
                ("public", "users", 1000),
                ("public", "orders", 500),
            ]
            mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

            tables = PostgresDriver.list_tables("postgresql://localhost/db")
            assert len(tables) == 2
            assert tables[0]["schema"] == "public"
            assert tables[0]["table"] == "users"
            assert tables[0]["row_count"] == 1000

    def test_list_tables_with_schema(self):
        """Test list_tables() with schema filter."""
        with patch.object(postgres_mod, "psycopg2") as mock_psycopg2:
            mock_conn = MagicMock()
            mock_psycopg2.connect.return_value = mock_conn
            mock_cursor = MagicMock()
            mock_cursor.fetchall.return_value = [("test", "users", 100)]
            mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

            tables = PostgresDriver.list_tables("postgresql://localhost/db", schema="test")
            assert len(tables) == 1
            assert tables[0]["schema"] == "test"

    def test_error_handling_raise(self):
        """Test error handling with 'raise' policy."""
        with patch.object(postgres_mod, "psycopg2") as mock_psycopg2:
            mock_conn = MagicMock()
            mock_psycopg2.connect.return_value = mock_conn
            mock_cursor = MagicMock()
            mock_cursor.execute.side_effect = Exception("SQL error")
            mock_conn.cursor.return_value = mock_cursor

            driver = PostgresDriver("postgresql://localhost/db", query="INVALID SQL", on_error="raise")
            driver.connect()

            with pytest.raises(Exception, match="SQL error"):
                list(driver.iterate())

    def test_error_handling_skip(self):
        """Test error handling with 'skip' policy."""
        with patch.object(postgres_mod, "psycopg2") as mock_psycopg2:
            mock_conn = MagicMock()
            mock_psycopg2.connect.return_value = mock_conn
            mock_cursor = MagicMock()
            mock_cursor.execute.side_effect = Exception("SQL error")
            mock_conn.cursor.return_value = mock_cursor

            driver = PostgresDriver("postgresql://localhost/db", query="INVALID SQL", on_error="skip")
            driver.connect()

            rows = list(driver.iterate())
            assert len(rows) == 0  # Error skipped, no rows returned

    def test_close_cleans_up_cursor(self):
        """Test close() cleans up cursor."""
        with patch.object(postgres_mod, "psycopg2") as mock_psycopg2:
            mock_conn = MagicMock()
            mock_psycopg2.connect.return_value = mock_conn
            mock_cursor = MagicMock()
            mock_conn.cursor.return_value = mock_cursor

            driver = PostgresDriver("postgresql://localhost/db", query="users")
            driver.connect()
            driver._cursor = mock_cursor
            driver.close()

            mock_cursor.close.assert_called_once()
            mock_conn.close.assert_called_once()


class TestDatabaseIterable:
    """Test DatabaseIterable wrapper."""

    def test_read_single_row(self):
        """Test reading single row."""
        mock_driver = MagicMock(spec=DBDriver)
        mock_driver.is_connected = True
        mock_driver.iterate.return_value = iter([{"id": 1, "name": "test"}])
        mock_driver._start_metrics = MagicMock()

        iterable = DatabaseIterable(mock_driver)
        row = iterable.read()

        assert row == {"id": 1, "name": "test"}
        mock_driver.iterate.assert_called_once()

    def test_read_bulk(self):
        """Test reading multiple rows."""
        mock_driver = MagicMock(spec=DBDriver)
        mock_driver.is_connected = True
        mock_driver.iterate.return_value = iter([{"id": i} for i in range(5)])
        mock_driver._start_metrics = MagicMock()

        iterable = DatabaseIterable(mock_driver)
        rows = iterable.read_bulk(3)

        assert len(rows) == 3
        assert rows[0] == {"id": 0}
        assert rows[1] == {"id": 1}
        assert rows[2] == {"id": 2}

    def test_reset_not_supported(self):
        """Test reset() raises NotImplementedError."""
        mock_driver = MagicMock(spec=DBDriver)
        iterable = DatabaseIterable(mock_driver)

        with pytest.raises(NotImplementedError, match="Reset is not supported"):
            iterable.reset()

    def test_close(self):
        """Test close() closes driver."""
        mock_driver = MagicMock(spec=DBDriver)
        iterable = DatabaseIterable(mock_driver)
        iterable._iterator = iter([{"id": 1}])

        iterable.close()

        mock_driver.close.assert_called_once()
        assert iterable._iterator is None

    def test_context_manager(self):
        """Test context manager usage."""
        mock_driver = MagicMock(spec=DBDriver)
        iterable = DatabaseIterable(mock_driver)

        with iterable:
            pass

        mock_driver.close.assert_called_once()

    def test_metrics_property(self):
        """Test metrics property delegates to driver."""
        mock_driver = MagicMock(spec=DBDriver)
        mock_driver.metrics = {"rows_read": 10, "elapsed_seconds": 1.5}
        iterable = DatabaseIterable(mock_driver)

        metrics = iterable.metrics
        assert metrics == {"rows_read": 10, "elapsed_seconds": 1.5}

    def test_is_streaming(self):
        """Test is_streaming() returns True."""
        mock_driver = MagicMock(spec=DBDriver)
        iterable = DatabaseIterable(mock_driver)
        assert iterable.is_streaming() is True

    def test_is_flat(self):
        """Test is_flat() returns True."""
        mock_driver = MagicMock(spec=DBDriver)
        iterable = DatabaseIterable(mock_driver)
        assert iterable.is_flat() is True


class TestDriverRegistry:
    """Test driver registry functionality."""

    def test_register_driver(self):
        """Test registering a driver."""

        # Create a mock driver class
        class MockDriver(DBDriver):
            def connect(self):
                pass

            def iterate(self) -> Iterator:
                yield {}

        register_driver("mock", MockDriver)
        assert get_driver("mock") == MockDriver

    def test_get_driver(self):
        """Test getting a registered driver."""
        driver_class = get_driver("postgres")
        # Should return PostgresDriver if psycopg2 is available, None otherwise
        assert driver_class is None or driver_class == PostgresDriver

    def test_list_drivers(self):
        """Test listing registered drivers."""
        drivers = list_drivers()
        assert isinstance(drivers, list)
        # May include postgres if psycopg2 is installed

    def test_is_database_engine(self):
        """Test checking if engine is a database engine."""

        # Register a test driver
        class TestDriver(DBDriver):
            def connect(self):
                pass

            def iterate(self) -> Iterator:
                yield {}

        register_driver("testdb", TestDriver)
        assert is_database_engine("testdb") is True
        assert is_database_engine("internal") is False
        assert is_database_engine("duckdb") is False


class TestOpenIterableIntegration:
    """Test integration with open_iterable()."""

    def test_open_iterable_with_postgres_engine(self):
        """Test open_iterable() with postgres engine."""
        with patch("iterable.helpers.detect.get_driver") as mock_get_driver:
            with patch("iterable.helpers.detect.PostgresDriver") as mock_postgres_driver_class:
                mock_driver = MagicMock()
                mock_postgres_driver_class.return_value = mock_driver
                mock_get_driver.return_value = mock_postgres_driver_class

                from iterable.helpers.detect import open_iterable

                iterable = open_iterable(
                    "postgresql://localhost/db",
                    engine="postgres",
                    iterableargs={"query": "users"},
                )

                assert isinstance(iterable, DatabaseIterable)
                mock_postgres_driver_class.assert_called_once()

    def test_open_iterable_database_engine_not_available(self):
        """Test open_iterable() when database engine is not available."""
        with patch("iterable.helpers.detect.get_driver") as mock_get_driver:
            mock_get_driver.return_value = None

            from iterable.helpers.detect import open_iterable

            with pytest.raises(ValueError, match="is not available"):
                open_iterable("postgresql://localhost/db", engine="postgres", iterableargs={"query": "users"})

    @pytest.mark.skipif(ClickHouseDriver is None, reason="clickhouse-connect not installed")
    def test_open_iterable_with_clickhouse_engine(self):
        """Test open_iterable() with clickhouse engine."""
        with patch("iterable.helpers.detect.get_driver") as mock_get_driver:
            with patch("iterable.helpers.detect.ClickHouseDriver") as mock_clickhouse_driver_class:
                mock_driver = MagicMock()
                mock_clickhouse_driver_class.return_value = mock_driver
                mock_get_driver.return_value = mock_clickhouse_driver_class

                from iterable.helpers.detect import open_iterable

                iterable = open_iterable(
                    "clickhouse://localhost/db",
                    engine="clickhouse",
                    iterableargs={"query": "events"},
                )

                assert isinstance(iterable, DatabaseIterable)
                mock_clickhouse_driver_class.assert_called_once()

    @pytest.mark.skipif(ClickHouseDriver is None, reason="clickhouse-connect not installed")
    def test_open_iterable_clickhouse_context_manager(self):
        """Test open_iterable() with ClickHouse engine using context manager."""
        with patch("iterable.helpers.detect.get_driver") as mock_get_driver:
            with patch("iterable.helpers.detect.ClickHouseDriver") as mock_clickhouse_driver_class:
                mock_driver = MagicMock()
                mock_driver.is_connected = True
                mock_driver.iterate.return_value = iter([{"id": 1, "name": "test"}])
                mock_driver._start_metrics = MagicMock()
                mock_clickhouse_driver_class.return_value = mock_driver
                mock_get_driver.return_value = mock_clickhouse_driver_class

                from iterable.helpers.detect import open_iterable

                with open_iterable(
                    "clickhouse://localhost/db",
                    engine="clickhouse",
                    iterableargs={"query": "events"},
                ) as iterable:
                    row = iterable.read()
                    assert row == {"id": 1, "name": "test"}

                mock_driver.close.assert_called_once()

    @pytest.mark.skipif(ClickHouseDriver is None, reason="clickhouse-connect not installed")
    def test_open_iterable_clickhouse_metrics(self):
        """Test metrics tracking with ClickHouse engine."""
        with patch("iterable.helpers.detect.get_driver") as mock_get_driver:
            with patch("iterable.helpers.detect.ClickHouseDriver") as mock_clickhouse_driver_class:
                mock_driver = MagicMock()
                mock_driver.is_connected = True
                mock_driver.iterate.return_value = iter([{"id": 1}, {"id": 2}])
                mock_driver._start_metrics = MagicMock()
                mock_clickhouse_driver_class.return_value = mock_driver
                mock_get_driver.return_value = mock_clickhouse_driver_class

                from iterable.helpers.detect import open_iterable

                iterable = open_iterable(
                    "clickhouse://localhost/db",
                    engine="clickhouse",
                    iterableargs={"query": "events"},
                )
                rows = list(iterable)
                assert len(rows) == 2
                mock_driver._start_metrics.assert_called_once()

    @pytest.mark.skipif(ClickHouseDriver is None, reason="clickhouse-connect not installed")
    def test_open_iterable_clickhouse_error_handling(self):
        """Test error handling with ClickHouse engine."""
        with patch("iterable.helpers.detect.get_driver") as mock_get_driver:
            with patch("iterable.helpers.detect.ClickHouseDriver") as mock_clickhouse_driver_class:
                mock_driver = MagicMock()
                mock_driver.is_connected = False
                mock_driver.connect.side_effect = ConnectionError("Connection refused")
                mock_clickhouse_driver_class.return_value = mock_driver
                mock_get_driver.return_value = mock_clickhouse_driver_class

                from iterable.helpers.detect import open_iterable

                iterable = open_iterable(
                    "clickhouse://localhost/db",
                    engine="clickhouse",
                    iterableargs={"query": "events"},
                )
                with pytest.raises(ConnectionError, match="Connection refused"):
                    iterable.read()


class TestConvertIntegration:
    """Test integration with convert()."""

    def test_convert_from_database_to_file(self):
        """Test convert() from database source to file."""
        with patch("iterable.helpers.detect.get_driver") as mock_get_driver:
            with patch("iterable.helpers.detect.PostgresDriver") as mock_postgres_driver_class:
                mock_driver = MagicMock()
                mock_driver.is_connected = True
                mock_driver.iterate.return_value = iter([{"id": 1, "name": "test"}])
                mock_driver._start_metrics = MagicMock()
                mock_postgres_driver_class.return_value = mock_driver
                mock_get_driver.return_value = mock_postgres_driver_class

                import os
                import tempfile

                from iterable.convert import convert

                with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as tmp:
                    tmp_path = tmp.name

                try:
                    convert(
                        fromfile="postgresql://localhost/db",
                        tofile=tmp_path,
                        iterableargs={"engine": "postgres", "query": "users"},
                    )

                    assert os.path.exists(tmp_path)
                    with open(tmp_path) as f:
                        content = f.read()
                        assert "test" in content
                finally:
                    if os.path.exists(tmp_path):
                        os.unlink(tmp_path)

    @pytest.mark.skipif(ClickHouseDriver is None, reason="clickhouse-connect not installed")
    def test_convert_from_clickhouse_to_file(self):
        """Test convert() from ClickHouse source to file."""
        with patch("iterable.helpers.detect.get_driver") as mock_get_driver:
            with patch("iterable.helpers.detect.ClickHouseDriver") as mock_clickhouse_driver_class:
                mock_driver = MagicMock()
                mock_driver.is_connected = True
                mock_driver.iterate.return_value = iter([{"id": 1, "name": "test"}])
                mock_driver._start_metrics = MagicMock()
                mock_clickhouse_driver_class.return_value = mock_driver
                mock_get_driver.return_value = mock_clickhouse_driver_class

                import os
                import tempfile

                from iterable.convert import convert

                with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as tmp:
                    tmp_path = tmp.name

                try:
                    convert(
                        fromfile="clickhouse://localhost/db",
                        tofile=tmp_path,
                        iterableargs={"engine": "clickhouse", "query": "events"},
                    )

                    assert os.path.exists(tmp_path)
                    with open(tmp_path) as f:
                        content = f.read()
                        assert "test" in content
                finally:
                    if os.path.exists(tmp_path):
                        os.unlink(tmp_path)

    @pytest.mark.skipif(ClickHouseDriver is None, reason="clickhouse-connect not installed")
    def test_convert_from_clickhouse_to_parquet(self):
        """Test convert() from ClickHouse source to Parquet."""
        pytest.importorskip("pyarrow", reason="pyarrow is required for Parquet support")
        with patch("iterable.helpers.detect.get_driver") as mock_get_driver:
            with patch("iterable.helpers.detect.ClickHouseDriver") as mock_clickhouse_driver_class:
                mock_driver = MagicMock()
                mock_driver.is_connected = True
                mock_driver.iterate.return_value = iter([{"id": 1, "name": "test"}])
                mock_driver._start_metrics = MagicMock()
                mock_clickhouse_driver_class.return_value = mock_driver
                mock_get_driver.return_value = mock_clickhouse_driver_class

                import os
                import tempfile

                from iterable.convert import convert

                with tempfile.NamedTemporaryFile(suffix=".parquet", delete=False) as tmp:
                    tmp_path = tmp.name

                try:
                    convert(
                        fromfile="clickhouse://localhost/db",
                        tofile=tmp_path,
                        iterableargs={"engine": "clickhouse", "query": "events"},
                    )

                    assert os.path.exists(tmp_path)
                finally:
                    if os.path.exists(tmp_path):
                        os.unlink(tmp_path)


class TestPipelineIntegration:
    """Test integration with pipeline()."""

    def test_pipeline_with_database_source(self):
        """Test pipeline() with database source."""
        with patch("iterable.helpers.detect.get_driver") as mock_get_driver:
            with patch("iterable.helpers.detect.PostgresDriver") as mock_postgres_driver_class:
                mock_driver = MagicMock()
                mock_driver.is_connected = True
                mock_driver.iterate.return_value = iter([{"id": 1, "name": "test"}])
                mock_driver._start_metrics = MagicMock()
                mock_postgres_driver_class.return_value = mock_driver
                mock_get_driver.return_value = mock_postgres_driver_class

                import tempfile

                from iterable.helpers.detect import open_iterable
                from iterable.pipeline import Pipeline

                with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as tmp:
                    tmp_path = tmp.name

                source = None
                dest = None
                try:
                    source = open_iterable(
                        "postgresql://localhost/db",
                        engine="postgres",
                        iterableargs={"query": "users"},
                    )
                    dest = open_iterable(tmp_path, mode="w")

                    pipeline = Pipeline(source, dest)
                    result = pipeline.run()

                    assert result.rows_processed > 0
                finally:
                    _close_iterables_and_unlink(tmp_path, dest, source)

    @pytest.mark.skipif(ClickHouseDriver is None, reason="clickhouse-connect not installed")
    def test_pipeline_with_clickhouse_source(self):
        """Test pipeline() with ClickHouse source."""
        with patch("iterable.helpers.detect.get_driver") as mock_get_driver:
            with patch("iterable.helpers.detect.ClickHouseDriver") as mock_clickhouse_driver_class:
                mock_driver = MagicMock()
                mock_driver.is_connected = True
                mock_driver.iterate.return_value = iter([{"id": 1, "name": "test"}])
                mock_driver._start_metrics = MagicMock()
                mock_clickhouse_driver_class.return_value = mock_driver
                mock_get_driver.return_value = mock_clickhouse_driver_class

                import tempfile

                from iterable.helpers.detect import open_iterable
                from iterable.pipeline import Pipeline

                with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as tmp:
                    tmp_path = tmp.name

                source = None
                dest = None
                try:
                    source = open_iterable(
                        "clickhouse://localhost/db",
                        engine="clickhouse",
                        iterableargs={"query": "events"},
                    )
                    dest = open_iterable(tmp_path, mode="w")

                    pipeline = Pipeline(source, dest)
                    result = pipeline.run()

                    assert result.rows_processed > 0
                finally:
                    _close_iterables_and_unlink(tmp_path, dest, source)

    @pytest.mark.skipif(ClickHouseDriver is None, reason="clickhouse-connect not installed")
    def test_pipeline_clickhouse_streaming(self):
        """Test pipeline() with ClickHouse source streaming behavior."""
        with patch("iterable.helpers.detect.get_driver") as mock_get_driver:
            with patch("iterable.helpers.detect.ClickHouseDriver") as mock_clickhouse_driver_class:
                mock_driver = MagicMock()
                mock_driver.is_connected = True
                mock_driver.iterate.return_value = iter([{"id": i} for i in range(10)])
                mock_driver._start_metrics = MagicMock()
                mock_clickhouse_driver_class.return_value = mock_driver
                mock_get_driver.return_value = mock_clickhouse_driver_class

                import tempfile

                from iterable.helpers.detect import open_iterable
                from iterable.pipeline import Pipeline

                with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as tmp:
                    tmp_path = tmp.name

                source = None
                dest = None
                try:
                    source = open_iterable(
                        "clickhouse://localhost/db",
                        engine="clickhouse",
                        iterableargs={"query": "events", "batch_size": 5},
                    )
                    dest = open_iterable(tmp_path, mode="w")

                    pipeline = Pipeline(source, dest)
                    result = pipeline.run()

                    assert result.rows_processed == 10
                finally:
                    _close_iterables_and_unlink(tmp_path, dest, source)

    @pytest.mark.skipif(ClickHouseDriver is None, reason="clickhouse-connect not installed")
    def test_pipeline_clickhouse_error_handling(self):
        """Test pipeline() error handling with ClickHouse source."""
        with patch("iterable.helpers.detect.get_driver") as mock_get_driver:
            with patch("iterable.helpers.detect.ClickHouseDriver") as mock_clickhouse_driver_class:
                mock_driver = MagicMock()
                mock_driver.is_connected = True
                mock_driver.iterate.side_effect = RuntimeError("Query failed")
                mock_driver._start_metrics = MagicMock()
                mock_clickhouse_driver_class.return_value = mock_driver
                mock_get_driver.return_value = mock_clickhouse_driver_class

                import tempfile

                from iterable.helpers.detect import open_iterable
                from iterable.pipeline import Pipeline

                with tempfile.NamedTemporaryFile(mode="w", suffix=".jsonl", delete=False) as tmp:
                    tmp_path = tmp.name

                source = None
                dest = None
                try:
                    source = open_iterable(
                        "clickhouse://localhost/db",
                        engine="clickhouse",
                        iterableargs={"query": "events", "on_error": "raise"},
                    )
                    dest = open_iterable(tmp_path, mode="w")

                    pipeline = Pipeline(source, dest)
                    with pytest.raises(RuntimeError, match="Query failed"):
                        pipeline.run()
                finally:
                    _close_iterables_and_unlink(tmp_path, dest, source)


class TestDataFrameBridges:
    """Test DataFrame bridge methods with database sources."""

    def test_to_pandas(self):
        """Test .to_pandas() with database source."""
        mock_driver = MagicMock(spec=DBDriver)
        mock_driver.is_connected = True
        mock_driver.iterate.return_value = iter([{"id": 1, "name": "test"}])
        mock_driver._start_metrics = MagicMock()

        iterable = DatabaseIterable(mock_driver)

        try:
            df = iterable.to_pandas()
            assert len(df) == 1
            assert "id" in df.columns
            assert "name" in df.columns
        except ImportError:
            pytest.skip("pandas not installed")

    def test_to_pandas_chunked(self):
        """Test .to_pandas() with chunksize."""
        mock_driver = MagicMock(spec=DBDriver)
        mock_driver.is_connected = True
        mock_driver.iterate.return_value = iter([{"id": i} for i in range(5)])
        mock_driver._start_metrics = MagicMock()

        iterable = DatabaseIterable(mock_driver)

        try:
            chunks = iterable.to_pandas(chunksize=2)
            chunk_list = list(chunks)
            assert len(chunk_list) == 3  # 2, 2, 1
            assert len(chunk_list[0]) == 2
        except ImportError:
            pytest.skip("pandas not installed")

    def test_to_polars(self):
        """Test .to_polars() with database source."""
        mock_driver = MagicMock(spec=DBDriver)
        mock_driver.is_connected = True
        mock_driver.iterate.return_value = iter([{"id": 1, "name": "test"}])
        mock_driver._start_metrics = MagicMock()

        iterable = DatabaseIterable(mock_driver)

        try:
            df = iterable.to_polars()
            assert len(df) == 1
            assert "id" in df.columns
            assert "name" in df.columns
        except ImportError:
            pytest.skip("polars not installed")

    def test_to_dask(self):
        """Test .to_dask() with database source."""
        mock_driver = MagicMock(spec=DBDriver)
        mock_driver.is_connected = True
        mock_driver.iterate.return_value = iter([{"id": 1, "name": "test"}])
        mock_driver._start_metrics = MagicMock()

        iterable = DatabaseIterable(mock_driver)

        try:
            df = iterable.to_dask()
            assert len(df) == 1
            assert "id" in df.columns
            assert "name" in df.columns
        except ImportError:
            pytest.skip("dask not installed")

    @pytest.mark.skipif(ClickHouseDriver is None, reason="clickhouse-connect not installed")
    def test_to_pandas_with_clickhouse(self):
        """Test .to_pandas() with ClickHouse source."""
        with patch("iterable.helpers.detect.get_driver") as mock_get_driver:
            with patch("iterable.helpers.detect.ClickHouseDriver") as mock_clickhouse_driver_class:
                mock_driver = MagicMock()
                mock_driver.is_connected = True
                mock_driver.iterate.return_value = iter([{"id": 1, "name": "test"}])
                mock_driver._start_metrics = MagicMock()
                mock_clickhouse_driver_class.return_value = mock_driver
                mock_get_driver.return_value = mock_clickhouse_driver_class

                from iterable.helpers.detect import open_iterable

                iterable = open_iterable(
                    "clickhouse://localhost/db",
                    engine="clickhouse",
                    iterableargs={"query": "events"},
                )

                try:
                    df = iterable.to_pandas()
                    assert len(df) == 1
                    assert "id" in df.columns
                    assert "name" in df.columns
                except ImportError:
                    pytest.skip("pandas not installed")

    @pytest.mark.skipif(ClickHouseDriver is None, reason="clickhouse-connect not installed")
    def test_to_pandas_chunked_with_clickhouse(self):
        """Test .to_pandas() with chunksize for ClickHouse source."""
        with patch("iterable.helpers.detect.get_driver") as mock_get_driver:
            with patch("iterable.helpers.detect.ClickHouseDriver") as mock_clickhouse_driver_class:
                mock_driver = MagicMock()
                mock_driver.is_connected = True
                mock_driver.iterate.return_value = iter([{"id": i} for i in range(5)])
                mock_driver._start_metrics = MagicMock()
                mock_clickhouse_driver_class.return_value = mock_driver
                mock_get_driver.return_value = mock_clickhouse_driver_class

                from iterable.helpers.detect import open_iterable

                iterable = open_iterable(
                    "clickhouse://localhost/db",
                    engine="clickhouse",
                    iterableargs={"query": "events"},
                )

                try:
                    chunks = iterable.to_pandas(chunksize=2)
                    chunk_list = list(chunks)
                    assert len(chunk_list) == 3  # 2, 2, 1
                    assert len(chunk_list[0]) == 2
                except ImportError:
                    pytest.skip("pandas not installed")

    @pytest.mark.skipif(ClickHouseDriver is None, reason="clickhouse-connect not installed")
    def test_to_polars_with_clickhouse(self):
        """Test .to_polars() with ClickHouse source."""
        with patch("iterable.helpers.detect.get_driver") as mock_get_driver:
            with patch("iterable.helpers.detect.ClickHouseDriver") as mock_clickhouse_driver_class:
                mock_driver = MagicMock()
                mock_driver.is_connected = True
                mock_driver.iterate.return_value = iter([{"id": 1, "name": "test"}])
                mock_driver._start_metrics = MagicMock()
                mock_clickhouse_driver_class.return_value = mock_driver
                mock_get_driver.return_value = mock_clickhouse_driver_class

                from iterable.helpers.detect import open_iterable

                iterable = open_iterable(
                    "clickhouse://localhost/db",
                    engine="clickhouse",
                    iterableargs={"query": "events"},
                )

                try:
                    df = iterable.to_polars()
                    assert len(df) == 1
                    assert "id" in df.columns
                    assert "name" in df.columns
                except ImportError:
                    pytest.skip("polars not installed")

    @pytest.mark.skipif(ClickHouseDriver is None, reason="clickhouse-connect not installed")
    def test_to_dask_with_clickhouse(self):
        """Test .to_dask() with ClickHouse source."""
        with patch("iterable.helpers.detect.get_driver") as mock_get_driver:
            with patch("iterable.helpers.detect.ClickHouseDriver") as mock_clickhouse_driver_class:
                mock_driver = MagicMock()
                mock_driver.is_connected = True
                mock_driver.iterate.return_value = iter([{"id": 1, "name": "test"}])
                mock_driver._start_metrics = MagicMock()
                mock_clickhouse_driver_class.return_value = mock_driver
                mock_get_driver.return_value = mock_clickhouse_driver_class

                from iterable.helpers.detect import open_iterable

                iterable = open_iterable(
                    "clickhouse://localhost/db",
                    engine="clickhouse",
                    iterableargs={"query": "events"},
                )

                try:
                    df = iterable.to_dask()
                    assert len(df) == 1
                    assert "id" in df.columns
                    assert "name" in df.columns
                except ImportError:
                    pytest.skip("dask not installed")


class TestEdgeCases:
    """Test edge cases and error conditions."""

    def test_empty_result_set(self):
        """Test handling of empty result sets."""
        mock_driver = MagicMock(spec=DBDriver)
        mock_driver.is_connected = True
        mock_driver.iterate.return_value = iter([])
        mock_driver._start_metrics = MagicMock()

        iterable = DatabaseIterable(mock_driver)

        with pytest.raises(StopIteration):
            iterable.read()

    def test_connection_failure(self):
        """Test handling of connection failures."""
        with patch.object(postgres_mod, "psycopg2") as mock_psycopg2:
            mock_psycopg2.connect.side_effect = Exception("Connection refused")

            driver = PostgresDriver("postgresql://localhost/db", query="users")
            with pytest.raises(ConnectionError, match="Failed to connect"):
                driver.connect()

    def test_invalid_query(self):
        """Test handling of invalid queries."""
        with patch.object(postgres_mod, "psycopg2") as mock_psycopg2:
            mock_conn = MagicMock()
            mock_psycopg2.connect.return_value = mock_conn
            mock_cursor = MagicMock()
            mock_cursor.execute.side_effect = Exception("syntax error")
            mock_conn.cursor.return_value = mock_cursor

            driver = PostgresDriver("postgresql://localhost/db", query="INVALID SQL", on_error="raise")
            driver.connect()

            with pytest.raises(Exception, match="syntax error"):
                list(driver.iterate())

    def test_malformed_connection_string(self):
        """Test handling of malformed connection strings."""
        driver = PostgresDriver(123, query="users")  # Not a string or connection object
        with pytest.raises(ValueError, match="must be a connection string"):
            driver.connect()


@pytest.mark.skipif(ClickHouseDriver is None, reason="clickhouse-connect not installed")
class TestClickHouseDriver:
    """Test ClickHouse driver implementation."""

    def test_connect_with_connection_string(self):
        """Test connection with connection string."""
        with patch.object(clickhouse_mod, "clickhouse_connect") as mock_ch:
            mock_client = MagicMock()
            mock_ch.get_client.return_value = mock_client

            driver = ClickHouseDriver("clickhouse://user:pass@localhost:9000/db", query="SELECT 1")
            driver.connect()

            assert driver.is_connected
            assert driver.conn == mock_client
            mock_ch.get_client.assert_called_once_with(url="clickhouse://user:pass@localhost:9000/db", **{})

    def test_connect_with_existing_client(self):
        """Test connection with existing client object."""
        mock_client = MagicMock()
        mock_client.query = MagicMock()
        mock_client.close = MagicMock()

        driver = ClickHouseDriver(mock_client, query="SELECT 1")
        driver.connect()

        assert driver.is_connected
        assert driver.conn == mock_client

    def test_connect_import_error(self):
        """Test ImportError when clickhouse-connect not installed."""
        with patch.dict("sys.modules", {"clickhouse_connect": None}):
            # Force reimport to trigger ImportError
            import sys

            if "iterable.db.clickhouse" in sys.modules:
                del sys.modules["iterable.db.clickhouse"]

            from iterable.db.clickhouse import ClickHouseDriver

            driver = ClickHouseDriver("clickhouse://localhost/db", query="SELECT 1")
            with pytest.raises(ImportError, match="clickhouse-connect is required"):
                driver.connect()

    def test_connect_with_connect_args(self):
        """Test connection with additional connect_args."""
        with patch.object(clickhouse_mod, "clickhouse_connect") as mock_ch:
            mock_client = MagicMock()
            mock_ch.get_client.return_value = mock_client

            driver = ClickHouseDriver(
                "clickhouse://localhost/db",
                query="SELECT 1",
                connect_args={"secure": True},
            )
            driver.connect()

            mock_ch.get_client.assert_called_once_with(url="clickhouse://localhost/db", secure=True)

    def test_read_only_validation(self):
        """Test read-only query validation."""
        with patch.object(clickhouse_mod, "clickhouse_connect") as mock_ch:
            mock_client = MagicMock()
            mock_ch.get_client.return_value = mock_client

            driver = ClickHouseDriver("clickhouse://localhost/db", query="INSERT INTO table VALUES (1)", read_only=True)
            driver.connect()

            with pytest.raises(ValueError, match="non-SELECT statement"):
                list(driver.iterate())

    def test_read_only_validation_allows_select(self):
        """Test read-only validation allows SELECT queries."""
        with patch.object(clickhouse_mod, "clickhouse_connect") as mock_ch:
            mock_client = MagicMock()
            mock_result = MagicMock()
            mock_result.column_names = ["id"]
            mock_result.result_rows = [(1,), (2,)]
            mock_client.query.return_value = mock_result
            mock_ch.get_client.return_value = mock_client

            driver = ClickHouseDriver("clickhouse://localhost/db", query="SELECT * FROM table", read_only=True)
            driver.connect()

            # Should not raise
            rows = list(driver.iterate())
            assert len(rows) == 2

    def test_build_query_from_table_name(self):
        """Test auto-building SELECT query from table name."""
        driver = ClickHouseDriver("clickhouse://localhost/db", query="events")
        query = driver._build_query()
        assert query == "SELECT * FROM `events`"

    def test_build_query_with_database(self):
        """Test query building with database parameter."""
        driver = ClickHouseDriver("clickhouse://localhost", query="events", database="analytics")
        query = driver._build_query()
        assert query == "SELECT * FROM `analytics`.`events`"

    def test_build_query_with_columns(self):
        """Test query building with columns parameter."""
        driver = ClickHouseDriver("clickhouse://localhost/db", query="events", columns=["id", "name"])
        query = driver._build_query()
        assert query == "SELECT `id`, `name` FROM `events`"

    def test_build_query_with_filter(self):
        """Test query building with filter parameter."""
        driver = ClickHouseDriver("clickhouse://localhost/db", query="events", filter="active = 1")
        query = driver._build_query()
        assert query == "SELECT * FROM `events` WHERE active = 1"

    def test_build_query_with_table_parameter(self):
        """Test query building with table parameter."""
        driver = ClickHouseDriver("clickhouse://localhost/db", table="events")
        query = driver._build_query()
        assert query == "SELECT * FROM `events`"

    def test_iterate_native_format(self):
        """Test iteration with native format."""
        with patch.object(clickhouse_mod, "clickhouse_connect") as mock_ch:
            mock_client = MagicMock()
            mock_result = MagicMock()
            mock_result.column_names = ["id", "name"]
            mock_result.result_rows = [(1, "test1"), (2, "test2")]
            mock_client.query.return_value = mock_result
            mock_ch.get_client.return_value = mock_client

            driver = ClickHouseDriver("clickhouse://localhost/db", query="SELECT * FROM table")
            driver.connect()

            rows = list(driver.iterate())
            assert len(rows) == 2
            assert rows[0] == {"id": 1, "name": "test1"}
            assert rows[1] == {"id": 2, "name": "test2"}

    def test_iterate_json_each_row_format(self):
        """Test iteration with JSONEachRow format."""
        with patch.object(clickhouse_mod, "clickhouse_connect") as mock_ch:
            mock_client = MagicMock()
            mock_result = MagicMock()
            mock_result.column_names = ["id", "name"]
            mock_result.result_rows = [{"id": 1, "name": "test1"}, {"id": 2, "name": "test2"}]
            mock_client.query.return_value = mock_result
            mock_ch.get_client.return_value = mock_client

            driver = ClickHouseDriver("clickhouse://localhost/db", query="SELECT * FROM table", format="JSONEachRow")
            driver.connect()

            rows = list(driver.iterate())
            assert len(rows) == 2
            assert rows[0] == {"id": 1, "name": "test1"}
            assert rows[1] == {"id": 2, "name": "test2"}

    def test_iterate_with_settings(self):
        """Test iteration with ClickHouse query settings."""
        with patch.object(clickhouse_mod, "clickhouse_connect") as mock_ch:
            mock_client = MagicMock()
            mock_result = MagicMock()
            mock_result.column_names = ["id"]
            mock_result.result_rows = [(1,)]
            mock_client.query.return_value = mock_result
            mock_ch.get_client.return_value = mock_client

            driver = ClickHouseDriver(
                "clickhouse://localhost/db",
                query="SELECT * FROM table",
                settings={"max_threads": 4},
            )
            driver.connect()

            list(driver.iterate())
            # Verify settings were passed to query
            call_args = mock_client.query.call_args
            assert call_args[1]["settings"]["max_threads"] == 4

    def test_iterate_with_batch_size(self):
        """Test iteration with batch_size parameter."""
        with patch.object(clickhouse_mod, "clickhouse_connect") as mock_ch:
            mock_client = MagicMock()
            mock_result = MagicMock()
            mock_result.column_names = ["id"]
            mock_result.result_rows = [(1,)]
            mock_client.query.return_value = mock_result
            mock_ch.get_client.return_value = mock_client

            driver = ClickHouseDriver("clickhouse://localhost/db", query="SELECT * FROM table", batch_size=5000)
            driver.connect()

            list(driver.iterate())
            # Verify max_block_size was added to settings
            call_args = mock_client.query.call_args
            assert call_args[1]["settings"]["max_block_size"] == 5000

    def test_iterate_empty_result(self):
        """Test iteration with empty result set."""
        with patch.object(clickhouse_mod, "clickhouse_connect") as mock_ch:
            mock_client = MagicMock()
            mock_result = MagicMock()
            mock_result.column_names = ["id"]
            mock_result.result_rows = []
            mock_client.query.return_value = mock_result
            mock_ch.get_client.return_value = mock_client

            driver = ClickHouseDriver("clickhouse://localhost/db", query="SELECT * FROM table")
            driver.connect()

            rows = list(driver.iterate())
            assert len(rows) == 0

    def test_close(self):
        """Test close() closes connection."""
        with patch.object(clickhouse_mod, "clickhouse_connect") as mock_ch:
            mock_client = MagicMock()
            mock_ch.get_client.return_value = mock_client

            driver = ClickHouseDriver("clickhouse://localhost/db", query="users")
            driver.connect()
            driver.close()

            mock_client.close.assert_called_once()

    def test_list_tables(self):
        """Test list_tables() helper function."""
        with patch.object(clickhouse_mod, "clickhouse_connect") as mock_ch:
            mock_client = MagicMock()
            mock_result = MagicMock()
            mock_result.column_names = ["database", "table", "row_count"]
            mock_result.result_rows = [("analytics", "events", 1000), ("analytics", "users", 500)]
            mock_client.query.return_value = mock_result
            mock_ch.get_client.return_value = mock_client

            tables = ClickHouseDriver.list_tables("clickhouse://localhost/db")

            assert len(tables) == 2
            assert tables[0] == {"database": "analytics", "table": "events", "row_count": 1000}
            assert tables[1] == {"database": "analytics", "table": "users", "row_count": 500}
            mock_client.close.assert_called_once()

    def test_list_tables_with_database(self):
        """Test list_tables() with database parameter."""
        with patch.object(clickhouse_mod, "clickhouse_connect") as mock_ch:
            mock_client = MagicMock()
            mock_result = MagicMock()
            mock_result.column_names = ["database", "table", "row_count"]
            mock_result.result_rows = [("analytics", "events", 1000)]
            mock_client.query.return_value = mock_result
            mock_ch.get_client.return_value = mock_client

            tables = ClickHouseDriver.list_tables("clickhouse://localhost", database="analytics")

            assert len(tables) == 1
            # Verify database parameter was used in query
            call_args = mock_client.query.call_args
            assert "analytics" in call_args[0][0]

    def test_connection_failure(self):
        """Test handling of connection failures."""
        with patch.object(clickhouse_mod, "clickhouse_connect") as mock_ch:
            mock_ch.get_client.side_effect = Exception("Connection refused")

            driver = ClickHouseDriver("clickhouse://localhost/db", query="users")
            with pytest.raises(ConnectionError, match="Failed to connect"):
                driver.connect()

    def test_invalid_query(self):
        """Test handling of invalid queries."""
        with patch.object(clickhouse_mod, "clickhouse_connect") as mock_ch:
            mock_client = MagicMock()
            mock_client.query.side_effect = Exception("syntax error")
            mock_ch.get_client.return_value = mock_client

            driver = ClickHouseDriver("clickhouse://localhost/db", query="INVALID SQL", on_error="raise")
            driver.connect()

            with pytest.raises(Exception, match="syntax error"):
                list(driver.iterate())

    def test_malformed_connection_string(self):
        """Test handling of malformed connection strings."""
        driver = ClickHouseDriver(123, query="users")  # Not a string or client object
        with pytest.raises(ValueError, match="must be a connection string"):
            driver.connect()


class TestMySQLDriver:
    """Test MySQL driver implementation."""

    def test_connect_with_connection_string(self):
        """Test connection with connection string."""
        with patch.object(mysql_mod, "pymysql") as mock_pymysql:
            mock_conn = MagicMock()
            mock_pymysql.connect.return_value = mock_conn

            driver = MySQLDriver("mysql://user:pass@localhost/db", query="SELECT 1")
            driver.connect()

            assert driver.is_connected
            assert driver.conn == mock_conn

    def test_connect_with_existing_connection(self):
        """Test connection with existing connection object."""
        mock_conn = MagicMock()
        mock_conn.cursor = MagicMock()
        mock_conn.close = MagicMock()

        driver = MySQLDriver(mock_conn, query="SELECT 1")
        driver.connect()

        assert driver.is_connected
        assert driver.conn == mock_conn

    def test_connect_import_error(self):
        """Test ImportError when pymysql not installed."""
        with patch.dict("sys.modules", {"pymysql": None}):
            import sys

            if "iterable.db.mysql" in sys.modules:
                del sys.modules["iterable.db.mysql"]

            from iterable.db.mysql import MySQLDriver

            driver = MySQLDriver("mysql://localhost/db", query="SELECT 1")
            with pytest.raises(ImportError, match="pymysql is required"):
                driver.connect()

    def test_build_query_from_table_name(self):
        """Test building query from table name."""
        driver = MySQLDriver("mysql://localhost/db", query="users")
        driver._connected = True
        driver.conn = MagicMock()

        query = driver._build_query()
        assert query == "SELECT * FROM `users`"

    def test_iterate_with_server_side_cursor(self):
        """Test iteration with server-side cursor."""
        with patch.object(mysql_mod, "pymysql") as mock_pymysql:
            mock_conn = MagicMock()
            mock_pymysql.connect.return_value = mock_conn
            mock_cursor = MagicMock()
            mock_cursor.description = [("id",), ("name",)]
            mock_cursor.fetchmany.side_effect = [
                [(1, "Alice"), (2, "Bob")],
                [],
            ]
            mock_pymysql.cursors.SSCursor = MagicMock
            mock_conn.cursor.return_value = mock_cursor

            driver = MySQLDriver("mysql://localhost/db", query="users")
            driver.connect()

            rows = list(driver.iterate())
            assert len(rows) == 2
            assert rows[0] == {"id": 1, "name": "Alice"}
            assert rows[1] == {"id": 2, "name": "Bob"}

    def test_list_tables(self):
        """Test list_tables() helper function."""
        with patch.object(mysql_mod, "pymysql") as mock_pymysql:
            mock_conn = MagicMock()
            mock_pymysql.connect.return_value = mock_conn
            mock_cursor = MagicMock()
            mock_cursor.fetchall.return_value = [
                ("test", "users", 1000),
                ("test", "orders", 500),
            ]
            mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

            tables = MySQLDriver.list_tables("mysql://localhost/db")
            assert len(tables) == 2
            assert tables[0]["schema"] == "test"
            assert tables[0]["table"] == "users"


class TestMSSQLDriver:
    """Test MSSQL driver implementation."""

    def test_connect_with_connection_string(self):
        """Test connection with connection string."""
        with patch.object(mssql_mod, "pyodbc") as mock_pyodbc:
            mock_conn = MagicMock()
            mock_pyodbc.connect.return_value = mock_conn

            driver = MSSQLDriver("mssql://user:pass@localhost/db", query="SELECT 1")
            driver.connect()

            assert driver.is_connected
            assert driver.conn == mock_conn

    def test_connect_with_existing_connection(self):
        """Test connection with existing connection object."""
        mock_conn = MagicMock()
        mock_conn.cursor = MagicMock()
        mock_conn.close = MagicMock()

        driver = MSSQLDriver(mock_conn, query="SELECT 1")
        driver.connect()

        assert driver.is_connected
        assert driver.conn == mock_conn

    def test_connect_import_error(self):
        """Test ImportError when pyodbc not installed."""
        with patch.dict("sys.modules", {"pyodbc": None}):
            import sys

            if "iterable.db.mssql" in sys.modules:
                del sys.modules["iterable.db.mssql"]

            from iterable.db.mssql import MSSQLDriver

            driver = MSSQLDriver("mssql://localhost/db", query="SELECT 1")
            with pytest.raises(ImportError, match="pyodbc is required"):
                driver.connect()

    def test_build_query_from_table_name(self):
        """Test building query from table name."""
        driver = MSSQLDriver("mssql://localhost/db", query="users")
        driver._connected = True
        driver.conn = MagicMock()

        query = driver._build_query()
        assert query == "SELECT * FROM [dbo].[users]"

    def test_iterate(self):
        """Test iteration."""
        with patch.object(mssql_mod, "pyodbc") as mock_pyodbc:
            mock_conn = MagicMock()
            mock_pyodbc.connect.return_value = mock_conn
            mock_cursor = MagicMock()
            mock_cursor.description = [("id",), ("name",)]
            mock_cursor.fetchmany.side_effect = [
                [(1, "Alice"), (2, "Bob")],
                [],
            ]
            mock_conn.cursor.return_value = mock_cursor

            driver = MSSQLDriver("mssql://localhost/db", query="users")
            driver.connect()

            rows = list(driver.iterate())
            assert len(rows) == 2
            assert rows[0] == {"id": 1, "name": "Alice"}
            assert rows[1] == {"id": 2, "name": "Bob"}

    def test_list_tables(self):
        """Test list_tables() helper function."""
        with patch.object(mssql_mod, "pyodbc") as mock_pyodbc:
            mock_conn = MagicMock()
            mock_pyodbc.connect.return_value = mock_conn
            mock_cursor = MagicMock()
            mock_cursor.fetchall.return_value = [
                ("dbo", "users", None),
                ("dbo", "orders", None),
            ]
            mock_conn.cursor.return_value.__enter__.return_value = mock_cursor

            tables = MSSQLDriver.list_tables("mssql://localhost/db")
            assert len(tables) == 2
            assert tables[0]["schema"] == "dbo"
            assert tables[0]["table"] == "users"


class TestSQLiteDriver:
    """Test SQLite driver implementation."""

    def test_connect_with_file_path(self):
        """Test connection with file path."""
        import os
        import tempfile

        with tempfile.NamedTemporaryFile(delete=False, suffix=".db") as tmp:
            tmp_path = tmp.name

        try:
            driver = SQLiteDriver(tmp_path, query="SELECT 1")
            driver.connect()

            assert driver.is_connected
            assert driver.conn is not None
            driver.close()
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

    def test_connect_with_memory_database(self):
        """Test connection with :memory: database."""
        driver = SQLiteDriver(":memory:", query="SELECT 1")
        driver.connect()

        assert driver.is_connected
        assert driver.conn is not None
        driver.close()

    def test_connect_with_existing_connection(self):
        """Test connection with existing connection object."""
        import sqlite3

        mock_conn = sqlite3.connect(":memory:")
        driver = SQLiteDriver(mock_conn, query="SELECT 1")
        driver.connect()

        assert driver.is_connected
        assert driver.conn == mock_conn

    def test_build_query_from_table_name(self):
        """Test building query from table name."""
        driver = SQLiteDriver(":memory:", query="users")
        driver._connected = True
        driver.conn = MagicMock()

        query = driver._build_query()
        assert query == 'SELECT * FROM "users"'

    def test_iterate(self):
        """Test iteration."""
        import sqlite3

        conn = sqlite3.connect(":memory:")
        conn.execute("CREATE TABLE users (id INTEGER, name TEXT)")
        conn.execute("INSERT INTO users VALUES (1, 'Alice')")
        conn.execute("INSERT INTO users VALUES (2, 'Bob')")
        conn.commit()

        driver = SQLiteDriver(conn, query="users")
        driver.connect()

        rows = list(driver.iterate())
        assert len(rows) == 2
        assert rows[0] == {"id": 1, "name": "Alice"}
        assert rows[1] == {"id": 2, "name": "Bob"}

        driver.close()

    def test_list_tables(self):
        """Test list_tables() helper function."""
        import os
        import sqlite3
        import tempfile

        with tempfile.NamedTemporaryFile(delete=False, suffix=".db") as tmp:
            tmp_path = tmp.name

        try:
            conn = sqlite3.connect(tmp_path)
            conn.execute("CREATE TABLE users (id INTEGER)")
            conn.execute("CREATE TABLE orders (id INTEGER)")
            conn.commit()
            conn.close()

            tables = SQLiteDriver.list_tables(tmp_path)
            assert len(tables) == 2
            assert tables[0]["table"] == "orders" or tables[0]["table"] == "users"
            assert tables[1]["table"] == "orders" or tables[1]["table"] == "users"
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)


class TestMongoDriver:
    """Test MongoDB driver implementation."""

    def test_connect_with_connection_string(self):
        """Test connection with connection string."""
        with patch.object(mongo_mod, "MongoClient") as mock_client:
            mock_client_instance = MagicMock()
            mock_client.return_value = mock_client_instance

            driver = MongoDriver("mongodb://localhost:27017", database="test", collection="users")
            driver.connect()

            assert driver.is_connected
            assert driver.conn == mock_client_instance

    def test_connect_with_existing_client(self):
        """Test connection with existing MongoClient."""
        mock_client = MagicMock()
        mock_client.list_database_names = MagicMock()
        mock_client.close = MagicMock()

        driver = MongoDriver(mock_client, database="test", collection="users")
        driver.connect()

        assert driver.is_connected
        assert driver.conn == mock_client

    def test_connect_import_error(self):
        """Test ImportError when pymongo not installed."""
        with patch.dict("sys.modules", {"pymongo": None}):
            import sys

            if "iterable.db.mongo" in sys.modules:
                del sys.modules["iterable.db.mongo"]

            from iterable.db.mongo import MongoDriver

            driver = MongoDriver("mongodb://localhost", database="test", collection="users")
            with pytest.raises(ImportError, match="pymongo is required"):
                driver.connect()

    def test_iterate_with_find(self):
        """Test iteration with find()."""
        with patch.object(mongo_mod, "MongoClient") as mock_client:
            mock_client_instance = MagicMock()
            mock_client.return_value = mock_client_instance
            mock_collection = MagicMock()
            mock_client_instance.__getitem__.return_value.__getitem__.return_value = mock_collection
            mock_cursor = MagicMock()
            mock_cursor.__iter__.return_value = [
                {"_id": "1", "name": "Alice"},
                {"_id": "2", "name": "Bob"},
            ]
            mock_collection.find.return_value.batch_size.return_value = mock_cursor

            driver = MongoDriver("mongodb://localhost", database="test", collection="users")
            driver.connect()

            rows = list(driver.iterate())
            assert len(rows) == 2
            assert rows[0]["name"] == "Alice"
            assert rows[1]["name"] == "Bob"

    def test_list_collections(self):
        """Test list_collections() helper function."""
        with patch.object(mongo_mod, "MongoClient") as mock_client:
            mock_client_instance = MagicMock()
            mock_client.return_value = mock_client_instance
            mock_db = MagicMock()
            mock_client_instance.__getitem__.return_value = mock_db
            mock_db.list_collection_names.return_value = ["users", "orders"]
            mock_db.__getitem__.return_value.estimated_document_count.return_value = 100

            collections = MongoDriver.list_collections("mongodb://localhost", database="test")
            assert len(collections) == 2
            assert collections[0]["collection"] in ["users", "orders"]


class TestElasticsearchDriver:
    """Test Elasticsearch driver implementation."""

    def test_connect_with_url(self):
        """Test connection with URL."""
        with patch.object(elasticsearch_mod, "Elasticsearch") as mock_es:
            mock_client = MagicMock()
            mock_es.return_value = mock_client

            driver = ElasticsearchDriver("http://localhost:9200", index="test_index")
            driver.connect()

            assert driver.is_connected
            assert driver.conn == mock_client

    def test_connect_with_existing_client(self):
        """Test connection with existing Elasticsearch client."""
        mock_client = MagicMock()
        mock_client.search = MagicMock()
        mock_client.close = MagicMock()

        driver = ElasticsearchDriver(mock_client, index="test_index")
        driver.connect()

        assert driver.is_connected
        assert driver.conn == mock_client

    def test_connect_import_error(self):
        """Test ImportError when elasticsearch not installed."""
        with patch.dict("sys.modules", {"elasticsearch": None}):
            import sys

            if "iterable.db.elasticsearch" in sys.modules:
                del sys.modules["iterable.db.elasticsearch"]

            from iterable.db.elasticsearch import ElasticsearchDriver

            driver = ElasticsearchDriver("http://localhost:9200", index="test_index")
            with pytest.raises(ImportError, match="elasticsearch is required"):
                driver.connect()

    def test_iterate_with_scroll(self):
        """Test iteration with scroll API."""
        with patch.object(elasticsearch_mod, "Elasticsearch") as mock_es:
            mock_client = MagicMock()
            mock_es.return_value = mock_client

            # Mock initial search response
            mock_client.search.return_value = {
                "_scroll_id": "scroll123",
                "hits": {
                    "hits": [
                        {"_source": {"id": 1, "name": "Alice"}},
                        {"_source": {"id": 2, "name": "Bob"}},
                    ]
                },
            }

            # Mock scroll response
            mock_client.scroll.return_value = {
                "_scroll_id": "scroll456",
                "hits": {"hits": []},
            }

            driver = ElasticsearchDriver("http://localhost:9200", index="test_index", scroll="5m")
            driver.connect()

            rows = list(driver.iterate())
            assert len(rows) == 2
            assert rows[0] == {"id": 1, "name": "Alice"}
            assert rows[1] == {"id": 2, "name": "Bob"}

    def test_iterate_without_scroll(self):
        """Test iteration without scroll API."""
        with patch.object(elasticsearch_mod, "Elasticsearch") as mock_es:
            mock_client = MagicMock()
            mock_es.return_value = mock_client

            mock_client.search.return_value = {
                "hits": {
                    "hits": [
                        {"_source": {"id": 1, "name": "Alice"}},
                    ]
                },
            }

            driver = ElasticsearchDriver("http://localhost:9200", index="test_index")
            driver.connect()

            rows = list(driver.iterate())
            assert len(rows) == 1
            assert rows[0] == {"id": 1, "name": "Alice"}
