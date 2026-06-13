"""
Tests for DuckDB datatype format support.
This tests the DuckDBIterable from iterable.datatypes.duckdb
"""

import os
import tempfile

import duckdb
import pytest

from iterable.datatypes.duckdb import DuckDBIterable


def _new_duckdb_path(suffix: str = ".duckdb") -> str:
    """
    Return a filesystem path that does not exist yet.

    Newer DuckDB versions error if the file exists but is not a valid database,
    so we must not pre-create an empty file.
    """
    fd, path = tempfile.mkstemp(suffix=suffix)
    os.close(fd)
    os.unlink(path)
    return path


def test_duckdb_id():
    """Test DuckDB ID"""
    assert DuckDBIterable.id() == "duckdb"


def test_duckdb_flatonly():
    """Test DuckDB is flat only"""
    assert DuckDBIterable.is_flatonly()


def test_duckdb_has_totals():
    """Test DuckDB has totals"""
    assert DuckDBIterable.has_totals()


def test_duckdb_read_write():
    """Test DuckDB read and write"""
    tmp_path = _new_duckdb_path(".duckdb")

    try:
        # Create a test database with data
        conn = duckdb.connect(tmp_path)
        conn.execute("CREATE TABLE test_table (name VARCHAR, age INTEGER, city VARCHAR)")
        conn.execute("INSERT INTO test_table VALUES ('Alice', 30, 'New York')")
        conn.execute("INSERT INTO test_table VALUES ('Bob', 25, 'London')")
        conn.execute("INSERT INTO test_table VALUES ('Charlie', 35, 'Tokyo')")
        if hasattr(conn, "commit"):
            conn.commit()
        conn.close()

        # Read data
        reader = DuckDBIterable(tmp_path, mode="r", table="test_table")
        results = []
        for record in reader:
            results.append(record)
        reader.close()

        assert len(results) == 3
        assert results[0]["name"] == "Alice"
        assert results[0]["age"] == 30
        assert results[0]["city"] == "New York"

        # Test totals
        reader2 = DuckDBIterable(tmp_path, mode="r", table="test_table")
        total = reader2.totals()
        reader2.close()
        assert total == 3
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)


def test_duckdb_write():
    """Test DuckDB write"""
    tmp_path = _new_duckdb_path(".duckdb")

    try:
        # Write data
        writer = DuckDBIterable(tmp_path, mode="w", table="test_table")
        writer.write({"name": "Alice", "age": 30, "city": "New York"})
        writer.write({"name": "Bob", "age": 25, "city": "London"})
        writer.close()

        # Read back
        reader = DuckDBIterable(tmp_path, mode="r", table="test_table")
        results = list(reader)
        reader.close()

        assert len(results) == 2
        assert results[0]["name"] == "Alice"
        assert results[0]["age"] == 30
        assert results[1]["name"] == "Bob"
        assert results[1]["age"] == 25
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)


def test_duckdb_write_bulk():
    """Test DuckDB bulk write"""
    tmp_path = _new_duckdb_path(".duckdb")

    try:
        test_data = [
            {"name": "Alice", "age": 30, "city": "New York"},
            {"name": "Bob", "age": 25, "city": "London"},
            {"name": "Charlie", "age": 35, "city": "Tokyo"},
        ]

        # Write bulk
        writer = DuckDBIterable(tmp_path, mode="w", table="test_table")
        writer.write_bulk(test_data)
        writer.close()

        # Read back
        reader = DuckDBIterable(tmp_path, mode="r", table="test_table")
        results = list(reader)
        reader.close()

        assert len(results) == 3
        assert results[0]["name"] == "Alice"
        assert results[1]["name"] == "Bob"
        assert results[2]["name"] == "Charlie"
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)


