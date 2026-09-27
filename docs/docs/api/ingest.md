---
sidebar_position: 14
title: Database Ingestion
description: Ingest data from iterables into various database systems
---

# Database Ingestion

The `iterable.ingest` module provides functions for ingesting data from iterables into various database systems.

## Overview

Database ingestion operations help you load data into databases:
- **Unified API** for multiple database systems
- **Batch processing** for efficient ingestion
- **Upsert support** for insert-or-update operations
- **Auto-create tables** with schema inference
- **Progress reporting** for long-running operations
- **Error handling** with retry logic

## Supported Databases

- **PostgreSQL** - Full-featured relational database
- **SQLite** - Lightweight file-based database
- **DuckDB** - High-performance analytical database
- **MongoDB** - NoSQL document database
- **MySQL** - Popular relational database
- **Elasticsearch** - Search and analytics engine
- **ClickHouse** - Columnar OLAP database (insert-only)
- **Microsoft SQL Server** - Enterprise relational database (insert-only)

## Functions

### `to_db()`

Ingest data from an iterable into a database.

```python
from iterable import ingest

# Basic ingestion
result = ingest.to_db(
    "data.csv",
    db_url="postgresql://user:pass@localhost:5432/mydb",
    table="users",
    dbtype="postgresql"
)

print(f"Inserted: {result.rows_inserted} rows")
```

**Parameters:**
- `iterable`: An iterable of row dictionaries, or a file path/stream
- `db_url`: Database connection URL or file path
- `table`: Table/collection name
- `dbtype`: Database type - "postgresql", "mongodb", "duckdb", "mysql", "sqlite", "elasticsearch", "clickhouse", "mssql"
- `mode`: Ingestion mode - "insert" (default) or "upsert". Note: "clickhouse" and "mssql" are insert-only; mode="upsert" raises ValueError for them
- `upsert_key`: Field name(s) to use for upsert matching (required if mode="upsert")
- `batch`: Batch size for bulk operations (default: 5000)
- `create_table`: Whether to auto-create table/collection if it doesn't exist (default: False)
- `totals`: Whether to return detailed statistics (default: False)
- `progress`: Optional progress callback function

**Returns:** `IngestionResult` object with:
- `rows_processed`: Total rows processed
- `rows_inserted`: Rows inserted
- `rows_updated`: Rows updated (for upsert mode)
- `errors`: List of error messages
- `elapsed_seconds`: Time taken for ingestion

## Examples

### Basic Ingestion

```python
from iterable import ingest

# Ingest CSV to PostgreSQL
result = ingest.to_db(
    "users.csv",
    db_url="postgresql://user:pass@localhost:5432/mydb",
    table="users",
    dbtype="postgresql",
    create_table=True
)

print(f"Processed: {result.rows_processed}")
print(f"Inserted: {result.rows_inserted}")
print(f"Errors: {len(result.errors)}")
```

### Upsert Operations

```python
from iterable import ingest

# Upsert to PostgreSQL (insert or update)
result = ingest.to_db(
    "users.csv",
    db_url="postgresql://user:pass@localhost:5432/mydb",
    table="users",
    dbtype="postgresql",
    mode="upsert",
    upsert_key="id"
)

print(f"Inserted: {result.rows_inserted}")
print(f"Updated: {result.rows_updated}")
```

### SQLite Ingestion

```python
from iterable import ingest

# Ingest to SQLite file
result = ingest.to_db(
    "data.csv",
    db_url="data.db",
    table="records",
    dbtype="sqlite",
    create_table=True
)
```

### DuckDB Ingestion

```python
from iterable import ingest

# Ingest to DuckDB
result = ingest.to_db(
    "data.csv",
    db_url="analytics.duckdb",
    table="events",
    dbtype="duckdb",
    create_table=True
)
```

### MongoDB Ingestion

```python
from iterable import ingest

# Ingest to MongoDB
result = ingest.to_db(
    "data.jsonl",
    db_url="mongodb://localhost:27017/mydb",
    table="documents",
    dbtype="mongodb"
)
```

### Batch Processing

```python
from iterable import ingest

# Use smaller batches for memory-constrained environments
result = ingest.to_db(
    "large_file.csv",
    db_url="postgresql://...",
    table="data",
    dbtype="postgresql",
    batch=1000  # Smaller batch size
)
```

### Progress Reporting

```python
from iterable import ingest

def progress_callback(stats):
    print(f"Processed: {stats['rows_processed']}, Inserted: {stats['rows_inserted']}")

result = ingest.to_db(
    "large_file.csv",
    db_url="postgresql://...",
    table="data",
    dbtype="postgresql",
    progress=progress_callback
)
```

