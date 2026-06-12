"""
Tests for ingest module.
"""

import os
import tempfile

import pytest

from iterable import ingest


class TestIngest:
    def test_ingest_sqlite(self):
        """Test SQLite ingestion."""
        rows = [
            {"id": 1, "name": "John"},
            {"id": 2, "name": "Jane"},
        ]

        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name

        try:
            result = ingest.to_db(
                rows,
                db_url=db_path,
                table="users",
                dbtype="sqlite",
                create_table=True,
            )
            assert result.rows_processed == 2
            assert result.rows_inserted == 2
            assert len(result.errors) == 0
        finally:
            if os.path.exists(db_path):
                os.unlink(db_path)

    def test_ingest_duckdb(self):
        """Test DuckDB ingestion."""
        try:
            rows = [
                {"id": 1, "name": "John"},
                {"id": 2, "name": "Jane"},
            ]

            with tempfile.NamedTemporaryFile(suffix=".duckdb", delete=False) as f:
                db_path = f.name
            # DuckDB refuses to open an existing file that is not a valid database
            os.unlink(db_path)

            try:
                result = ingest.to_db(
                    rows,
                    db_url=db_path,
                    table="users",
                    dbtype="duckdb",
                    create_table=True,
                )
                assert result.rows_processed == 2
                assert result.rows_inserted == 2
            finally:
                if os.path.exists(db_path):
                    os.unlink(db_path)
        except ImportError:
            pytest.skip("DuckDB not available")

    def test_ingest_unsupported_dbtype(self):
        """Test handling of unsupported database type."""
        rows = [{"a": 1}]
        with pytest.raises(ValueError, match="Unsupported database type"):
            ingest.to_db(rows, db_url="test", table="test", dbtype="unsupported")

    def test_ingest_with_batch(self):
        """Test ingestion with batch size."""
        rows = [{"id": i} for i in range(10)]

        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name

        try:
            result = ingest.to_db(
                rows,
                db_url=db_path,
                table="test",
                dbtype="sqlite",
                batch=3,
                create_table=True,
            )
            assert result.rows_processed == 10
        finally:
            if os.path.exists(db_path):
                os.unlink(db_path)

    def test_ingest_file_path(self):
        """Test ingestion from file path."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name

        try:
            # This will test file path handling (cwd is tests/ via conftest)
            result = ingest.to_db(
                "fixtures/2cols6rows.csv",
                db_url=db_path,
                table="test",
                dbtype="sqlite",
                create_table=True,
            )
            assert result.rows_processed > 0
        finally:
            if os.path.exists(db_path):
                os.unlink(db_path)
