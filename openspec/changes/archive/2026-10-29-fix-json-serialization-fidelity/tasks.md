## 1. Shared encoder

- [x] 1.1 Add `iterable/helpers/jsonvalues.py` with `encode_default(obj)` and the type table from the proposal.
- [x] 1.2 Add `decimal` (`"auto"` default: number when `Decimal(repr(float(d))) == d`, else string; `"string"`) and `on_unknown_type` (`"str"` default, `"raise"`) writer options.
- [x] 1.3 Replace `date_handler`/`default=str` in the JSON text writers: `jsonl` (and `geojsonseq` through it), `json`, `gelf`, `jsonld`, `geojson`, `topojson`, `czml`. Binary containers with JSON payloads (`recordio`, `tfrecord`, `kafka`, `pulsar`, `sequencefile`, `beam`, `flink`) raise `TypeError` on such values instead of writing `null` and are left for a follow-up.

## 2. Reader parity

- [x] 2.1 Pass `use_float=True` to every `ijson.items`/`ijson.kvitems` call used for record streaming (`json`, `geojson`, `topojson`, `czml`, `otlp`).
- [x] 2.2 Add a test that reads the same array through the in-memory and the streaming path (forced via `_should_use_streaming`) and asserts identical rows and types.

## 3. Tests and docs

- [x] 3.1 Add a round-trip matrix: `time`, `date`, `datetime` (naive and aware), `Decimal`, `UUID`, `bytes`, `timedelta`, `set`, NumPy scalar, `None` for every JSON-family writer; assert no `null` for non-`None` input.
- [x] 3.2 Add a regression test: `convert(big.json -> out.jsonl)` keeps fractional numbers.
- [x] 3.3 Document the encoding table and the visible changes in `CHANGELOG.md` and `docs/docs/formats/jsonl.md`.
- [x] 3.4 Run `ruff check iterable tests`, focused tests and the full suite.