### Combining with Other Operations

```python
from iterable import ingest, filter as f, transform

# Filter, transform, then ingest
filtered = f.filter_expr("data.csv", "`status` == 'active'")
cleaned = transform.deduplicate(filtered, keys=["email"])
renamed = transform.rename_fields(cleaned, {"old_email": "email"})

result = ingest.to_db(
    renamed,
    db_url="postgresql://...",
    table="active_users",
    dbtype="postgresql",
    mode="upsert",
    upsert_key="email"
)
```

## Database-Specific Notes

### PostgreSQL

- Requires `psycopg[binary]` package
- Supports full SQL features
- Upsert uses `ON CONFLICT` clause
- Connection URL format: `postgresql://user:pass@host:port/dbname`

### SQLite

- No additional dependencies (built-in)
- File-based database
- Upsert uses `INSERT OR REPLACE`
- Connection URL: file path (e.g., `"data.db"`)

### DuckDB

- Requires `duckdb` package
- High-performance analytical queries
- Upsert uses `INSERT OR REPLACE`
- Connection URL: file path or `":memory:"` for in-memory

### MongoDB

- Requires `pymongo` package
- Document-based storage
- Upsert uses `replace_one` with `upsert=True`
- Connection URL format: `mongodb://host:port/dbname`

### MySQL

- Requires `mysql-connector-python` package
- Upsert uses `ON DUPLICATE KEY UPDATE`
- Connection URL format: `mysql://user:pass@host:port/dbname`

### Elasticsearch

- Requires `elasticsearch>=8.0` package
- Index-based storage
- Upsert uses document ID matching
- Connection URL: Elasticsearch server URL

### ClickHouse

- Requires `clickhouse-connect` package
- Insert-only: `mode="upsert"` raises `ValueError` (ClickHouse has no row-level UPDATE)
- `create_table=True` creates all columns as `Nullable(String)` under `ENGINE = MergeTree ORDER BY tuple()`
- Connection URL format: `clickhouse://user:pass@host:port/dbname`

```python
from iterable import ingest

# Ingest to ClickHouse
result = ingest.to_db(
    "events.jsonl",
    db_url="clickhouse://user:pass@localhost:9000/analytics",
    table="events",
    dbtype="clickhouse",
    create_table=True
)
```

### Microsoft SQL Server

- Requires `pyodbc` package (plus an ODBC driver, e.g. ODBC Driver 17/18 for SQL Server)
- Insert-only: `mode="upsert"` raises `ValueError` (MERGE-based upsert is not implemented)
- `create_table=True` creates all columns as `NVARCHAR(MAX)`, guarded by an `OBJECT_ID` check
  (T-SQL has no `CREATE TABLE IF NOT EXISTS`)
- Connection URL format: `mssql://user:pass@host:port/dbname?driver=ODBC+Driver+17+for+SQL+Server`
  (`mssql+pyodbc://`, `odbc://`, DSNs, and full pyodbc connection strings also work)

```python
from iterable import ingest

# Ingest to SQL Server
result = ingest.to_db(
    "users.csv",
    db_url="mssql://user:pass@localhost:1433/mydb",
    table="dbo.users",
    dbtype="mssql",
    create_table=True
)
```

## Error Handling

```python
from iterable import ingest

result = ingest.to_db(
    "data.csv",
    db_url="postgresql://...",
    table="users",
    dbtype="postgresql"
)

if result.errors:
    print(f"Ingestion completed with {len(result.errors)} errors:")
    for error in result.errors:
        print(f"  - {error}")
else:
    print("Ingestion completed successfully!")
```

## Performance Tips

1. **Use appropriate batch sizes** - Larger batches (5000-10000) are faster but use more memory
2. **Enable auto-create tables** - Let the system infer schema automatically
3. **Use upsert for updates** - More efficient than separate insert/update operations
4. **Monitor progress** - Use progress callbacks for long-running operations
5. **Handle errors gracefully** - Check `result.errors` after ingestion

## Installation

Database ingestion requires optional dependencies:

```bash
# PostgreSQL
pip install 'psycopg[binary]'

# MongoDB
pip install pymongo

# MySQL
pip install mysql-connector-python

# Elasticsearch
pip install 'elasticsearch>=8.0'

# ClickHouse
pip install clickhouse-connect

# Microsoft SQL Server
pip install pyodbc

# DuckDB (if not already installed)
pip install duckdb

# All database dependencies
pip install iterabledata[db]
```
