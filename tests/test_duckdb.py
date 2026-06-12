import pytest
from fixdata import FIXTURES_TYPES

from iterable.engines import DuckDBIterable


class TestParquet:
    def test_id(self):
        datatype_id = DuckDBIterable.id()
        assert datatype_id == "duckdb"

    def test_parsesimple_readone(self):
        iterable = DuckDBIterable("fixtures/2cols6rows.parquet")
        row = iterable.read()
        assert row == FIXTURES_TYPES[0]
        iterable.close()

    def test_totals(self):
        iterable = DuckDBIterable("fixtures/2cols6rows.parquet")
        totals = iterable.totals()
        assert totals == 6

    def test_parsesimple_next(self):
        iterable = DuckDBIterable("fixtures/2cols6rows.parquet")
        row = next(iterable)
        assert row == FIXTURES_TYPES[0]
        iterable.reset()
        row_reset = next(iterable)
        assert row_reset == FIXTURES_TYPES[0]
        iterable.close()

    def test_parsesimple_count(self):
        iterable = DuckDBIterable("fixtures/2cols6rows.parquet")
        n = 0
        for _row in iterable:
            n += 1
        assert n == len(FIXTURES_TYPES)
        iterable.close()

    def test_parsesimple_iterateall(self):
        iterable = DuckDBIterable("fixtures/2cols6rows.parquet")
        n = 0
        for row in iterable:
            assert row == FIXTURES_TYPES[n]
            n += 1
        iterable.close()

    def test_is_flatonly_false(self):
        assert DuckDBIterable.is_flatonly() is False

    def test_open_close_noop(self):
        iterable = DuckDBIterable("fixtures/2cols6rows.parquet")
        totals_before = iterable.totals()
        iterable.open()
        iterable.close()
        # Should not affect ability to query totals
        iterable2 = DuckDBIterable("fixtures/2cols6rows.parquet")
        totals_after = iterable2.totals()
        assert totals_before == totals_after == 6

    def test_read_bulk_returns_n_records(self):
        iterable = DuckDBIterable("fixtures/2cols6rows.parquet")
        chunk = iterable.read_bulk(3)
        assert len(chunk) == 3
        assert chunk == FIXTURES_TYPES[:3]
        iterable.close()

    def test_read_bulk_does_not_advance_pos(self):
        iterable = DuckDBIterable("fixtures/2cols6rows.parquet")
        first_chunk = iterable.read_bulk(2)
        second_chunk = iterable.read_bulk(2)
        assert first_chunk == FIXTURES_TYPES[:2]
        assert second_chunk == FIXTURES_TYPES[:2]  # position not advanced by read_bulk
        # Now a single read should still return the first row
        row = iterable.read()
        assert row == FIXTURES_TYPES[0]
        iterable.close()

    def test_stop_iteration_after_exhaustion(self):
        iterable = DuckDBIterable("fixtures/2cols6rows.parquet")
        # Consume all rows
        for _ in range(6):
            _ = iterable.read()
        with pytest.raises(StopIteration):
            _ = iterable.read()
        iterable.close()


