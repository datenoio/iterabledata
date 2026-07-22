## Context

Apache Paimon is a streaming-first lakehouse table format (LSM-style). File formats (`.row`, Mosaic, Parquet, etc.) sit under table metadata. IterableData already implements standalone Row/Mosaic file iterables. Full table access is provided by **PyPaimon** (`pip install pypaimon`): catalogs, databases, tables, batch read/write builders, and iterators.

## Goals / Non-Goals

- Goals:
  - Open a Paimon table via warehouse/catalog configuration and stream dictionary rows.
  - Discover databases/tables through `list_tables()` (documented naming scheme).
  - Support common read options (projection, snapshot/tag when available).
  - Support bounded batch writes/commits when PyPaimon write builders are stable enough.
- Non-Goals:
  - Replacing file-level `paimon_row` / `paimon_mosaic` iterables.
  - Implementing Flink/Spark runtime semantics inside IterableData.
  - Guaranteeing every merge-engine / changelog consumer mode in v1.

## Decisions

### Identity and coexistence

| Id | Role |
|----|------|
| `paimon` | Table iterable (`PaimonTableIterable`) |
| `paimon_row` / `row` | Standalone `.row` files |
| `paimon_mosaic` / `mosaic` | Standalone Mosaic files |

`format="paimon"` always means **table**. File extensions continue to select file iterables.

### Open contract

```python
open_iterable(
    warehouse_path_or_uri,
    iterableargs={
        "format": "paimon",
        "database": "default",
        "table": "orders",
        # catalog options / catalog_type as required by pypaimon
        "columns": ["id", "ts"],  # optional projection
    },
)
```

### Reads and writes

- Prefer `to_iterator` / Arrow batch APIs from PyPaimon read builders; never full-table pandas materialization on the hot path.
- Writes use batch write + commit builders; buffer at `batch_size`; document commit semantics (append vs upsert) and which table kinds are supported initially (start with append-only if upsert APIs are fragile).

### Extras

- `paimon-table = ["pypaimon>=…"]`
- Update convenience `paimon` to include `pypaimon` plus existing Row/Mosaic deps.

## Risks / Trade-offs

- **PyPaimon API evolution** → Pin versions; experimental maturity; capability tests.
- **User confusion file vs table** → Docs cross-link; distinct format ids.
- **Heavy optional deps** → Keep out of core and default `lakehouse` extra unless a follow-up explicitly expands `lakehouse`.

## Migration Plan

1. Read path + discovery for filesystem warehouse catalogs.
2. Projection / snapshot options as available.
3. Append write + commit for simple tables.
4. Docs clarifying file formats vs tables.

## Open Questions

- Minimum `pypaimon` version for stable standalone warehouse catalogs without JDK.
- Whether upsert/primary-key tables are in scope for the first writable release or read-only initially.