def test_duckdb_query():
    """Test DuckDB with custom query"""
    tmp_path = _new_duckdb_path(".duckdb")

    try:
        # Create test data
        conn = duckdb.connect(tmp_path)
        conn.execute("CREATE TABLE test_table (name VARCHAR, age INTEGER)")
        conn.execute("INSERT INTO test_table VALUES ('Alice', 30)")
        conn.execute("INSERT INTO test_table VALUES ('Bob', 25)")
        if hasattr(conn, "commit"):
            conn.commit()
        conn.close()

        # Read with query
        reader = DuckDBIterable(tmp_path, mode="r", query="SELECT name FROM test_table WHERE age > 26")
        results = list(reader)
        reader.close()

        assert len(results) == 1
        assert results[0]["name"] == "Alice"
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)


def test_duckdb_auto_table_detection():
    """Test DuckDB automatically detects first table"""
    tmp_path = _new_duckdb_path(".duckdb")

    try:
        # Create test data
        conn = duckdb.connect(tmp_path)
        conn.execute("CREATE TABLE test_table (name VARCHAR, age INTEGER)")
        conn.execute("INSERT INTO test_table VALUES ('Alice', 30)")
        conn.execute("INSERT INTO test_table VALUES ('Bob', 25)")
        if hasattr(conn, "commit"):
            conn.commit()
        conn.close()

        # Read without specifying table (should auto-detect first table)
        reader = DuckDBIterable(tmp_path, mode="r")
        results = list(reader)
        reader.close()

        assert len(results) == 2
        assert results[0]["name"] == "Alice"
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)


def test_duckdb_read_bulk():
    """Test DuckDB read_bulk method"""
    tmp_path = _new_duckdb_path(".duckdb")

    try:
        # Create test data
        conn = duckdb.connect(tmp_path)
        conn.execute("CREATE TABLE test_table (name VARCHAR, age INTEGER)")
        for i in range(10):
            conn.execute(f"INSERT INTO test_table VALUES ('Person{i}', {20 + i})")
        if hasattr(conn, "commit"):
            conn.commit()
        conn.close()

        # Read bulk
        reader = DuckDBIterable(tmp_path, mode="r", table="test_table")
        chunk = reader.read_bulk(5)
        reader.close()

        assert len(chunk) == 5
        assert chunk[0]["name"] == "Person0"
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)


def test_duckdb_reset():
    """Test DuckDB reset functionality"""
    tmp_path = _new_duckdb_path(".duckdb")

    try:
        # Create test data
        conn = duckdb.connect(tmp_path)
        conn.execute("CREATE TABLE test_table (name VARCHAR)")
        conn.execute("INSERT INTO test_table VALUES ('Alice')")
        conn.execute("INSERT INTO test_table VALUES ('Bob')")
        if hasattr(conn, "commit"):
            conn.commit()
        conn.close()

        # Read and reset
        reader = DuckDBIterable(tmp_path, mode="r", table="test_table")
        first = reader.read()
        reader.reset()
        first_after_reset = reader.read()

        assert first == first_after_reset
        reader.close()
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)


def test_duckdb_no_table_error():
    """Test DuckDB raises error when no tables exist"""
    tmp_path = _new_duckdb_path(".duckdb")

    try:
        # Create empty database
        conn = duckdb.connect(tmp_path)
        conn.close()

        # Try to read without tables
        reader = DuckDBIterable(tmp_path, mode="r")
        with pytest.raises(ValueError, match="No tables found"):
            _ = reader.read()
        reader.close()
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)


def test_duckdb_write_no_table_error():
    """Test DuckDB raises error when writing without table name"""
    tmp_path = _new_duckdb_path(".duckdb")

    try:
        writer = DuckDBIterable(tmp_path, mode="w")
        with pytest.raises(ValueError, match="Table name required"):
            writer.write({"name": "Alice"})
        writer.close()
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)


