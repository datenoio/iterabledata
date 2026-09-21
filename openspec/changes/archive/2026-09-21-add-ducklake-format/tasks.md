## 1. Dependency and registration

- [x] 1.1 Bake off and pin one DuckLake Python SDK in a `ducklake` optional extra; document install hints.
- [x] 1.2 Add `ducklake` format descriptor (experimental) without hijacking plain `.duckdb` detection.
- [x] 1.3 Raise clear `ImportError` / selection errors for missing deps and ambiguous tables.

## 2. Read and discovery

- [x] 2.1 Implement `DuckLakeIterable` opening a catalog + table and streaming Arrow batches to dict rows.
- [x] 2.2 Implement `list_tables()` for discoverable tables in the attached catalog.
- [x] 2.3 Implement `reset()`, `totals()`, and bounded `read`/`read_bulk` contracts.

## 3. Write path

- [x] 3.1 Implement create/append writes when the chosen SDK supports them; otherwise document read-only and keep `writable=False`.
- [x] 3.2 Flush at `batch_size` and declare write-memory capability truthfully.

## 4. Tests and docs

- [x] 4.1 Add local catalog fixtures and round-trip/discovery/missing-dependency tests.
- [x] 4.2 Document usage, catalog backends, and limitations; update README lakehouse list.
- [x] 4.3 Run targeted tests and `openspec validate add-ducklake-format --strict`.
