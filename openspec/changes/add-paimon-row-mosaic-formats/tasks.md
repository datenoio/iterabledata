## 1. Dependencies and registration

- [x] 1.1 Add optional extras `paimon-row` (`pypaimon`), `paimon-mosaic` (`paimon-mosaic`), and convenience `paimon` to `pyproject.toml`; wire install hints in the format registry.
- [x] 1.2 Add format descriptors for `paimon_row` (`.row`) and `paimon_mosaic` (`.mosaic`) with experimental maturity, write support, and footer-magic metadata.
- [x] 1.3 Extend content detection for seekable sources to validate trailing 32-byte footers (`ROWS`, `MOSA`) without changing leading-magic matching.
- [x] 1.4 Raise clear `ImportError` messages naming the correct extra when dependencies are missing.

## 2. Paimon Mosaic iterable

- [x] 2.1 Implement `PaimonMosaicIterable` using `paimon-mosaic` (`mosaic.MosaicReader` / `MosaicWriter`) and PyArrow batch conversion.
- [x] 2.2 Stream row groups on read; apply `columns`/`project` via backend projection before decompression.
- [x] 2.3 Implement bounded batch writes (`write` / `write_bulk`), `reset()`, `totals()`, and context-manager cleanup.
- [x] 2.4 Declare streaming/write-memory capability truth accurately (row-group bounded vs whole-file).

## 3. Paimon Row iterable

- [x] 3.1 Implement `PaimonRowIterable` preferring pypaimon ROW file primitives; fall back to the published `.row` binary spec only if needed for standalone files.
- [x] 3.2 Require explicit schema on read; infer or accept explicit schema on write; fail clearly when schema is missing/incompatible.
- [x] 3.3 Implement block-oriented read/write, `reset()`, footer-based `totals()`, and optional row-number selection when supported.
- [x] 3.4 Document and test primitive type coverage; mark unsupported nested/VARIANT cases explicitly.

## 4. Tests and docs

- [x] 4.1 Add committed small golden fixtures (IterableData-produced) and, where feasible, one cross-tool fixture per format.
- [x] 4.2 Add tests for detection, read/bulk/reset/totals, round-trip, missing dependency, missing Row schema, projection (Mosaic), and malformed footers.
- [x] 4.3 Document both formats under `docs/docs/formats/`, update format index and README lakehouse list.
- [x] 4.4 Run targeted tests plus `openspec validate add-paimon-row-mosaic-formats --strict`.
