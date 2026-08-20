---
sidebar_position: 4
title: Engines
description: Processing engines available in Iterable Data
---

# Engines

Iterable Data supports multiple processing engines, each optimized for different use cases.

## Internal Engine (Default)

The internal engine uses pure Python implementations for all formats. It supports all file types and compression codecs.

### Features

- ✅ Supports 100+ formats
- ✅ Supports all compression codecs
- ✅ Works with nested data structures
- ✅ No additional dependencies required

### Usage

```python
from iterable import open_iterable

# Internal engine is the default
# Recommended: Using context manager
with open_iterable('data.csv.gz', engine='internal') as source:
    for row in source:
        print(row)
# or simply (internal is default)
with open_iterable('data.csv.gz') as source:
    for row in source:
        print(row)
```

### When to Use

- Working with formats not supported by DuckDB
- Need other compression codecs (BZip2, LZMA, LZ4, etc.)
- Processing nested data structures
- General-purpose data processing

## DuckDB Engine

The DuckDB engine provides high-performance querying capabilities using the DuckDB database engine with advanced pushdown optimizations.

### Features

- ⚡ Fast queries on large files
- ⚡ Efficient row counting
- ⚡ SQL-like operations
- ⚡ Supports compressed files
- ⚡ **Column projection pushdown** - Only read needed columns
- ⚡ **Filter pushdown** - Filter at the database level
- ⚡ **Direct SQL queries** - Full SQL power with iterator interface

### Supported Formats

- **Formats**: CSV, JSONL, NDJSON, JSON, Parquet
- **Compression**: GZIP (`.gz`), ZStandard (`.zst`, `.zstd`)

### Installation

DuckDB is an optional dependency:

```bash
pip install duckdb
```

### Basic Usage

```python
from iterable import open_iterable

# Recommended: Using context manager
# Use DuckDB engine
with open_iterable('data.csv.gz', engine='duckdb') as source:
    # Fast row counting
    total = source.totals()
    print(f"Total records: {total}")
    
    for row in source:
        print(row)
# File automatically closed
```

### Column Projection Pushdown

Only read specific columns to reduce I/O and memory usage:

```python
from iterable import open_iterable

# Only read 'name' and 'age' columns
with open_iterable('data.csv', engine='duckdb', 
                   iterableargs={'columns': ['name', 'age']}) as source:
    for row in source:
        print(row)  # Only contains 'name' and 'age' keys
```

### Filter Pushdown

Filter rows at the database level for maximum performance:

```python
from iterable import open_iterable

# SQL string filter
with open_iterable('data.csv', engine='duckdb',
                   iterableargs={'filter': "age > 18 AND status = 'active'"}) as source:
    for row in source:
        print(row)  # Only rows matching the condition

# Python callable filter (falls back to Python-side filtering if not translatable)
with open_iterable('data.csv', engine='duckdb',
                   iterableargs={'filter': lambda row: row['age'] > 18}) as source:
    for row in source:
        print(row)
```

### Combined Pushdown

Combine column projection and filtering for maximum efficiency:

```python
from iterable import open_iterable

# Read only 'name' and 'age' columns, filtered by age > 18
with open_iterable('data.csv', engine='duckdb',
                   iterableargs={
                       'columns': ['name', 'age'],
                       'filter': 'age > 18'
                   }) as source:
    for row in source:
        print(row)  # Only 'name' and 'age', only rows where age > 18
```

### Direct SQL Queries

Execute full SQL queries while maintaining the iterator interface:

```python
from iterable import open_iterable

# Custom SQL query with ORDER BY and LIMIT
with open_iterable('data.parquet', engine='duckdb',
                   iterableargs={
                       'query': 'SELECT name, age FROM read_parquet(\'data.parquet\') WHERE age > 18 ORDER BY age DESC LIMIT 100'
                   }) as source:
    for row in source:
        print(row)

# Note: When 'query' is provided, 'columns' and 'filter' parameters are ignored
```

**Important**: When using custom queries, you must reference files using DuckDB's read functions:
- CSV: `read_csv_auto('file.csv')`
- JSONL/JSON: `read_json_auto('file.jsonl')`
- Parquet: `read_parquet('file.parquet')`