class TestDuckDBPushdown:
    """Tests for DuckDB engine pushdown features (columns, filter, query)"""

    def test_column_projection_single_column_csv(self):
        """Test column projection with single column from CSV"""
        from iterable.helpers.detect import open_iterable

        with open_iterable("fixtures/2cols6rows.csv", engine="duckdb", iterableargs={"columns": ["name"]}) as source:
            rows = list(source)
            assert len(rows) == 6
            # Each row should only have 'name' key
            for row in rows:
                assert "name" in row
                assert "id" not in row
                assert isinstance(row["name"], str)

    def test_column_projection_multiple_columns_csv(self):
        """Test column projection with multiple columns from CSV"""
        from iterable.helpers.detect import open_iterable

        with open_iterable(
            "fixtures/2cols6rows.csv", engine="duckdb", iterableargs={"columns": ["id", "name"]}
        ) as source:
            rows = list(source)
            assert len(rows) == 6
            # Each row should have both columns
            for row in rows:
                assert "id" in row
                assert "name" in row
                assert len(row) == 2

    def test_column_projection_jsonl(self):
        """Test column projection with JSONL file"""
        from iterable.helpers.detect import open_iterable

        with open_iterable(
            "fixtures/2cols6rows_flat.jsonl", engine="duckdb", iterableargs={"columns": ["name"]}
        ) as source:
            rows = list(source)
            assert len(rows) == 6
            for row in rows:
                assert "name" in row
                assert "id" not in row

    def test_filter_pushdown_sql_string_simple(self):
        """Test filter pushdown with simple SQL string condition"""
        from iterable.helpers.detect import open_iterable

        with open_iterable("fixtures/2cols6rows.csv", engine="duckdb", iterableargs={"filter": "id = '1'"}) as source:
            rows = list(source)
            assert len(rows) == 1
            assert rows[0]["id"] == "1"
            assert rows[0]["name"] == "John"

    def test_filter_pushdown_sql_string_complex(self):
        """Test filter pushdown with complex SQL string condition"""
        from iterable.helpers.detect import open_iterable

        with open_iterable(
            "fixtures/2cols6rows.csv", engine="duckdb", iterableargs={"filter": "id IN ('1', '2', '3')"}
        ) as source:
            rows = list(source)
            assert len(rows) == 3
            ids = {row["id"] for row in rows}
            assert ids == {"1", "2", "3"}

    def test_filter_pushdown_callable(self):
        """Test filter pushdown with Python callable (fallback to Python filtering)"""
        from iterable.helpers.detect import open_iterable

        def filter_func(row):
            return row["id"] == "1"

        with open_iterable("fixtures/2cols6rows.csv", engine="duckdb", iterableargs={"filter": filter_func}) as source:
            rows = list(source)
            assert len(rows) == 1
            assert rows[0]["id"] == "1"

    def test_combined_columns_and_filter(self):
        """Test combining column projection and filter pushdown"""
        from iterable.helpers.detect import open_iterable

        with open_iterable(
            "fixtures/2cols6rows.csv", engine="duckdb", iterableargs={"columns": ["name"], "filter": "id = '1'"}
        ) as source:
            rows = list(source)
            assert len(rows) == 1
            assert "name" in rows[0]
            assert "id" not in rows[0]
            assert rows[0]["name"] == "John"

    def test_direct_sql_query(self):
        """Test direct SQL query support"""
        from iterable.helpers.detect import open_iterable

        with open_iterable(
            "fixtures/2cols6rows.csv",
            engine="duckdb",
            iterableargs={"query": "SELECT name FROM read_csv_auto('fixtures/2cols6rows.csv') WHERE id = '1'"},
        ) as source:
            rows = list(source)
            assert len(rows) == 1
            assert "name" in rows[0]
            assert rows[0]["name"] == "John"

    def test_direct_sql_query_with_order_by_limit(self):
        """Test direct SQL query with ORDER BY and LIMIT"""
        from iterable.helpers.detect import open_iterable

        with open_iterable(
            "fixtures/2cols6rows.csv",
            engine="duckdb",
            iterableargs={"query": "SELECT * FROM read_csv_auto('fixtures/2cols6rows.csv') ORDER BY id LIMIT 2"},
        ) as source:
            rows = list(source)
            assert len(rows) == 2
            assert rows[0]["id"] == "1"
            assert rows[1]["id"] == "2"

    def test_query_validation_rejects_ddl(self):
        """Test that DDL operations are rejected"""
        from iterable.exceptions import ReadError
        from iterable.helpers.detect import open_iterable

        with pytest.raises(ReadError, match="DDL operation") as exc_info:
            open_iterable(
                "fixtures/2cols6rows.csv", engine="duckdb", iterableargs={"query": "CREATE TABLE test (id INT)"}
            )
        assert exc_info.value.error_code == "INVALID_QUERY"

    def test_query_validation_rejects_dml(self):
        """Test that DML operations are rejected"""
        from iterable.exceptions import ReadError
        from iterable.helpers.detect import open_iterable

        with pytest.raises(ReadError, match="DML operation") as exc_info:
            open_iterable(
                "fixtures/2cols6rows.csv", engine="duckdb", iterableargs={"query": "INSERT INTO test VALUES (1)"}
            )
        assert exc_info.value.error_code == "INVALID_QUERY"

    def test_query_validation_requires_select(self):
        """Test that query must be a SELECT statement"""
        from iterable.exceptions import ReadError
        from iterable.helpers.detect import open_iterable

        with pytest.raises(ReadError, match="SELECT") as exc_info:
            open_iterable("fixtures/2cols6rows.csv", engine="duckdb", iterableargs={"query": "SHOW TABLES"})
        assert exc_info.value.error_code == "INVALID_QUERY"

    def test_query_takes_precedence_over_columns_filter(self):
        """Test that query parameter takes precedence over columns and filter"""
        import warnings

        from iterable.helpers.detect import open_iterable

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            with open_iterable(
                "fixtures/2cols6rows.csv",
                engine="duckdb",
                iterableargs={
                    "query": "SELECT name FROM read_csv_auto('fixtures/2cols6rows.csv')",
                    "columns": ["id"],
                    "filter": "id = '2'",
                },
            ) as source:
                rows = list(source)
                # Query should return all names, not filtered by id='2'
                assert len(rows) == 6
                # Warning should be issued
                assert len(w) > 0
                assert any("ignored" in str(warning.message).lower() for warning in w)

    def test_format_detection_csv(self):
        """Test that CSV files use read_csv_auto"""
        from iterable.engines.duckdb import DuckDBEngineIterable

        iterable = DuckDBEngineIterable("fixtures/2cols6rows.csv", options={})
        assert iterable._file_format == "csv"
        assert iterable._duckdb_function == "read_csv_auto"
        iterable.close()

    def test_format_detection_jsonl(self):
        """Test that JSONL files use read_json_auto"""
        from iterable.engines.duckdb import DuckDBEngineIterable

        iterable = DuckDBEngineIterable("fixtures/2cols6rows_flat.jsonl", options={})
        assert iterable._file_format == "jsonl"
        assert iterable._duckdb_function == "read_json_auto"
        iterable.close()

    def test_format_detection_parquet(self):
        """Test that Parquet files use read_parquet"""
        from iterable.engines.duckdb import DuckDBEngineIterable

        iterable = DuckDBEngineIterable("fixtures/2cols6rows.parquet", options={})
        assert iterable._file_format == "parquet"
        assert iterable._duckdb_function == "read_parquet"
        iterable.close()

    def test_totals_with_filter(self):
        """Test totals() with filter pushdown"""
        from iterable.helpers.detect import open_iterable

        with open_iterable("fixtures/2cols6rows.csv", engine="duckdb", iterableargs={"filter": "id = '1'"}) as source:
            total = source.totals()
            assert total == 1

    def test_totals_with_query(self):
        """Test totals() with custom query"""
        from iterable.helpers.detect import open_iterable

        with open_iterable(
            "fixtures/2cols6rows.csv",
            engine="duckdb",
            iterableargs={"query": "SELECT * FROM read_csv_auto('fixtures/2cols6rows.csv') WHERE id = '1'"},
        ) as source:
            total = source.totals()
            assert total == 1

    def test_read_bulk_with_columns(self):
        """Test read_bulk() with column projection"""
        from iterable.helpers.detect import open_iterable

        with open_iterable("fixtures/2cols6rows.csv", engine="duckdb", iterableargs={"columns": ["name"]}) as source:
            chunk = source.read_bulk(3)
            assert len(chunk) == 3
            for row in chunk:
                assert "name" in row
                assert "id" not in row

    def test_column_validation_invalid_column(self):
        """Test that invalid column names raise an error"""
        from iterable.helpers.detect import open_iterable

        with pytest.raises(ValueError, match="Invalid column name"):
            with open_iterable(
                "fixtures/2cols6rows.csv", engine="duckdb", iterableargs={"columns": ["nonexistent"]}
            ) as source:
                list(source)

    def test_column_validation_multiple_invalid(self):
        """Test that multiple invalid column names are reported"""
        from iterable.helpers.detect import open_iterable

        with pytest.raises(ValueError, match="Invalid column name"):
            with open_iterable(
                "fixtures/2cols6rows.csv",
                engine="duckdb",
                iterableargs={"columns": ["nonexistent1", "nonexistent2"]},
            ) as source:
                list(source)

    def test_callable_filter_translation_simple(self):
        """Test that simple callable filters are translated to SQL"""
        from iterable.helpers.detect import open_iterable

        # Simple comparison that should be translatable
        with open_iterable(
            "fixtures/2cols6rows.csv", engine="duckdb", iterableargs={"filter": lambda row: row["id"] == "1"}
        ) as source:
            rows = list(source)
            # Should work (either translated or Python-side filtered)
            assert len(rows) == 1
            assert rows[0]["id"] == "1"

    def test_callable_filter_translation_complex(self):
        """Test that complex callable filters fall back to Python filtering"""
        from iterable.helpers.detect import open_iterable

        # Complex filter that can't be translated
        def complex_filter(row):
            return len(row["name"]) > 3  # Can't translate len() to SQL easily

        with open_iterable(
            "fixtures/2cols6rows.csv", engine="duckdb", iterableargs={"filter": complex_filter}
        ) as source:
            rows = list(source)
            # Should still work (Python-side filtering)
            assert len(rows) > 0
            for row in rows:
                assert len(row["name"]) > 3

    def test_callable_filter_translation_and(self):
        """Test AND operation in callable filter"""
        from iterable.helpers.detect import open_iterable

        # AND condition that might be translatable
        with open_iterable(
            "fixtures/2cols6rows.csv",
            engine="duckdb",
            iterableargs={"filter": lambda row: row["id"] == "1" and row["name"] == "John"},
        ) as source:
            rows = list(source)
            # Should work
            assert len(rows) == 1
            assert rows[0]["id"] == "1"
            assert rows[0]["name"] == "John"

    def test_callable_filter_translation_in(self):
        """Test IN operation in callable filter"""
        from iterable.helpers.detect import open_iterable

        # IN condition that might be translatable
        with open_iterable(
            "fixtures/2cols6rows.csv",
            engine="duckdb",
            iterableargs={"filter": lambda row: row["id"] in ["1", "2", "3"]},
        ) as source:
            rows = list(source)
            # Should work
            assert len(rows) == 3
            ids = {row["id"] for row in rows}
            assert ids == {"1", "2", "3"}


