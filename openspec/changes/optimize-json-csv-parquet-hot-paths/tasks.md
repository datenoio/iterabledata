## 1. Benchmarks first

- [ ] 1.1 Add the read, write and convert workloads from `design.md` to the performance suite (CSV/JSONL/JSON read, JSONL/CSV/Parquet write, CSV->JSONL, CSV->Parquet, JSONL->CSV).
- [ ] 1.2 Record baselines on the reference environment before any code change.

## 2. JSON backend

- [ ] 2.1 Add `iterable/helpers/jsonbackend.py` (`loads`, `dumps_line`, `dumps_lines`) with orjson and stdlib implementations producing identical bytes.
- [ ] 2.2 Add the `fast` extra (`orjson`, `isal`) to `pyproject.toml` and the `ITERABLEDATA_JSON_BACKEND` override for tests.
- [ ] 2.3 Use the backend in `JSONLinesIterable` (bytes-mode UTF-8 fast path, `islice` batching in `read_bulk`) and `JSONIterable` (in-memory load).
- [ ] 2.4 Tests: run JSON/JSONL suites under both backends; byte-identical output; stdlib fallback for NaN literals and >64-bit integers.

## 3. CSV

- [ ] 3.1 Replace `DictReader` with `csv.reader` + `dict(zip())` keeping short/long-row semantics.
- [ ] 3.2 Remove per-row `tell()` on the success path; keep byte offsets when `on_error != "raise"` or debug is on.
- [ ] 3.3 Replace `DictWriter` with `csv.writer` + key projection, keeping `extrasaction="raise"` behavior.
- [ ] 3.4 Tests: short rows, long rows, quoted newlines, BOM, custom dialects, error diagnostics.

## 4. Parquet writer

- [ ] 4.1 Convert each batch to Arrow once; buffer Arrow batches; flush at `row_group_size`.
- [ ] 4.2 Skip `normalize_extended_json` for batches without dict values.
- [ ] 4.3 Tests: schema alignment errors still raised at the offending batch; row-group layout unchanged.

## 5. Columnar CSV path

- [ ] 5.1 Add a CSV native batch reader on `pyarrow.csv.open_csv` with all-string columns and the CSV dialect options; declare `native_bulk_read` in the registry.
- [ ] 5.2 Tests: CSV -> Parquet via the native path matches the row path value for value (empty fields stay `""`).

## 6. gzip

- [ ] 6.1 Use `isal.igzip` (or `igzip_threaded` for `profile="fast"`) for gzip writes when installed.
- [ ] 6.2 Add an opt-in gzip read backend option; benchmark on Linux x86-64 before changing defaults.

## 7. Wrap-up

- [ ] 7.1 Re-run the gate, update baselines intentionally, and document results in `docs/docs/getting-started/performance.md`.
- [ ] 7.2 Note the compact JSON output in `CHANGELOG.md`.
- [ ] 7.3 Run `ruff check iterable tests`, `ruff format --check iterable tests` and the full suite.
