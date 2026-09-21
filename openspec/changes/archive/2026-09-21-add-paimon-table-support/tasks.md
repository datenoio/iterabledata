## 1. Dependency and registration

- [x] 1.1 Add `paimon-table` extra (`pypaimon`) and extend convenience `paimon` to include table + file deps; wire install hints.
- [x] 1.2 Register `paimon` / `PaimonTableIterable` descriptor (experimental) distinct from `paimon_row` / `paimon_mosaic`.
- [x] 1.3 Document and enforce format selection so `.row`/`.mosaic` keep file iterables.

## 2. Read and discovery

- [x] 2.1 Implement catalog/warehouse open + table load via PyPaimon.
- [x] 2.2 Implement bounded row iteration (`read`/`read_bulk`/`reset`/`totals`) from PyPaimon readers.
- [x] 2.3 Implement `list_tables()` for databases/tables with a documented naming scheme.
- [x] 2.4 Support optional projection and snapshot/tag options when exposed by PyPaimon.

## 3. Write path

- [x] 3.1 Implement append (or documented subset) writes with commit semantics and batch flush.
- [x] 3.2 Fail clearly for unsupported table kinds/write modes.

## 4. Tests and docs

- [x] 4.1 Add warehouse fixtures and tests for discovery, read, missing schema/table, missing dependency, and round-trip where writable.
- [x] 4.2 Document table vs file formats; update README/format index.
- [x] 4.3 Run targeted tests and `openspec validate add-paimon-table-support --strict`.
