# Design: CSV, JSON Lines, JSON and Parquet hot paths

## Context

Benchmark setup (2026-10-28): Apple M4 Max, Homebrew Python 3.13.7, iterabledata 1.0.23 from
this checkout. Data: 500,000 synthetic rows, 9 columns (id, date, category, city, amount, qty,
email with 10% empty, md5, text with commas and quotes). CSV 67 MB, JSON Lines 141 MB (adds a
nested `meta` object), JSON array 46 MB (200,000 rows). Library versions: orjson 3.11.5,
msgspec 0.22.0, pysimdjson, yyjson, polars 2.1.0, pyarrow 24.0.0,
duckdb 1.5.3, isal 1.8.0, zlib-ng 1.0.0, rapidgzip 0.16.0, ujson 6.0.0. Best of two runs. Every reader
materializes Python `dict` rows, because that is what the iterabledata API returns.

### Reading (dict rows)

| Path | CSV | JSONL |
|---|---|---|
| iterabledata, row iteration | 0.94 s | 1.13 s |
| iterabledata, `read_bulk(10000)` | 0.89 s | 1.41 s |
| stdlib `csv.DictReader` / `json.loads` | 0.79 s | 1.05 s |
| stdlib `csv.reader` + `dict(zip())` | 0.65 s | — |
| `orjson.loads` per line (bytes) | — | 0.34 s |
| `msgspec` `Decoder.decode` / `decode_lines` | — | 0.35 s / 0.36 s |
| `yyjson` / `ujson` | — | 0.43 s / 0.46 s |
| `pysimdjson` (`recursive=True`) | — | 7.46 s |
| `pyarrow` `open_csv` / `open_json` + `to_pylist` | 1.35 s | 2.39 s |
| `polars` `scan_csv(...).collect_batches()` + `to_dicts` | 0.40 s | — |
| `duckdb` `read_csv(all_varchar)` + `fetchmany` | 0.73 s | — |

JSON array (200k rows): iterabledata 0.75 s (ijson stream, `Decimal` floats), stdlib
`json.load` 0.24 s, `ijson.items` (yajl2_c) 0.26 s, `orjson.loads` 0.10 s, `msgspec` 0.10 s.

### Writing

| Path | Time |
|---|---|
| JSONL iterabledata `write_bulk` | 1.42 s |
| JSONL stdlib `json.dumps` join | 1.29 s |
| JSONL `orjson.dumps(OPT_APPEND_NEWLINE)` | 0.19 s |
| JSONL `msgspec` `Encoder.encode_lines` | 0.12 s |
| JSONL.gz iterabledata `write_bulk` | 2.30 s |
| CSV iterabledata `write_bulk` / `DictWriter` | 0.99 s / 1.02 s |
| CSV `csv.writer` + `itemgetter` | 0.72 s |
| Parquet iterabledata `write_bulk` | 1.66 s |
| Parquet `Table.from_pylist` + `ParquetWriter` | 0.36 s |

### gzip (141 MB of JSONL)

| Backend | Read | Write |
|---|---|---|
| stdlib `gzip` (level 6) | 0.07 s | 1.01 s |
| `isal.igzip` (level 2, similar ratio) | 0.41 s | 0.51 s |
| `isal.igzip_threaded` (4 threads) | 0.44 s | 0.19 s |
| `zlib_ng.gzip_ng` | 0.10 s | 0.68 s |
| `rapidgzip` (4 threads) | 0.09 s | — |

Reads were already fast with this Python build's zlib on Apple silicon; ISA-L's advantage is on
x86-64, so read backends need a per-platform benchmark before they become defaults.

### End-to-end `convert()`

| Pair | iterabledata | Reference |
|---|---|---|
| CSV -> JSONL | 2.45 s | 0.88 s (`csv.reader` + `orjson`) |
| CSV -> Parquet | 2.85 s (2.57 s with `use_native_batch`) | 0.31 s (`open_csv` -> `ParquetWriter`) |
| JSONL -> CSV | 2.98 s, 0 rows written (see `fix-convert-silent-row-loss`) | — |

## Goals / Non-Goals

- Goals: 2-3x faster CSV/JSONL row paths, 5x+ faster JSONL writes, 3x+ faster Parquet writes,
  a columnar CSV -> Parquet path, unchanged records and values.
- Non-Goals: replacing the row API, making Polars or DuckDB a reader backend, Rust extensions.

## Decisions