class TestDuckDBRefactoredEngine:
    """Tests for refactored DuckDB engine features (Phase 2 improvements)"""

    def test_invalid_column_raises_format_not_supported_error(self):
        """Test that invalid column names raise FormatNotSupportedError"""
        from iterable.exceptions import FormatNotSupportedError
        from iterable.helpers.detect import open_iterable

        with pytest.raises(FormatNotSupportedError) as exc_info:
            with open_iterable(
                "fixtures/2cols6rows.csv",
                engine="duckdb",
                iterableargs={"columns": ["nonexistent_column"]},
            ) as source:
                list(source)
        assert exc_info.value.format_id == "csv"
        assert "nonexistent_column" in exc_info.value.reason

    def test_invalid_filename_raises_read_error(self):
        """Test that invalid filename parameter raises ReadError"""
        from iterable.engines import DuckDBIterable
        from iterable.exceptions import ReadError

        # DuckDB engine requires filename to be a string
        with pytest.raises(ReadError) as exc_info:
            iterable = DuckDBIterable(filename=None)
            iterable._ensure_connection()
        assert exc_info.value.error_code == "INVALID_PARAMETER"

    def test_batch_caching_works_correctly(self):
        """Test that batch caching works correctly with refactored logic"""
        from iterable.engines import DuckDBIterable

        iterable = DuckDBIterable("fixtures/2cols6rows.csv")
        try:
            # Read first batch (should load batch 0)
            row1 = iterable.read()
            assert row1 is not None

            # Reset and read again (should reload batch 0)
            iterable.reset()
            row1_again = iterable.read()
            assert row1_again == row1

            # Read multiple rows to test batch boundary handling
            rows = []
            for _ in range(5):
                rows.append(iterable.read())
            assert len(rows) == 5
        finally:
            iterable.close()

    def test_parameterized_queries_used(self):
        """Test that parameterized queries are used for LIMIT/OFFSET"""
        from iterable.engines import DuckDBIterable

        iterable = DuckDBIterable("fixtures/2cols6rows.csv")
        try:
            # Verify that _build_sql_query returns tuple with parameters
            query, params = iterable._build_sql_query(limit=5, offset=1)
            assert isinstance(query, str)
            assert isinstance(params, list)
            assert "LIMIT ?" in query
            assert "OFFSET ?" in query
            assert params == [5, 1]
        finally:
            iterable.close()

    def test_read_bulk_advances_position(self):
        """Test that read_bulk correctly advances position"""
        from iterable.engines import DuckDBIterable

        iterable = DuckDBIterable("fixtures/2cols6rows.csv")
        try:
            # Read bulk should advance position
            chunk1 = iterable.read_bulk(2)
            assert len(chunk1) == 2

            # Next read_bulk should continue from where we left off
            chunk2 = iterable.read_bulk(2)
            assert len(chunk2) == 2
            # Should be different rows
            assert chunk1[0] != chunk2[0] or chunk1[1] != chunk2[1]

            # Position should be advanced
            assert iterable.pos == 4
        finally:
            iterable.close()

    def test_connection_reuse(self):
        """Test that connection is reused efficiently"""
        from iterable.engines import DuckDBIterable

        iterable = DuckDBIterable("fixtures/2cols6rows.csv")
        try:
            # First operation creates connection
            totals1 = iterable.totals()
            connection1 = iterable._connection

            # Reset should keep connection
            iterable.reset()
            connection2 = iterable._connection
            assert connection1 is connection2

            # Another operation should reuse connection
            totals2 = iterable.totals()
            connection3 = iterable._connection
            assert connection1 is connection3
            assert totals1 == totals2
        finally:
            iterable.close()
            # After close, connection should be None
            assert iterable._connection is None

    def test_error_handling_for_malformed_query(self):
        """Test that malformed queries raise FormatParseError"""
        from iterable.exceptions import FormatParseError
        from iterable.helpers.detect import open_iterable

        with pytest.raises(FormatParseError) as exc_info:
            with open_iterable(
                "fixtures/2cols6rows.csv",
                engine="duckdb",
                iterableargs={"query": "SELECT * FROM nonexistent_table"},
            ) as source:
                list(source)
        assert exc_info.value.format_id == "csv"
        assert "Failed to execute query" in exc_info.value.message

    def test_dataframe_conversion_fallback(self):
        """Test that DataFrame conversion falls back gracefully"""
        from iterable.engines import DuckDBIterable

        iterable = DuckDBIterable("fixtures/2cols6rows.csv")
        try:
            # Should work whether pandas is available or not
            rows = []
            for _ in range(3):
                rows.append(iterable.read())
            assert len(rows) == 3
            # All rows should be dicts
            for row in rows:
                assert isinstance(row, dict)
        finally:
            iterable.close()
