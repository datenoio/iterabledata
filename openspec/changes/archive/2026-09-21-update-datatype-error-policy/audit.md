# Follow-up audit: `except Exception` blocks in `iterable/datatypes/`

Task 4.1 of this change. Snapshot taken after migrating the known offenders
(SMILE, Hudi, VCF, Parquet, `open_iterable` stream fallback).

Total remaining `except Exception` blocks in `iterable/datatypes/`: **~96**
across ~45 modules (top counts: `dxf.py` 6, `warc.py` 5, `edn.py` 4,
`cdf.py` 4).

## Classification

### 1. Silent-empty on parse failure (data-loss hazard — migrate next)

These modules still convert whole-file parse failures into empty result sets
(`self.items = []` or equivalent inside `except Exception`). They should be
migrated to `BaseFileIterable._handle_parse_failure()` exactly as done for
SMILE in this change:

- `asn1.py` (reset: falls back to empty after multi-structure parse loop)
- `bencode.py` (two sites in reset)
- `capnp.py` (reset)
- `cbor.py` (two sites in reset)
- `edn.py` (two sites in reset)
- `flatbuffers.py` (reset)
- `flexbuffers.py` (two sites in reset)
- `gpx.py` (reset)
- `thrift.py` (reset)
- `ubjson.py` (reset)

### 2. Per-value/per-field fallbacks (acceptable — leave, optionally narrow)

Failures scoped to one field or one value where a documented fallback exists
(hex-encode, `None`, raw content). Not silent data loss; the record itself is
still yielded:

- `asn1.py:86`, `bencode.py:107` (value → hex fallback)
- `cdf.py:118` (field → `None`)
- `dxf.py:111,117` (geometry points → `None`)
- `warc.py:195,200` (content decode fallback)

### 3. Cleanup/close paths (acceptable — standard practice)

`except Exception: pass` around `close()`/release calls in `warc.py:56,267,274`,
`cdf.py:151`, and similar. Failing a close should not mask the original error.

### 4. Already typed (good examples, no action)

`dxf.py:47,56,66` and `cdf.py:81` wrap failures in `FormatParseError`/`ReadError`
with context; this is the target pattern for category 1.

## Follow-up items

1. Migrate category 1 modules (10 modules) to `_handle_parse_failure()`;
   one small PR per 2-3 formats, each with malformed-fixture tests mirroring
   `tests/test_error_policy.py`.
2. Extend `tests/test_error_policy.py` (or the conformance suite) with a
   parametrized malformed-input check as fixtures become available per format.
3. Optionally narrow category 2 handlers to the concrete exception types the
   underlying libraries raise.
