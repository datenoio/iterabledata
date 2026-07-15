# Change: Report streaming capability truthfully across all formats

## Why

Only 7 of 108 formats override `is_streaming()`; everything else returns the base-class default `False`, including genuinely streaming readers (ORC, Avro, BSON, MessagePack, PCAP, SQLite). Conversely, full-load formats (Arrow, Lance, Delta, Iceberg, Hudi, Shapefile, CBOR, YAML, TOML) report nothing that distinguishes them, so users, the capability API, and the AI conversion planner cannot reason about memory behavior.

## What Changes

- Override `is_streaming()` to return `True` in every format whose read path is genuinely incremental (at minimum: ORC, Avro, BSON, MessagePack, PCAP, SQLite, LTSV-per-line readers).
- Ensure full-load formats explicitly return `False` and document the memory behavior in their class docstrings.
- Surface the flag through the capability API (`get_format_capabilities()["streaming"]`) without `None` for built-in formats whose behavior is known.
- Add a conformance test asserting the `is_streaming()` declaration matches an allowlist derived from the performance review, so future formats must declare their behavior deliberately.

## Impact

- Affected specs: `datatype-implementation`
- Affected code: ~15 modules under `iterable/datatypes/`, `iterable/helpers/capabilities.py`, `tests/test_format_conformance.py`
- No behavioral change to reading/writing; only capability reporting.
