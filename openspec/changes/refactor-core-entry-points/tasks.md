## 1. open_iterable

- [x] 1.1 Extract detection, format/codec resolution, source validation, instantiation, and engine configuration into named helpers
- [x] 1.2 Keep the public `open_iterable()` signature and behavior identical
- [x] 1.3 Add unit tests for each extracted stage

## 2. convert / bulk_convert

- [x] 2.1 Extract read-plan, schema-scan, and write-loop helpers from `convert()`
- [x] 2.2 Refactor `bulk_convert()` to reuse the same helpers per file
- [x] 2.3 Add tests for the extracted helpers

## 3. Pipeline.run

- [x] 3.1 Extract per-stage execution into a helper; keep run orchestration thin

## 4. Verify

- [x] 4.1 Confirm radon complexity for each function is below C
- [x] 4.2 Run the full suite; behavior must be unchanged
- [x] 4.3 Lint and format
