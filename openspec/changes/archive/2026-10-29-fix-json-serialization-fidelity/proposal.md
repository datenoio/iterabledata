# Change: Fix lossy JSON value serialization and float decoding

## Why

undatum's DuckDB-vs-Python contract tests found that iterabledata's JSON Lines writer replaces
`datetime.time` values with `null`. The root cause is wider: `jsonl.date_handler` returns `None` for
every type other than `date`/`datetime`, so `Decimal`, `UUID`, `bytes`, `timedelta`, `time` and
`set` values are silently written as `null` (verified on 1.0.23). The same values are written as
`str()` by the JSON writer, so the two JSON writers disagree.

The defect compounds with the JSON reader: files larger than 10 MB are streamed through `ijson`
without `use_float=True`, so every float becomes `Decimal` (smaller files go through `json.load`
and yield `float`). Converting a large `.json` file to `.jsonl` therefore writes `null` for every
fractional number — reproduced with `convert("big.json", "out.jsonl")` on a 15 MB file. Parquet
`DECIMAL` columns and database `NUMERIC` columns hit the same path.

## What Changes

- Add one shared JSON value encoder (`iterable/helpers/jsonvalues.py`) used by every JSON text
  writer (`jsonl`, `geojsonseq`, `json`, `gelf`, `jsonld`, `geojson`, `topojson`, `czml`).
- Encode `date`/`datetime`/`time` as ISO 8601, `Decimal` as a JSON number when the shortest float repr equals it
  and as a string otherwise (`decimal="string"` forces strings), `UUID` as its canonical string,
  `bytes` as base64, `timedelta` as ISO 8601 duration, `set`/`frozenset`/`tuple` as arrays, and
  NumPy scalars via `.item()`. Other objects are written as `str(value)` (the JSON writer's current
  behavior); `on_unknown_type="raise"` turns them into `WriteError`.
- Never emit `null` for a non-`None` value.
- Stream large JSON arrays with `ijson.items(..., use_float=True)` so the same file yields the same
  Python types regardless of size.
- **Visible change:** JSON writer output for `bytes` changes from the Python repr (`"b'\\x01'"`)
  to base64; `Decimal` changes from a quoted string to a number.

## Impact

- Affected specs: `datatype-implementation`
- Affected code: `iterable/datatypes/{jsonl,json,gelf,jsonld,geojson,topojson,czml,otlp}.py`, new
  `iterable/helpers/jsonvalues.py`
- Affected tests: new type-fidelity matrix for every JSON-family writer; JSON reader size-parity test
- Downstream: undatum can drop the `TIME` exclusion from its engine contract tests
