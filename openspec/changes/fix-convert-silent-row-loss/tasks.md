## 1. Consistent flattening

- [x] 1.1 For flat-only outputs, flatten every record with the same key function used by `_scan_schema_keys()`.
- [x] 1.2 Add `extra_fields` (`"raise"` default, `"ignore"`) for keys not seen during the schema scan.
- [x] 1.3 Tests: nested JSONL to CSV without `is_flatten`; a new field after `scan_limit` with each policy.

## 2. Write error policy

- [x] 2.1 Make `_flush_batch()` raise `WriteError` (with the batch row range) unless `on_write_error="skip"`.
- [x] 2.2 Add `rows_skipped` to `ConversionResult` and fill it in the skip mode.
- [x] 2.3 Apply the same policy in `bulk_convert()` and the native batch path.
- [x] 2.4 Tests: a failing writer raises by default; with `skip`, `rows_out + rows_skipped == rows_in`.

## 3. Verification

- [x] 3.1 Document the policies in `docs/docs/api/convert.md` and the behavior change in `CHANGELOG.md`.
- [x] 3.2 Run `ruff check iterable tests`, focused tests and the full suite.
