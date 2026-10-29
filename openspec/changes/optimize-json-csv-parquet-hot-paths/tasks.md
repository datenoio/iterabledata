## 1. Benchmarks first

- [x] 1.1 Add the read, write and convert workloads from `design.md` to the performance suite (CSV/JSONL/JSON read, JSONL/CSV/Parquet write, CSV->JSONL, CSV->Parquet, JSONL->CSV).
- [x] 1.2 Record baselines on the reference environment before any code change (CI-like env: dev tools + PyArrow, no orjson/isal; numbers in the PR).

## 2. JSON backend

- [x] 2.1 Add `iterable/helpers/jsonbackend.py` (`make_decoder`, `make_encoder`, `make_lines_encoder`): msgspec decoding, orjson encoding, stdlib fallback; identical values, identical bytes except floats below 1e-4 (see design).
- [x] 2.2 Add the `fast` extra (`orjson`, `msgspec`, `isal`) to `pyproject.toml` and the `ITERABLEDATA_JSON_BACKEND` override for tests.
- [x] 2.3 Use the backend in `JSONLinesIterable` (`islice` batching in `read_bulk`, no per-line `strip()` on success) and `JSONIterable` (in-memory load). Bytes-mode reading was not adopted (see design).
- [x] 2.4 Tests (`tests/test_json_backend.py`, CI `optional-fast` leg): both backends; byte-identical output; stdlib fallback for NaN literals; exact >64-bit integers.

## 3. CSV

- [x] 3.1 Replace `DictReader` with `csv.reader` + `dict(zip())` keeping short/long-row semantics.
- [x] 3.2 Remove per-row `tell()` on the success path; keep byte offsets when `on_error != "raise"` or debug is on.
- [x] 3.3 Replace `DictWriter` with `csv.writer` + key projection, keeping `extrasaction="raise"` behavior.
- [x] 3.4 Tests (`tests/test_csv_fast_path.py`): short rows, long rows, quoted newlines, BOM, custom dialects, error diagnostics, all compared with `DictReader`/`DictWriter`.

## 4. Parquet writer

- [x] 4.1 Convert each batch to Arrow once; buffer Arrow batches; flush at `row_group_size`.
- [x] 4.2 Skip `normalize_extended_json` for batches without dict values (decided from the Arrow result, see design).
- [x] 4.3 Tests (`tests/test_parquet_write_path.py`): schema alignment errors still raised at the offending batch; row-group layout unchanged.

## 5. Columnar CSV path

- [x] 5.1 Add a CSV native batch reader on `pyarrow.csv.open_csv` with all-string columns and the CSV dialect options; declare `native_bulk_read` in the registry. Arrow batches go to Parquet and Arrow IPC writers (ORC uses pyorc and keeps the row path).
- [x] 5.2 Tests (`tests/test_csv_native_batches.py`): CSV -> Parquet via the native path matches the row path value for value (empty fields stay `""`).

## 6. gzip

- [x] 6.1 Use `isal.igzip` (or `igzip_threaded` for `profile="fast"`) for gzip writes when installed, at levels 1-2 where the ratio matches zlib (see design).
- [x] 6.2 Add an opt-in gzip read backend option (`backend="isal"`). Read defaults are unchanged; a Linux x86-64 benchmark is still needed before changing them.

## 7. Wrap-up

- [x] 7.1 Re-run the gate, update baselines intentionally, and document results in `docs/docs/getting-started/performance.md`.
- [x] 7.2 Note the compact JSON output in `CHANGELOG.md`.
- [x] 7.3 Run `ruff check iterable tests`, `ruff format --check iterable tests` and the full suite.
