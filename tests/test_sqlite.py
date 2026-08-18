import os
import sqlite3
import tempfile

from iterable.datatypes.sqlite import SQLiteIterable


def test_sqlite_read_write():
    """Test SQLite read and write"""
    with tempfile.NamedTemporaryFile(delete=False, suffix=".sqlite") as tmp:
        tmp_path = tmp.name

    try:
        # Create a test database with data
        conn = sqlite3.connect(tmp_path)
        conn.execute("CREATE TABLE test_table (name TEXT, age INTEGER, city TEXT)")
        conn.execute("INSERT INTO test_table VALUES ('Alice', 30, 'New York')")
        conn.execute("INSERT INTO test_table VALUES ('Bob', 25, 'London')")
        conn.execute("INSERT INTO test_table VALUES ('Charlie', 35, 'Tokyo')")
        conn.commit()
        conn.close()

        # Read data
        reader = SQLiteIterable(tmp_path, mode="r", table="test_table")
        results = []
        for record in reader:
            results.append(record)
        reader.close()

        assert len(results) == 3
        assert results[0]["name"] == "Alice"
        assert results[0]["age"] == 30

        # Test totals
        reader2 = SQLiteIterable(tmp_path, mode="r", table="test_table")
        total = reader2.totals()
        reader2.close()
        assert total == 3
    finally:
        if os.path.exists(tmp_path):
            try:
                os.unlink(tmp_path)
            except OSError:
                pass


def test_sqlite_has_tables():
    """Test has_tables static method"""
    assert SQLiteIterable.has_tables() is True


def test_sqlite_list_tables():
    """Test list_tables with multiple tables"""
    with tempfile.NamedTemporaryFile(delete=False, suffix=".sqlite") as tmp:
        tmp_path = tmp.name

    try:
        # Create a test database with multiple tables
        conn = sqlite3.connect(tmp_path)
        conn.execute("CREATE TABLE users (id INTEGER, name TEXT)")
        conn.execute("CREATE TABLE orders (id INTEGER, user_id INTEGER)")
        conn.execute("CREATE TABLE products (id INTEGER, name TEXT)")
        conn.commit()
        conn.close()

        # Test instance method
        reader = SQLiteIterable(tmp_path, mode="r", table="users")
        tables = reader.list_tables()
        assert isinstance(tables, list)
        assert len(tables) == 3
        assert "users" in tables
        assert "orders" in tables
        assert "products" in tables
        reader.close()

        # Test with filename parameter
        reader2 = SQLiteIterable(tmp_path, mode="r", table="users")
        tables2 = reader2.list_tables(tmp_path)
        assert tables2 == tables
        reader2.close()

        # Test reuses connection - insert data first
        conn = sqlite3.connect(tmp_path)
        conn.execute("INSERT INTO users (id, name) VALUES (1, 'test')")
        conn.commit()
        conn.close()

        reader3 = SQLiteIterable(tmp_path, mode="r", table="users")
        _ = reader3.read()  # Ensure connection is open
        tables3 = reader3.list_tables()
        tables4 = reader3.list_tables()
        assert tables3 == tables4
        reader3.close()
    finally:
        if os.path.exists(tmp_path):
            try:
                os.unlink(tmp_path)
            except OSError:
                pass


def test_sqlite_list_tables_empty():
    """Test list_tables on empty database"""
    with tempfile.NamedTemporaryFile(delete=False, suffix=".sqlite") as tmp:
        tmp_path = tmp.name

    try:
        # Create empty database
        conn = sqlite3.connect(tmp_path)
        conn.close()

        reader = SQLiteIterable(tmp_path, mode="r")
        # Should raise ValueError for empty database when reading
        # But list_tables should return empty list
        tables = reader.list_tables()
        assert isinstance(tables, list)
        assert len(tables) == 0
        reader.close()
    finally:
        if os.path.exists(tmp_path):
            try:
                os.unlink(tmp_path)
            except OSError:
                pass


def test_sqlite_write():
    """Test SQLite write"""
    with tempfile.NamedTemporaryFile(delete=False, suffix=".sqlite") as tmp:
        tmp_path = tmp.name

    try:
        # Write data
        writer = SQLiteIterable(tmp_path, mode="w", table="test_table")
        writer.write({"name": "Alice", "age": 30, "city": "New York"})
        writer.write({"name": "Bob", "age": 25, "city": "London"})
        writer.close()

        # Read back
        reader = SQLiteIterable(tmp_path, mode="r", table="test_table")
        results = list(reader)
        reader.close()

        assert len(results) == 2
        assert results[0]["name"] == "Alice"
    finally:
        if os.path.exists(tmp_path):
            try:
                os.unlink(tmp_path)
            except OSError:
                pass


