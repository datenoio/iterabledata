# Change: Speed up CSV, JSON Lines, JSON and Parquet hot paths

## Why

undatum benchmarks show the Python (iterabledata) path is 12-43x slower than DuckDB for `convert`
and `dedup`, and undatum now routes CSV/JSON/JSONL/Parquet conversions around iterabledata. A
review benchmark on 500k rows (see `design.md`) shows where the time goes:

- JSON Lines parsing and serialization use the stdlib `json` module. `orjson` reads 3.3x faster
  (0.34 s vs 1.13 s) and writes 7.5x faster (0.19 s vs 1.42 s); `msgspec` is comparable.
- `JSONLinesIterable.read_bulk()` is slower than row iteration (1.41 s vs 1.13 s).
- CSV reading pays `DictReader` plus a per-row `tell()` that raises `OSError` on text files after
  `next()`; `csv.reader` + `dict(zip())` is 1.45x faster than the current path.
- The Parquet writer normalizes and converts every batch twice (validation, then flush):
  1.66 s vs 0.36 s for the same rows written directly with PyArrow (4.6x).
- `convert()` has no columnar path for CSV: CSV -> Parquet takes 2.85 s; streaming
  `pyarrow.csv.open_csv` into `ParquetWriter` takes 0.31 s (9x) with all values kept as text.
- gzip writing uses `zlib`; `isal.igzip_threaded` writes the same stream 5x faster.

## What Changes

- Add an internal JSON backend (`iterable/helpers/jsonbackend.py`) that decodes with `msgspec`
  and encodes with `orjson` when installed and uses the stdlib otherwise, with the same values
  and, except for floats below `1e-4`, the same bytes from both (compact separators, UTF-8,
  shared value encoder from `fix-json-serialization-fidelity`). Use it in JSONL/JSON readers
  and writers. Add an optional `fast` extra (`orjson`, `msgspec`, `isal`).
- Batch JSON Lines `read_bulk()` with `islice` and no per-line `strip()`/`rstrip()` on the
  success path.
- Replace `DictReader`/`DictWriter` on the CSV hot path with `csv.reader`/`csv.writer` while
  keeping `DictReader` semantics for short and long rows; remove per-row `tell()` unless
  `on_error != "raise"` or debug is on.
- Parquet writer: convert each batch to Arrow once, buffer Arrow batches, and skip the extended
  JSON walk when a batch has no nested values.
- Add a native Arrow batch reader for CSV (all columns as strings) so `convert(..., use_native_batch=True)`
  and auto-native pairs stream CSV -> Parquet/Arrow/ORC without Python dicts.
- Use `isal` (when installed) for gzip writes at levels 1-2, where its ratio matches zlib, and
  as an opt-in gzip backend for other levels and for reads.
- Extend the performance regression gate with these workloads.
- **Visible changes:** JSON and JSON Lines output becomes compact (`{"a":1}` instead of
  `{"a": 1}`), NaN and infinities are written as `null` instead of invalid `NaN`, and `Enum`
  members are written as their value; other values are unchanged.

## Impact

- Affected specs: `datatype-implementation`, `native-batch-io`, `compression-codecs`,
  `performance-regression`
- Affected code: `iterable/datatypes/{jsonl,json,csv,parquet}.py`, new
  `iterable/helpers/jsonbackend.py`, `iterable/codecs/gzipcodec.py`, `iterable/convert/core.py`,
  `pyproject.toml`, `tests/performance_baselines.json`
- Depends on: `fix-json-serialization-fidelity` (shared encoder), `fix-csv-dialect-and-codec-options`
  (dialect handling must land before the CSV rewrite)
- Out of scope: Polars or DuckDB as row readers (no gain once rows become dicts; see `design.md`)
