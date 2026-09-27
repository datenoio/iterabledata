# Change: Add Write Support for XLSX, XML, and ODS

## Why

XLSX, XML, and ODS are the highest-demand read-only formats remaining in the
registry (improvement plan 2026-09 §6.1). All three have write-capable backing
libraries already declared as optional extras (`openpyxl` for xlsx, stdlib
`xml.sax`/writer machinery for xml, `odfpy` for ods), so closing the gap is an
implementation exercise, not a dependency decision. Write support makes the
convert pipeline symmetric for the most common office interchange formats.

## What Changes

- Implement `write()`/`write_bulk()` for `XLSXIterable` (openpyxl), `XMLIterable`
  (stdlib, respecting the configured `tagname`), and `ODSIterable` (odfpy).
- Buffered writers: spreadsheet documents are single-file containers, so rows
  accumulate in memory and materialize on `close()`; memory profile descriptors
  are updated accordingly (write = full-buffer).
- Round-trip fidelity: written files must be readable by the format's own
  reader and by the backing library, verified by round-trip tests including
  typed values (numbers, booleans, dates) where the format supports them.
- Detection/registry: format descriptors flip `writable=True`; capability
  conformance tests updated.
- Documentation: format pages gain write usage examples; Limitations sections
  record the buffering behavior.

## Dependencies

- Coordinate with `validation-consistency` hooks so write-time validation
  applies uniformly (plan 6.4 will extend hooks repo-wide; this change wires
  them for these three formats only).

## Impact

- Affected specs: new `office-format-writes` capability; descriptor updates
  under `format-registry` conventions.
- Affected code: `iterable/datatypes/xlsx.py`, `xml.py`, `ods.py`,
  `iterable/helpers/format_registry.py`, tests, docs.
- No new dependencies: openpyxl, odfpy, and stdlib XML are already extras.

## Non-goals

- HDF5/NetCDF write support (deferred per plan 6.1 phasing).
- XLSX styling, formulas, charts; ODS styles; XML namespaces beyond the
  existing reader's conventions.
