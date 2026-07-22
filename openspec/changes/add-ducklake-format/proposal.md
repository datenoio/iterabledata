# Change: Add DuckLake Table Format Support

## Why

DuckLake is the newest mainstream open lakehouse table format: metadata lives in a SQL catalog (DuckDB/SQLite/Postgres/MySQL) and data lives in Parquet. IterableData already covers Delta, Iceberg, Hudi, Lance, Vortex, and Paimon file formats, but has no DuckLake path. Adding it closes the largest remaining table-format gap for embedded and DuckDB-centric lakehouses.

## What Changes

- Add experimental `DuckLakeIterable` for reading (and writing where the chosen SDK supports it) DuckLake tables as dictionary rows.
- Support catalog URI + table selection via `iterableargs` (and `list_tables()` for discoverable tables).
- Add optional `ducklake` extra pinning a reviewed Python SDK (`pyducklake` and/or `ducklake-sdk`) plus `duckdb`/`pyarrow` as required by that choice.
- Register format descriptor, docs, golden fixtures, and bounded batch iteration tests.
- Keep core install free of DuckLake dependencies.

## Impact

- Affected specs: `ducklake-format` (new)
- Affected code: new datatype module, format registry/detection, `pyproject.toml` extras, tests, fixtures, docs, README lakehouse list
- New dependency: optional DuckLake Python client (decision recorded in `design.md`)
- Maturity: **experimental** until round-trip and catalog-backend smoke tests pass
