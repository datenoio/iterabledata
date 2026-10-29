# IterableData — undatum Integration Review and Performance Plan (October 2026)

**Date:** 2026-10-28 · **Code state:** `main` @ `5f813e4`, version 1.0.23
**Method:** mined the undatum Claude Code sessions (2026-10-07 … 2026-10-28) and undatum's code
(`master`, `claude/duckdb-convert-copy`) for iterabledata defects and workarounds, reproduced each
one against this checkout, then benchmarked the CSV/JSON/JSONL/Parquet paths undatum uses.

---

## 1. Summary

- **8 defects reported or worked around in undatum, all still present in 1.0.23.** Three cause
  silent data loss or wrong parsing by default (JSON writers, `.tsv`, explicit format + codec).
- **2 more silent-data-loss defects found during this review:** large JSON files decode floats as
  `Decimal`, which the JSONL writer then writes as `null`; and `convert()` of nested JSON Lines to
  CSV writes a header-only file and returns normally.
- **undatum depends on private iterabledata names and monkeypatches `iterable.convert.core`** to
  pass CSV dialect options and codec arguments.
- **Performance:** the row path is limited by stdlib parsers and avoidable overhead. Measured
  headroom: JSONL read 3.3x, JSONL write 7.5x, Parquet write 4.6x, CSV read 1.45x, CSV -> Parquet
  9x with a columnar path, `import iterable` 0.42 s -> target < 0.1 s.

Six OpenSpec changes plan the work (all pass `openspec validate --strict`).

## 2. Defects found through undatum

| # | Defect (reproduced on 1.0.23) | Seen in undatum | Severity | Change |
|---|---|---|---|---|
| 1 | JSONL writer writes `null` for `time`, `Decimal`, `UUID`, `bytes`, `timedelta`, `set` (`date_handler` returns `None`) | engine contract tests, PR #77 | P0 data loss | `fix-json-serialization-fidelity` |
| 2 | JSON > 10 MB streams via `ijson` without `use_float` -> floats become `Decimal` -> `null` in JSONL | found in this review | P0 data loss | `fix-json-serialization-fidelity` |
| 3 | `convert()` nested JSONL -> CSV writes 0 rows; batch write errors are logged and swallowed | found in this review | P0 data loss | `fix-convert-silent-row-loss` |
| 4 | `delimiter`/`quotechar`/`keys` in `iterableargs` ignored by `CSVIterable` (read and write) | `open_path` workaround, `_with_csv_options` monkeypatch | P0 wrong parse | `fix-csv-dialect-and-codec-options` |
| 5 | `.tsv` read and written with commas | "`.tsv` came out with commas" | P0 wrong parse | `fix-csv-dialect-and-codec-options` |
| 6 | Explicit `format=` drops the codec: `x.csv.gz` parsed as raw bytes, `data.zip` fails | `_codec_safe_source` symlink workaround | P0 wrong parse | `fix-csv-dialect-and-codec-options` |
| 7 | `import iterable` loads every DB driver, pyarrow, numpy, httpx (0.42 s here, ~1 s in undatum) | lazy-import shims, CLI start-up | P1 | `fix-package-import-hygiene` |
| 8 | `iterable.ai` attribute is the `doc` module, breaking `mock.patch("iterable.ai.…")` | test rewrites | P1 | `fix-package-import-hygiene` |
| 9 | `iterable/ai/prompts/*.txt` missing from the wheel -> `ai.filter/plan/suggest` fail when installed | "missing AI prompt files in 1.0.21" | P1 | `fix-package-import-hygiene` |
| 10 | `convert()`/`bulk_convert()` lack `codecargs`; `bulk_convert()` lacks `use_native_batch`/`selection`/`strict_native` | `_with_codecargs` monkeypatch, signature filtering | P2 | `update-convert-api-parity` |
| 11 | Private names used downstream (`_get_codec_registry`, `_assemble_markdown`, `_run_metacrafter_scan`, …) | 6 private imports | P2 | `update-convert-api-parity` |
| 12 | `CSVIterable.totals()` counts the header and quoted newlines (4 for a 2-row file) | found in this review | P2 | `fix-csv-dialect-and-codec-options` |