### When to Use

- ✅ Large files (100MB+)
- ✅ Need fast row counting
- ✅ Working with CSV, JSONL, JSON, or Parquet files
- ✅ Files compressed with GZIP or ZStandard
- ✅ Need SQL-like querying capabilities
- ✅ Want to reduce I/O by reading only needed columns
- ✅ Need to filter large datasets efficiently

### Limitations

- ❌ Only supports CSV, JSONL, NDJSON, JSON, and Parquet formats
- ❌ Only supports GZIP and ZStandard compression
- ❌ Requires DuckDB to be installed
- ❌ Not suitable for very large streaming files
- ❌ Python callable filters fall back to Python-side filtering (may be slower)

## Direct DuckDB Queries

You can also use DuckDB directly for more complex queries:

```python
import duckdb

# Connect to DuckDB
conn = duckdb.connect()

# Query JSONL file directly
result = conn.execute("""
    SELECT * 
    FROM 'data.jsonl.zst' 
    WHERE age > 18
    LIMIT 100
""").fetchall()

for row in result:
    print(row)
```

## Performance Comparison

| Operation | Internal Engine | DuckDB Engine |
|-----------|----------------|---------------|
| Small files (< 10MB) | Fast | Fast |
| Large files (> 100MB) | Moderate | Very Fast |
| Row counting | Slow | Very Fast |
| Filtering | Moderate | Very Fast |
| Format support | All formats | CSV/JSONL only |
| Compression | All codecs | GZIP/ZStandard only |

## Choosing an Engine

**Use Internal Engine when:**
- Working with formats not supported by DuckDB
- Need other compression codecs
- Processing nested data structures
- General-purpose data processing

**Use DuckDB Engine when:**
- Working with large CSV or JSONL files
- Need fast row counting
- Need SQL-like querying
- Files are compressed with GZIP or ZStandard

## Error Handling

```python
from iterable import open_iterable

try:
    # Using DuckDB engine with error handling
    with open_iterable('data.csv.gz', engine='duckdb') as source:
        total = source.totals()
        for row in source:
            process(row)
except ImportError:
    print("DuckDB not installed. Install with: pip install duckdb")
except FileNotFoundError:
    print("File not found")
except Exception as e:
    print(f"Error with DuckDB engine: {e}")
    # Fallback to internal engine
    with open_iterable('data.csv.gz', engine='internal') as source:
        for row in source:
            process(row)
```

## Troubleshooting

### DuckDB Engine Not Available

- **Install DuckDB**: `pip install duckdb`
- **Check format**: DuckDB only supports CSV, JSONL, NDJSON, and JSON
- **Check compression**: Only GZIP and ZStandard compression supported
- **Fallback**: Use `engine='internal'` as fallback

### Performance Issues

- **Large files**: DuckDB engine is faster for files > 100MB
- **Small files**: Internal engine may be faster for small files
- **Format support**: Use internal engine for unsupported formats
- **Compression**: DuckDB engine works best with GZIP and ZStandard

## Database Engines

Database engines provide read-only access to SQL and NoSQL databases as iterable data sources. They enable streaming, memory-efficient access to database tables and queries.

### Features

- ✅ **Streaming access**: Large result sets streamed in batches
- ✅ **Unified interface**: Works with `open_iterable()`, `convert()`, and `pipeline()`
- ✅ **Read-only safety**: All operations are read-only by default
- ✅ **Memory efficient**: Server-side cursors and batch processing
- ✅ **Multiple databases**: PostgreSQL, ClickHouse (available), MySQL, MSSQL, SQLite, MongoDB, Elasticsearch (planned)

### Supported Databases

- **PostgreSQL**: ✅ Available (requires `psycopg2-binary`)
- **ClickHouse**: ✅ Available (requires `clickhouse-connect`)
- **MySQL/MariaDB**: 🚧 Planned
- **Microsoft SQL Server**: 🚧 Planned
- **SQLite**: 🚧 Planned
- **MongoDB**: 🚧 Planned
- **Elasticsearch/OpenSearch**: 🚧 Planned

### Installation

Install database dependencies:

