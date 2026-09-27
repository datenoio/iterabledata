"""Optional live database ingest integration tests (skipped without services).

These tests exercise ingest→read round-trips for the ClickHouse and MSSQL backends
against real services. They are excluded from the default test run via the
``integration`` marker and additionally skip unless the service URLs are provided:

- ``ITERABLE_TEST_CLICKHOUSE_URL`` (e.g. ``clickhouse://default:@localhost:8123/default``)
- ``ITERABLE_TEST_MSSQL_URL`` (e.g. ``mssql://sa:pass@localhost:1433/master?driver=ODBC+Driver+18+for+SQL+Server``)

Each test uses a unique throwaway table and drops it afterwards.
"""

from __future__ import annotations

import os
import uuid

import pytest

from iterable import ingest
from iterable.helpers.detect import open_iterable

CLICKHOUSE_URL = os.environ.get("ITERABLE_TEST_CLICKHOUSE_URL")
MSSQL_URL = os.environ.get("ITERABLE_TEST_MSSQL_URL")


@pytest.mark.integration
def test_clickhouse_ingest_read_roundtrip():
    """Ingest rows into ClickHouse, then read them back through the clickhouse engine."""
    if not CLICKHOUSE_URL:
        pytest.skip("ITERABLE_TEST_CLICKHOUSE_URL not set")
    clickhouse_connect = pytest.importorskip("clickhouse_connect")

    table = f"iterable_ingest_test_{uuid.uuid4().hex[:8]}"
    rows = [{"id": "1", "name": "Alice"}, {"id": "2", "name": "Bob"}]
    client = clickhouse_connect.get_client(url=CLICKHOUSE_URL)
    try:
        result = ingest.to_db(rows, db_url=CLICKHOUSE_URL, table=table, dbtype="clickhouse", create_table=True)
        assert result.errors == []
        assert result.rows_inserted == 2

        # create_table builds Nullable(String) columns, so values read back as strings
        with open_iterable(CLICKHOUSE_URL, engine="clickhouse", iterableargs={"query": table}) as source:
            read_rows = sorted(source, key=lambda r: r["id"])
        assert read_rows == rows
    finally:
        client.command(f"DROP TABLE IF EXISTS {table}")
        client.close()


@pytest.mark.integration
def test_clickhouse_ingest_without_create_table():
    """Ingest into a pre-created typed ClickHouse table."""
    if not CLICKHOUSE_URL:
        pytest.skip("ITERABLE_TEST_CLICKHOUSE_URL not set")
    clickhouse_connect = pytest.importorskip("clickhouse_connect")

    table = f"iterable_ingest_test_{uuid.uuid4().hex[:8]}"
    client = clickhouse_connect.get_client(url=CLICKHOUSE_URL)
    try:
        client.command(f"CREATE TABLE {table} (id UInt32, name String) ENGINE = MergeTree ORDER BY id")
        result = ingest.to_db(
            [{"id": 1, "name": "Alice"}, {"id": 2, "name": "Bob"}],
            db_url=CLICKHOUSE_URL,
            table=table,
            dbtype="clickhouse",
        )
        assert result.errors == []
        assert result.rows_inserted == 2

        with open_iterable(CLICKHOUSE_URL, engine="clickhouse", iterableargs={"query": table}) as source:
            read_rows = sorted(source, key=lambda r: r["id"])
        assert read_rows == [{"id": 1, "name": "Alice"}, {"id": 2, "name": "Bob"}]
    finally:
        client.command(f"DROP TABLE IF EXISTS {table}")
        client.close()


@pytest.mark.integration
def test_mssql_ingest_read_roundtrip():
    """Ingest rows into SQL Server, then read them back through the mssql engine."""
    if not MSSQL_URL:
        pytest.skip("ITERABLE_TEST_MSSQL_URL not set")
    pyodbc = pytest.importorskip("pyodbc")
    from iterable.db.mssql import _build_connection_string

    table = f"iterable_ingest_test_{uuid.uuid4().hex[:8]}"
    rows = [{"id": "1", "name": "Alice"}, {"id": "2", "name": "Bob"}]
    conn = pyodbc.connect(_build_connection_string(MSSQL_URL, {}))
    try:
        result = ingest.to_db(rows, db_url=MSSQL_URL, table=table, dbtype="mssql", create_table=True)
        assert result.errors == []
        assert result.rows_inserted == 2

        # create_table builds NVARCHAR(MAX) columns, so values read back as strings
        with open_iterable(MSSQL_URL, engine="mssql", iterableargs={"query": table}) as source:
            read_rows = sorted(source, key=lambda r: r["id"])
        assert read_rows == rows
    finally:
        conn.execute(f"DROP TABLE IF EXISTS {table}")
        conn.commit()
        conn.close()
