# Tasks

## 1. Implementation

- [x] 1.1 Validation consistency: update `write` and `write_bulk` in `iterable/datatypes/json.py` to call `_apply_validation_hooks`
- [x] 1.2 Validation consistency: update `iterable/datatypes/parquet.py` (write/write_bulk)
- [x] 1.3 Validation consistency: update `iterable/datatypes/sqlite.py` (write/write_bulk)
- [x] 1.4 Validation consistency: update `iterable/datatypes/topojson.py` (write/write_bulk)
- [x] 1.5 Audit other datatypes and apply validation hooks where `write`/`write_bulk` exist (jsonl, arrow, yaml added; remainder can follow in follow-up)
- [x] 1.6 SQLite optimization: implement `fetchmany` in `SQLiteIterable.read_bulk`
- [x] 1.7 TopoJSON fix: make `TopoJSONIterable.write_bulk` produce a single valid Topology JSON object (buffer + write on close)
- [x] 1.8 Add tests that validation hooks are triggered for json, parquet, sqlite, topojson