```bash
# All database engines
pip install iterabledata[db]

# SQL databases only
pip install iterabledata[db-sql]

# NoSQL databases only
pip install iterabledata[db-nosql]

# Specific database (PostgreSQL)
pip install psycopg2-binary

# Specific database (ClickHouse)
pip install clickhouse-connect
```

### Basic Usage

```python
from iterable import open_iterable

# Read from PostgreSQL database
with open_iterable(
    'postgresql://user:password@localhost:5432/mydb',
    engine='postgres',
    iterableargs={'query': 'users'}
) as source:
    for row in source:
        print(row)

# Read from ClickHouse database
with open_iterable(
    'clickhouse://user:password@localhost:9000/analytics',
    engine='clickhouse',
    iterableargs={'query': 'events'}
) as source:
    for row in source:
        print(row)
```

### When to Use Database Engines

**Use Database Engines when:**
- ✅ Reading data from SQL or NoSQL databases
- ✅ Need streaming access to large database tables
- ✅ Want to use database sources with `convert()` and `pipeline()`
- ✅ Need memory-efficient processing of large result sets
- ✅ Working with ETL/analytical workloads (read-only is safe)

**Use File Engines (internal/duckdb) when:**
- ✅ Working with file-based data sources
- ✅ Need write operations
- ✅ Working with formats not supported by database engines
- ✅ Processing local files

### Database vs File Engines

| Feature | File Engines | Database Engines |
|---------|--------------|------------------|
| Data Source | Files | Databases |
| Write Support | ✅ Yes | ❌ Read-only (write planned) |
| Streaming | ✅ Yes | ✅ Yes (server-side cursors) |
| Format Support | 100+ formats | SQL/NoSQL databases |
| Memory Efficiency | Good | Excellent (batched) |
| Query Capabilities | Limited | Full SQL/NoSQL queries |
| Reset Support | ✅ Yes | ❌ No (queries can't be reset) |

### Examples

#### PostgreSQL

```python
from iterable import open_iterable

# Read table
with open_iterable(
    'postgresql://localhost/mydb',
    engine='postgres',
    iterableargs={'query': 'users'}
) as source:
    for row in source:
        print(row)

# Read with filtering
with open_iterable(
    'postgresql://localhost/mydb',
    engine='postgres',
    iterableargs={
        'query': 'users',
        'columns': ['id', 'name', 'email'],
        'filter': 'active = TRUE'
    }
) as source:
    for row in source:
        print(row)
```

#### ClickHouse

```python
from iterable import open_iterable

# Read table
with open_iterable(
    'clickhouse://localhost:9000/analytics',
    engine='clickhouse',
    iterableargs={'query': 'events'}
) as source:
    for row in source:
        print(row)

# Read with ClickHouse query settings
with open_iterable(
    'clickhouse://localhost:9000/analytics',
    engine='clickhouse',
    iterableargs={
        'query': 'large_table',
        'settings': {'max_threads': 4, 'max_memory_usage': 10000000000}
    }
) as source:
    for row in source:
        print(row)

# Read with database parameter
with open_iterable(
    'clickhouse://localhost:9000',
    engine='clickhouse',
    iterableargs={
        'query': 'events',
        'database': 'analytics',
        'columns': ['id', 'name', 'timestamp']
    }
) as source:
    for row in source:
        print(row)
```

### Limitations

- **Read-only**: Write operations (INSERT, UPDATE, DELETE) are not yet supported
- **No reset**: Database queries cannot be reset after iteration starts
- **Driver dependencies**: Each database requires its own driver package

### Error Handling

```python
from iterable import open_iterable

try:
    with open_iterable(
        'postgresql://localhost/mydb',
        engine='postgres',
        iterableargs={'query': 'users'}
    ) as source:
        for row in source:
            process(row)
except ImportError:
    print("Database driver not installed. Install with: pip install psycopg2-binary")
except ConnectionError as e:
    print(f"Connection failed: {e}")
```

See [Database Engines](/api/database-engines) for comprehensive documentation.

## Related Topics

- [DuckDB Integration Use Case](/use-cases/duckdb-integration)
- [open_iterable()](/api/open-iterable) - Opening files with engines
- [Database Engines](/api/database-engines) - Database engine documentation
- [Supported Formats](/formats/)