def test_duckdb_write_mode_error():
    """Test DuckDB raises error when writing in read mode"""
    tmp_path = _new_duckdb_path(".duckdb")

    try:
        # Create table first
        conn = duckdb.connect(tmp_path)
        conn.execute("CREATE TABLE test_table (name VARCHAR)")
        if hasattr(conn, "commit"):
            conn.commit()
        conn.close()

        reader = DuckDBIterable(tmp_path, mode="r", table="test_table")
        with pytest.raises(ValueError, match="Write mode not enabled"):
            reader.write({"name": "Alice"})
        reader.close()
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)


def test_duckdb_stream_error():
    """Test DuckDB raises error when stream is provided"""
    with pytest.raises(ValueError, match="DuckDB requires a filename"):
        DuckDBIterable(stream=open(os.devnull))


def test_duckdb_filename_required():
    """Test DuckDB raises error when filename is None"""
    with pytest.raises(ValueError, match="DuckDB requires a filename"):
        DuckDBIterable(filename=None)


def test_duckdb_totals_with_query():
    """Test DuckDB totals with custom query"""
    tmp_path = _new_duckdb_path(".duckdb")

    try:
        # Create test data
        conn = duckdb.connect(tmp_path)
        conn.execute("CREATE TABLE test_table (name VARCHAR, age INTEGER)")
        conn.execute("INSERT INTO test_table VALUES ('Alice', 30)")
        conn.execute("INSERT INTO test_table VALUES ('Bob', 25)")
        conn.execute("INSERT INTO test_table VALUES ('Charlie', 35)")
        if hasattr(conn, "commit"):
            conn.commit()
        conn.close()

        # Test totals with query
        reader = DuckDBIterable(tmp_path, mode="r", query="SELECT * FROM test_table WHERE age > 26")
        total = reader.totals()
        reader.close()

        assert total == 2  # Alice and Charlie
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)


def test_duckdb_iteration():
    """Test DuckDB iteration protocol"""
    tmp_path = _new_duckdb_path(".duckdb")

    try:
        # Create test data
        conn = duckdb.connect(tmp_path)
        conn.execute("CREATE TABLE test_table (name VARCHAR)")
        conn.execute("INSERT INTO test_table VALUES ('Alice')")
        conn.execute("INSERT INTO test_table VALUES ('Bob')")
        if hasattr(conn, "commit"):
            conn.commit()
        conn.close()

        # Test iteration
        reader = DuckDBIterable(tmp_path, mode="r", table="test_table")
        results = [row for row in reader]
        reader.close()

        assert len(results) == 2
        assert results[0]["name"] == "Alice"
        assert results[1]["name"] == "Bob"
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)


def test_duckdb_stop_iteration():
    """Test DuckDB raises StopIteration when exhausted"""
    tmp_path = _new_duckdb_path(".duckdb")

    try:
        # Create test data with one row
        conn = duckdb.connect(tmp_path)
        conn.execute("CREATE TABLE test_table (name VARCHAR)")
        conn.execute("INSERT INTO test_table VALUES ('Alice')")
        if hasattr(conn, "commit"):
            conn.commit()
        conn.close()

        reader = DuckDBIterable(tmp_path, mode="r", table="test_table")
        _ = reader.read()  # Read the one row
        with pytest.raises(StopIteration):
            _ = reader.read()  # Should raise StopIteration
        reader.close()
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)


def test_duckdb_open_iterable():
    """Test DuckDB format detection with open_iterable"""
    from iterable.helpers.detect import open_iterable  # noqa: F401

    tmp_path = _new_duckdb_path(".duckdb")

    try:
        # Create test data
        conn = duckdb.connect(tmp_path)
        conn.execute("CREATE TABLE test_table (name VARCHAR, age INTEGER)")
        conn.execute("INSERT INTO test_table VALUES ('Alice', 30)")
        if hasattr(conn, "commit"):
            conn.commit()
        conn.close()

        # Test format detection
        reader = open_iterable(tmp_path, iterableargs={"table": "test_table"})
        results = list(reader)
        reader.close()

        assert len(results) == 1
        assert results[0]["name"] == "Alice"
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)


