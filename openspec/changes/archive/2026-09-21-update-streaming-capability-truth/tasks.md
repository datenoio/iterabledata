## 1. Streaming formats declare True

- [x] 1.1 Override `is_streaming()` to return `True` in genuinely incremental readers: `orc.py`, `avro.py`, `bsonf.py`, `msgpack.py`, `pcap.py`, `sqlite.py`, `ltsv.py`
- [x] 1.2 Audit remaining line/record-oriented text formats (apachelog, cdx, cef, gelf, ilp, ntriples, nquads) and declare `True` where the read path is incremental

## 2. Full-load formats declare False and document it

- [x] 2.1 Ensure `is_streaming()` returns `False` for full-load formats: `arrow.py`, `lance.py`, `delta.py`, `iceberg.py`, `hudi.py`, `shapefile.py`, `cbor.py`, `yaml.py`, `toml.py`
- [x] 2.2 Add a "Memory behavior" note to class docstrings of full-load formats stating the whole file/table is materialized

## 3. Capability API surfacing

- [x] 3.1 Ensure `get_format_capabilities()` reports `streaming` as True/False (not None) for all built-in formats whose behavior is known
- [x] 3.2 Update `iterable/helpers/capabilities.py` inference so it does not guess when the class declares explicitly

## 4. Conformance tests

- [x] 4.1 Add conformance test comparing each format's `is_streaming()` declaration against a reviewed allowlist in `tests/test_format_conformance.py`
- [x] 4.2 Run `pytest tests/test_format_conformance.py tests/test_capabilities.py -v` and lint
