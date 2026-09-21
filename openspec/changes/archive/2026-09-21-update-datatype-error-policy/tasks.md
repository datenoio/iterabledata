## 1. Contract and helpers

- [x] 1.1 Document the error-policy contract in `iterable/base.py` docstrings (parse failure → `_handle_error()` → `FormatParseError` by default)
- [x] 1.2 Provide a small mixin/helper so formats can wrap their iterator setup and record loops without copy-paste

## 2. Migrate silent-failure offenders

- [x] 2.1 `smile.py`: raise `FormatParseError` instead of setting `self.items = []` on parse failure
- [x] 2.2 `hudi.py`: raise `ReadError`/`ImportError` instead of substituting `iter([])`; make `list_tables()` distinguish dependency, path, and parse errors
- [x] 2.3 `vcf.py`: route fallback parsing through `_handle_error()` with `FormatParseError` context
- [x] 2.4 `parquet.py`: surface write-alignment failures instead of buffering silently
- [x] 2.5 `open_iterable.py`: replace silent CSV fallback on stream-detection failure with a warning (or error) naming the detection failure
- [x] 2.6 `open_iterable.py`: raise `IterableDataError` subclasses instead of `RuntimeError` at the API boundary

## 3. Conformance tests

- [x] 3.1 Add malformed-fixture conformance test: malformed non-empty input MUST NOT yield zero rows silently under default `on_error="raise"`
- [x] 3.2 Add tests for `on_error="skip"` and `"warn"` behavior on at least SMILE, VCF, and Parquet
- [x] 3.3 Run full suite and lint

## 4. Follow-up audit

- [x] 4.1 Grep-audit remaining `except Exception` blocks in `iterable/datatypes/` and classify (re-raise typed / log+skip / narrow); file follow-up items for the long tail (see `audit.md`)
