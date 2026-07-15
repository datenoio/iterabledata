# Change: Reconcile format dependency extras and descriptor metadata

## Why

The 2026-07-14 repository review found that several advertised formats cannot be installed through any `pyproject.toml` extra (lakehouse formats `delta`, `iceberg`, `hudi`, `lance` have no declared dependencies at all and their install hints misleadingly point at `[parquet]`), the `[all]` group omits existing extras (`cbor`, `cdf`), and descriptor metadata contradicts implementations (Avro `_LLM_METADATA` says "Read-only" while Avro write shipped in 1.0.14; `docs/docs/formats/vcf.md` says writing is unsupported while `vcf.py` implements `write()`/`write_bulk()`).

## What Changes

- Add dependency extras for lakehouse formats: a `lakehouse` extra (or individual `delta`/`iceberg`/`lance`/`hudi` extras) declaring `deltalake`, `pyiceberg`, `pylance`, and `pyhudi` where pip-installable.
- Fix `_MODULE_INSTALL_EXTRAS` in `iterable/helpers/format_registry.py` so install hints for delta/iceberg/lance no longer point at `[parquet]`.
- Add `cbor2` and `spacepy` (extras `cbor`, `cdf`) to the `[all]` group.
- Add dedicated extras (or fold into existing groups) for the long tail of formats that raise `ImportError` without a resolvable hint: `avro`, `npy`/`npz`, `ubj`, `vcf`, `ods`, `rda`/`rds`, `capnp`, `thrift`, `fbs`, `flexbuf`, `smile`, `edn`, `hocon`, `der`, `bencode`, `gpx`, `ics`, `ldif`.
- Correct the Avro "Read-only" limitation string in `_LLM_METADATA`.
- Correct the write-support claim in `docs/docs/formats/vcf.md`.
- Add a regression test asserting every `install_extra_hint()` value resolves to an existing extra in `pyproject.toml`, and that the extra installs the module's required package(s).

## Impact

- Affected specs: `format-registry`
- Affected code: `pyproject.toml`, `iterable/helpers/format_registry.py` (`_MODULE_INSTALL_EXTRAS`, `_LLM_METADATA`), `docs/docs/formats/vcf.md`, `tests/test_format_registry.py`
- No runtime behavior change for installed users; improves installability and hint accuracy.
