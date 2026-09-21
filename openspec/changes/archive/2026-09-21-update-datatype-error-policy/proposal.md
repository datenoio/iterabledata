# Change: Adopt centralized error policy across datatype implementations

## Why

The centralized error policy (`BaseFileIterable._handle_error()` with `on_error="raise"|"skip"|"warn"`) is used by only 3 of ~110 format modules; the rest bypass it via 296 `except Exception` blocks. Several formats silently convert parse failures into empty datasets (`smile.py:53-66` sets `self.items = []`, `hudi.py:90` substitutes an empty iterator, `open_iterable.py:107-108` silently falls back to CSV on stream-detection failure), so malformed files read as valid zero-row datasets — a data-loss hazard for ETL pipelines. The public API boundary also raises generic `RuntimeError` instead of `IterableDataError` subclasses (`open_iterable.py:119-120, 365-372`).

## What Changes

- Establish a normative error-handling contract for datatype implementations: parse failures MUST surface through the `on_error` policy (default `raise` with `FormatParseError`), never as silently empty results.
- Migrate the known silent-failure offenders first: SMILE, Hudi, VCF, Parquet write-alignment buffering, and the CSV stream fallback in `open_iterable`.
- Replace generic `RuntimeError`/`ValueError` raised at the `open_iterable()` boundary with `IterableDataError` subclasses.
- Add conformance tests: for every format with a golden fixture, a malformed non-empty file MUST NOT read as zero rows unless `on_error="skip"` is set.
- **BREAKING** (behavioral): files that previously read as empty due to swallowed parse errors will now raise `FormatParseError` by default.

## Impact

- Affected specs: `error-handling` (new capability)
- Affected code: `iterable/datatypes/smile.py`, `hudi.py`, `vcf.py`, `parquet.py`, `iterable/helpers/open_iterable.py`, `iterable/base.py`, `tests/test_format_conformance.py`
- Existing `on_error` semantics in `csv.py`/`jsonl.py`/`xml.py` are unchanged; this extends them to the remaining formats incrementally.
