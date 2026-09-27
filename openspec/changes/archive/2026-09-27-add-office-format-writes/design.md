# Design: Office Format Writes

## Approach

All three targets are single-file document containers, so writers buffer rows
and materialize the document on `close()`. This matches how the lakehouse
writers already behave and keeps the implementation simple; the memory-profile
descriptor for each format records write = full-buffer.

## Per-format decisions

- **XLSX (openpyxl)**: create a `Workbook` lazily on first write; each record
  becomes one row in insertion order of dict keys (stable header from the
  first record, extended if later records add keys). Types map to openpyxl
  cell values directly (int/float/bool/str/datetime).
- **XML (stdlib)**: stream-write `<root><tagname>…</tagname>…</root>`;
  scalar dict values become child elements named by key, nested dicts/lists
  follow the reader's flattening conventions so round-trips hold.
- **ODS (odfpy)**: accumulate `TableRow`/`TableCell` entries and save on
  `close()`; cell types follow odfpy value attributes.

## Error handling

- Missing optional dependency → existing `ImportError` with install-hint path
  (openpyxl/odfpy already guarded at module level).
- Unsupported value types → the standard write-time validation error policy
  (`on_error` hooks) rather than silent stringification.

## Testing strategy

Round-trip tests per format (write → read → compare), backing-library
compatibility checks (openpyxl/odfpy can load what we wrote), validation-hook
tests, and public convert-pipeline round-trips (csv→xlsx→csv etc.).