def test_duckdb_ddb_extension():
    """Test DuckDB format detection with .ddb extension"""
    from iterable.helpers.detect import open_iterable  # noqa: F401

    tmp_path = _new_duckdb_path(".ddb")

    try:
        # Create test data
        conn = duckdb.connect(tmp_path)
        conn.execute("CREATE TABLE test_table (name VARCHAR)")
        conn.execute("INSERT INTO test_table VALUES ('Alice')")
        if hasattr(conn, "commit"):
            conn.commit()
        conn.close()

        # Test format detection with .ddb extension
        reader = open_iterable(tmp_path, iterableargs={"table": "test_table"})
        results = list(reader)
        reader.close()

        assert len(results) == 1
        assert results[0]["name"] == "Alice"
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)


def test_duckdb_has_tables():
    """Test has_tables static method"""
    assert DuckDBIterable.has_tables() is True


def test_duckdb_list_tables_instance_method():
    """Test list_tables on an already-opened instance"""
    tmp_path = _new_duckdb_path(".duckdb")

    try:
        # Create test database with multiple tables
        conn = duckdb.connect(tmp_path)
        conn.execute("CREATE TABLE users (name VARCHAR, age INTEGER)")
        conn.execute("CREATE TABLE products (id INTEGER, name VARCHAR)")
        conn.execute("CREATE TABLE orders (order_id INTEGER, user_id INTEGER)")
        if hasattr(conn, "commit"):
            conn.commit()
        conn.close()

        # Open iterable and list tables (should reuse connection)
        reader = DuckDBIterable(tmp_path, mode="r", table="users")
        tables = reader.list_tables()
        assert isinstance(tables, list)
        assert len(tables) >= 3
        assert "users" in tables
        assert "products" in tables
        assert "orders" in tables
        reader.close()
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)


def test_duckdb_list_tables_with_filename():
    """Test list_tables with filename parameter (class-like usage)"""
    tmp_path = _new_duckdb_path(".duckdb")

    try:
        # Create test database with multiple tables
        conn = duckdb.connect(tmp_path)
        conn.execute("CREATE TABLE users (name VARCHAR)")
        conn.execute("CREATE TABLE products (id INTEGER)")
        if hasattr(conn, "commit"):
            conn.commit()
        conn.close()

        # Create instance and call list_tables with filename
        reader = DuckDBIterable(tmp_path, mode="r", table="users")
        tables = reader.list_tables(tmp_path)
        assert isinstance(tables, list)
        assert len(tables) >= 2
        assert "users" in tables
        assert "products" in tables
        reader.close()
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)


def test_duckdb_list_tables_reuses_connection():
    """Test that list_tables reuses open connection"""
    tmp_path = _new_duckdb_path(".duckdb")

    try:
        # Create test database
        conn = duckdb.connect(tmp_path)
        conn.execute("CREATE TABLE test_table (name VARCHAR)")
        conn.execute("INSERT INTO test_table VALUES ('Alice')")
        if hasattr(conn, "commit"):
            conn.commit()
        conn.close()

        # Open iterable and read a row to ensure connection is open
        reader = DuckDBIterable(tmp_path, mode="r", table="test_table")
        _ = reader.read()
        # Now list tables - should reuse connection
        tables1 = reader.list_tables()
        tables2 = reader.list_tables()
        assert tables1 == tables2
        reader.close()
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)


def test_duckdb_list_tables_empty():
    """Test list_tables on empty database"""
    tmp_path = _new_duckdb_path(".duckdb")

    try:
        # Create empty database
        conn = duckdb.connect(tmp_path)
        conn.close()

        # List tables should return empty list
        reader = DuckDBIterable(tmp_path, mode="r")
        tables = reader.list_tables()
        assert isinstance(tables, list)
        assert len(tables) == 0
        reader.close()
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
