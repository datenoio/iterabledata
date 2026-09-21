## 1. Packaging extras

- [x] 1.1 Add `lakehouse` extra (`deltalake`, `pyiceberg`, `pylance`; evaluate `pyhudi` availability) to `pyproject.toml`
- [x] 1.2 Add `cbor2` and `spacepy` to the `[all]` extra
- [x] 1.3 Audit remaining ImportError-raising formats and add extras or fold into existing groups (`avro`, `npy`, `ubj`, `vcf`, `ods`, `rda`/`rds`, `capnp`, `thrift`, `fbs`, `flexbuf`, `smile`, `edn`, `hocon`, `der`, `bencode`, `gpx`, `ics`, `ldif`)
- [x] 1.4 Update `[all]` to include every new pip-installable extra

## 2. Registry metadata

- [x] 2.1 Update `_MODULE_INSTALL_EXTRAS` so delta/iceberg/lance/hudi hints point at the new extras, not `[parquet]`
- [x] 2.2 Remove the incorrect "Read-only" limitation from `_LLM_METADATA["avro"]`
- [x] 2.3 Verify descriptor `writable` flags match implementations for all formats touched

## 3. Documentation

- [x] 3.1 Fix `docs/docs/formats/vcf.md` write-support statement
- [x] 3.2 Update README optional-dependency section for new extras

## 4. Tests

- [x] 4.1 Add test: every `install_extra_hint()` value exists as an extra in `pyproject.toml`
- [x] 4.2 Add test: `_LLM_METADATA` limitations do not claim "Read-only" for descriptors with `writable=True`
- [x] 4.3 Run `pytest tests/test_format_registry.py -v` and full lint suite