Not defects: xlsx/ods/xml becoming writable (intended, `add-office-format-writes`); gzip id `gz`
vs `gzip` (undatum now accepts both; `list_codecs()` will document ids).

## 3. Performance findings

Full numbers and rejected options are in
`openspec/changes/archive/2026-10-29-optimize-json-csv-parquet-hot-paths/design.md` (500k rows, Apple M4 Max,
Python 3.13).

| Path | Now | Best measured alternative | Gain |
|---|---|---|---|
| JSONL read (dict rows) | 1.13 s | `orjson.loads` per line 0.34 s | 3.3x |
| JSONL `read_bulk` | 1.41 s (slower than row iteration) | same as above | 4x |
| JSONL write | 1.42 s | `orjson` 0.19 s / `msgspec` 0.12 s | 7.5-12x |
| CSV read | 0.94 s | `csv.reader` + `dict(zip())` 0.65 s | 1.45x |
| CSV write | 0.99 s | `csv.writer` + projection 0.72 s | 1.4x |
| Parquet write | 1.66 s | single Arrow conversion 0.36 s | 4.6x |
| CSV -> Parquet convert | 2.85 s | `pyarrow.csv.open_csv` -> `ParquetWriter` 0.31 s | 9x |
| gzip write (141 MB) | 1.01 s | `isal.igzip_threaded` 0.19 s | 5x |
| `import iterable` | 0.42 s | lazy optional imports (target < 0.1 s, not yet measured) | target ~4x |

Rejected: `pysimdjson` (7x slower than stdlib when rows are materialized), `pyarrow.json`/`pyarrow.csv`
for dict rows (`to_pylist` dominates), DuckDB for row iteration (no faster than `DictReader`),
Polars as a core backend (2.3x faster CSV-to-dict but ~150 MB runtime). For dict rows the
Python object creation is the floor; larger wins need columnar paths that never build dicts.

## 4. Order of work

1. **Release 1.0.24 (P0 correctness):** `fix-json-serialization-fidelity`,
   `fix-csv-dialect-and-codec-options`, `fix-convert-silent-row-loss` — implemented 2026-10-28
   (defects 1-6 and 12; 50 new tests), merged in PR #28, not yet released.
2. **Release 1.0.25 (P1 hygiene):** `fix-package-import-hygiene` (includes the wheel fix) —
   implemented 2026-10-29 (defects 7-9), merged in PR #30: `import iterable` 0.42 s -> 0.09 s.
3. **Release 1.1.0 (performance + API):** `optimize-json-csv-parquet-hot-paths` (after 1 and 2;
   it reuses the shared JSON encoder and the CSV dialect handling), `update-convert-api-parity` —
   both implemented 2026-10-29 (defects 10-11; JSONL write 5x and read 2x with `[fast]`, Parquet
   write 5x, CSV -> Parquet 2x, or 12x with `use_native_batch=True`; numbers in
   `docs/docs/getting-started/performance.md`); merged in PRs #31 and #32.

   All six changes are archived as `openspec/changes/archive/2026-10-29-*` with their spec deltas applied.
4. **undatum follow-up after each release:** remove `_with_csv_options`, `_with_codecargs`,
   `_codec_safe_source`, `_filter_bulk_convert_kwargs`, private imports, and the `TIME` exclusion
   in its engine contract tests; raise the `iterabledata` lower bound.

## 5. Test-suite baseline (this checkout)

`pytest tests -n 8 --no-cov` with Homebrew Python 3.13 and locally installed extras:
3127 passed, 440 skipped, 9 failed, 3 collection errors.

- 7 DBF failures (`test_dbf.py`, `test_openiterable.py::test_iterate_plain_dbf`): tests expect
  `ID`/`NAME`, the committed fixture has `id`/`name`. Hidden in environments without `dbfread`.
- `test_format_registry.py::test_totals_tables_match_implementation`: `jsonld` descriptor says
  `totals=False`, `JSONLDIterable.has_totals()` returns `True`.
- `test_validation_hooks_conformance.py[orc]`: pyorc rejects an int in a string struct field.
- 3 collection errors from fixture generator scripts collected as tests (missing optional deps).
- The worktree checkout materialized `tests/testdata` as a file (`core.symlinks=false`); restored
  per `AGENTS.md`.

These are outside the six changes; fix them in the next housekeeping pass.
