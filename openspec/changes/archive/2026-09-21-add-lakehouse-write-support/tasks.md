## 1. Shared write groundwork

- [x] 1.1 Define shared Arrow conversion / batch flush helpers reusable by Delta, Iceberg, and Hudi writers.
- [x] 1.2 Document per-format write modes and schema rules in format docs.

## 2. Delta Lake writes

- [x] 2.1 Implement create/overwrite/append via `deltalake` with bounded flush.
- [x] 2.2 Mark Delta descriptor writable; add round-trip and schema-mismatch tests.

## 3. Iceberg writes

- [x] 3.1 Implement append (and create/overwrite if safe) via PyIceberg using existing catalog/table options.
- [x] 3.2 Mark Iceberg descriptor writable; add round-trip tests for filesystem/catalog fixtures.

## 4. Hudi writes

- [x] 4.1 Evaluate Hudi Python write APIs; implement supported append/COW subset or explicitly defer with task/docs note.
- [x] 4.2 If implemented, mark Hudi descriptor writable and add round-trip tests; otherwise keep read-only and record follow-up.

## 5. Validation

- [x] 5.1 Update README/capability notes for writable lakehouse formats.
- [x] 5.2 Run targeted tests and `openspec validate add-lakehouse-write-support --strict`.
