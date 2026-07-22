## Context

DuckLake stores table metadata in a relational catalog and data files as Parquet. Official access is via the DuckDB `ducklake` extension (`ATTACH 'ducklake:...'`). Community Python SDKs include `pyducklake` (pyiceberg-like API over DuckDB) and `ducklake-sdk` (standalone Rust/Python client, import `ducklake`).

IterableData already patterns lakehouse tables after Iceberg/Delta/Hudi: path or catalog args, `list_tables()`, Arrow-batch → dict rows, optional extras.

## Goals / Non-Goals

- Goals:
  - Open a DuckLake table through `open_iterable()` and iterate dictionary rows with bounded memory.
  - Discover tables via `list_tables()` when a catalog is attached.
  - Support local DuckDB/SQLite catalogs first; document Postgres/MySQL when the SDK allows.
  - Prefer append/create writes when the SDK exposes stable APIs.
- Non-Goals:
  - Reimplementing the DuckLake spec in pure Python.
  - Full catalog administration UI (create catalog only as needed for tests).
  - Replacing the existing DuckDB **engine** (`engine='duckdb'`) for CSV/JSONL files.

## Decisions

### Backend selection

Prefer **`pyducklake`** if it remains pip-installable and exposes streaming Arrow batch readers aligned with Iceberg-style scans. Fall back to **`ducklake-sdk`** (`import ducklake`) if `pyducklake` is unsuitable. Record the pinned package and minimum version in `pyproject.toml` and docs. Do not depend on two competing SDKs at once.

### Format identity

- Canonical id: `ducklake`
- Aliases: none initially (avoid colliding with `duckdb` engine/database files)
- Detection: explicit `format="ducklake"` or path/URI patterns documented for metadata files (e.g. `*.ducklake` / catalog URI), not silent takeover of arbitrary `.duckdb` files

### Open contract

```python
open_iterable(
    "meta.duckdb",  # or ducklake URI / catalog path
    iterableargs={
        "format": "ducklake",
        "table": "main.events",   # or table_name=
        "data_path": "./data",    # when required by catalog
        # catalog backend options as needed
    },
)
```

Ambiguous catalogs with multiple tables require explicit table selection (same pattern as Zarr/Iceberg).

### Row iteration and writes

- Read via Arrow batch reader / dataset scan; convert with existing helpers.
- Writes (if enabled): append batches through the SDK; flush at `batch_size`; declare `write_memory` accurately.
- `totals()` uses SDK count/metadata when available.

## Risks / Trade-offs

- **SDK churn / unofficial clients** → Pin versions; mark experimental; prefer APIs with Arrow batch streaming.
- **Confusion with DuckDB database files** → Never auto-detect plain `.duckdb` as DuckLake without explicit format or DuckLake attach metadata.
- **Remote catalogs** → Phase 1 local only; remote backends opt-in and tested separately.

## Migration Plan

1. Dependency + descriptor + read path for single-table local catalogs.
2. `list_tables()` + multi-table selection errors.
3. Optional append/create write path.
4. Docs and fixtures; stabilize after interoperability checks.

## Open Questions

- Exact preferred SDK after a short bake-off (`pyducklake` vs `ducklake-sdk`).
- Whether `engine='duckdb'` should gain a first-class DuckLake attach shortcut or stay separate from `DuckLakeIterable`.