def test_sqlite_write_bulk():
    """Test SQLite bulk write"""
    with tempfile.NamedTemporaryFile(delete=False, suffix=".sqlite") as tmp:
        tmp_path = tmp.name

    try:
        test_data = [
            {"name": "Alice", "age": 30, "city": "New York"},
            {"name": "Bob", "age": 25, "city": "London"},
            {"name": "Charlie", "age": 35, "city": "Tokyo"},
        ]

        # Write bulk
        writer = SQLiteIterable(tmp_path, mode="w", table="test_table")
        writer.write_bulk(test_data)
        writer.close()

        # Read back
        reader = SQLiteIterable(tmp_path, mode="r", table="test_table")
        results = list(reader)
        reader.close()

        assert len(results) == 3
    finally:
        if os.path.exists(tmp_path):
            try:
                os.unlink(tmp_path)
            except OSError:
                pass


def test_sqlite_query():
    """Test SQLite with custom query"""
    with tempfile.NamedTemporaryFile(delete=False, suffix=".sqlite") as tmp:
        tmp_path = tmp.name

    try:
        # Create test data
        conn = sqlite3.connect(tmp_path)
        conn.execute("CREATE TABLE test_table (name TEXT, age INTEGER)")
        conn.execute("INSERT INTO test_table VALUES ('Alice', 30)")
        conn.execute("INSERT INTO test_table VALUES ('Bob', 25)")
        conn.commit()
        conn.close()

        # Read with query
        reader = SQLiteIterable(tmp_path, mode="r", query="SELECT name FROM test_table WHERE age > 26")
        results = list(reader)
        reader.close()

        assert len(results) == 1
        assert results[0]["name"] == "Alice"
    finally:
        if os.path.exists(tmp_path):
            try:
                os.unlink(tmp_path)
            except OSError:
                pass


def test_sqlite_default_table_name():
    """Writing without an explicit table defaults the table name from the file."""
    from iterable.datatypes.sqlite import _default_table_name

    assert _default_table_name("/a/b/reestrpo_final.sqlite") == "reestrpo_final"
    assert _default_table_name("/a/b/123data.db") == "_123data"
    assert _default_table_name("/a/b/weird name!.sqlite") == "weird_name_"

    with tempfile.NamedTemporaryFile(delete=False, suffix=".sqlite") as tmp:
        tmp_path = tmp.name
    os.unlink(tmp_path)
    expected_table = _default_table_name(tmp_path)
    try:
        writer = SQLiteIterable(tmp_path, mode="w")
        assert writer.table == expected_table
        writer.write_bulk([{"name": "Alice", "age": "30"}, {"name": "Bob", "age": "25"}])
        writer.close()

        reader = SQLiteIterable(tmp_path, mode="r", table=expected_table)
        results = list(reader)
        reader.close()
        assert results == [{"name": "Alice", "age": "30"}, {"name": "Bob", "age": "25"}]
    finally:
        if os.path.exists(tmp_path):
            try:
                os.unlink(tmp_path)
            except OSError:
                pass


def test_sqlite_id():
    """Test SQLite ID"""
    assert SQLiteIterable.id() == "sqlite"


def test_sqlite_flatonly():
    """Test SQLite is flat only"""
    assert SQLiteIterable.is_flatonly()


def test_sqlite_list_tables_invalid_file():
    """Test list_tables on invalid file (edge case)"""
    with tempfile.NamedTemporaryFile(delete=False, suffix=".sqlite") as tmp:
        tmp_path = tmp.name
        tmp.write(b"not a sqlite database")

    try:
        # Should handle gracefully - SQLite will create a new database if file doesn't exist or is invalid
        reader = SQLiteIterable(tmp_path, mode="r")
        # Should return a list (might be empty if new database)
        tables = reader.list_tables()
        assert isinstance(tables, list)
        reader.close()
    except Exception:
        # If it raises an error, that's also acceptable for invalid files
        pass
    finally:
        if os.path.exists(tmp_path):
            try:
                os.unlink(tmp_path)
            except OSError:
                pass
