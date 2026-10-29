# Change: Stop `convert()` from silently dropping rows

## Why

Found while benchmarking the paths undatum uses: `convert("n.jsonl", "n.csv")` on 25,000 records
with a nested field (`{"id": 1, "meta": {"a": 1}}`) writes only the CSV header and returns
`ConversionResult(rows_in=25000, rows_out=0)` without raising.

Two defects combine:

1. For flat outputs without `is_flatten=True`, `_scan_schema_keys()` collects dotted paths
   (`meta.a`) from `dict_generator()`, but `_run_write_loop()` appends the unflattened rows. Every
   `DictWriter.writerows()` call then fails with `dict contains fields not in fieldnames: 'meta'`.
   A field that first appears after `scan_limit` rows fails the same way.
2. `_flush_batch()` catches every write exception, appends it to `metrics.errors`, logs it and
   continues. The whole batch is lost, and the caller only learns about it by inspecting
   `result.errors`.

## What Changes

- When the output format is flat-only, `convert()` flattens records with the same function that
  produced the header keys, whether or not `is_flatten` is set: nested objects become dotted
  columns and lists become JSON text (`is_flatten=True` keeps the legacy `make_flat` form).
- Fields that are not in the header (first seen after `scan_limit`) are handled by a
  `extra_fields` policy: `"raise"` (default, `WriteError` naming the fields) or `"ignore"`.
- Batch write failures raise `WriteError` by default. A new `on_write_error="skip"` keeps the
  current behavior for callers that want it, and `ConversionResult` reports `rows_skipped`.
- **Behavior change:** callers that relied on `convert()` returning normally after write errors now
  get an exception unless they pass `on_write_error="skip"`.

## Impact

- Affected specs: `convert`
- Affected code: `iterable/convert/core.py`, `iterable/types.py` (`ConversionResult.rows_skipped`)
- Affected tests: `tests/test_convert*.py`
- Downstream: undatum `convert` reports a failure instead of writing a header-only CSV