- **msgspec decodes, orjson encodes (revised during implementation).** `orjson.loads` turns
  integers beyond 64 bits into floats without an error (`18446744073709551616` ->
  `1.8446744073709552e+19`), which is silent data loss; detecting such lines costs more than the
  parse. `msgspec.json.Decoder` keeps them exact at the same speed (0.27 s vs 0.26 s for 200k
  lines) and parses floats identically to `json` (200k random doubles, 0 mismatches). For
  encoding `msgspec` cannot route datetimes, sets or `Decimal` through the shared encoder (it
  serializes them natively and differently), while `orjson` can (`OPT_PASSTHROUGH_DATETIME`,
  `OPT_PASSTHROUGH_DATACLASS`; sets and `Decimal` reach `default`). Hence `fast` =
  `orjson>=3.11.7`, `msgspec`, `isal`; orjson before 3.11.7 writes `1e16` instead of `1e+16`
  and is ignored.
- **Optional, auto-detected.** The base install stays `chardet` + `tqdm`. `iterabledata[fast]`
  pulls the accelerated libraries; the stdlib path remains and produces the same values.
- **Near byte-identical output across backends.** The stdlib writer switches to
  `separators=(",", ":")` and the shared encoder. NaN and infinities are written as `null` by
  both backends (stdlib used to write invalid `NaN`). Records orjson cannot encode (integers
  beyond 64 bits, non-string keys) fall back to the stdlib encoder per record. The one remaining
  byte difference: floats below `1e-4` (`orjson` `0.00001`, `json` `1e-05`). `Enum` members are
  encoded as their value by both (the shared encoder used to write `str(member)`).
- **Reader fallback.** When `msgspec` rejects a line, retry with `json.loads` before raising
  `FormatParseError`, so inputs the stdlib accepts today (for example `NaN` literals) still load.
- **JSON Lines stays a text stream.** Reading bytes would change `fobj` for subclasses
  (`GeoJSONSeqIterable`) and callers that pass text streams; `msgspec` decodes `str` directly.
- **CSV semantics.** Keep `DictReader` behavior exactly: missing trailing fields become `None`,
  extra fields go to the `None` key. The fast path handles rows whose length equals the header
  and defers to the general path otherwise.
- **Native CSV batches read every column as a string**, matching row-path values (no type
  inference, empty fields stay `""`), the same rule undatum uses for its DuckDB COPY path.
  They travel through a new optional Arrow protocol (`read_arrow_batches`/`write_arrow_batch`,
  `arrow_batch_supported()`), implemented by CSV (reader) and Parquet and Arrow IPC (writers);
  GeoParquet opts out because its schema metadata is added on the row path. ORC is written with
  pyorc, not PyArrow, so it keeps the row path. The native path stays opt-in
  (`use_native_batch=True`): PyArrow rejects ragged rows that the row path pads.
- **Parquet writes convert once and normalize lazily.** A batch is converted with
  `Table.from_pylist`; extended-JSON unwrapping runs only when that conversion fails or yields
  nested types, because a flat result proves the batch had no dict or list values.
- **gzip keeps zlib's ratios.** On this machine ISA-L level 3 is 1.3x faster than zlib 6 but its
  output is 14% larger (ratio 0.193 vs 0.169); ISA-L level 1 matches zlib 1 (0.213 vs 0.216).
  `backend="auto"` therefore uses ISA-L only at levels 1-2 (threaded for `profile="fast"`);
  `backend="isal"` opts in at any level and for reads; read defaults are unchanged.
- **Rejected:** `pysimdjson` (lazy proxies make full materialization 7x slower than stdlib),
  `pyarrow.json` and `pyarrow.csv` for dict rows (`to_pylist` dominates), DuckDB for row
  iteration (no faster than `DictReader` once rows are dicts), Polars (2.3x faster CSV-to-dict,
  but a ~150 MB runtime; undatum's engine analysis rejected it as a core dependency too).

## Risks / Trade-offs

- Compact JSON output changes bytes for users who diff files -> called out in CHANGELOG; values
  are unchanged.
- Two JSON backends double the test matrix -> run the JSON test modules with and without orjson
  (`ITERABLEDATA_JSON_BACKEND=stdlib`) in CI.
- Threaded gzip writes use more CPU -> only for `profile="fast"` or when the user opts in.

## Open Questions

- Should `orjson` become a core dependency instead of an extra once the fallback is proven?
- Is `msgspec`'s faster writer worth a second optional backend for JSONL-heavy users?
