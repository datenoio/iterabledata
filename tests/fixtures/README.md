# Test fixtures

All committed test data lives in this directory.

## Layout

| Pattern | Purpose |
|---------|---------|
| `2cols6rows.*` | Shared golden read fixtures (CSV, Parquet, JSON, compressed variants, etc.) |
| `2cols6rows_test.*` | Write/round-trip outputs and codec-specific test copies |
| `2cols6rows_flat.*` / `2cols6rows_array.*` / `2cols6rows_tag.*` | JSON/JSONL shape variants |
| `books.*` | Secondary XML/JSONL fixture set |
| `ru_*` | Encoding/delimiter variants (UTF-8, CP1251) |
| `sample.*` | Small samples (WARC, GPX, KMZ) |
| `test_*` | Format-specific fixtures (zipxml, vortex, 7z, annotated CSV, etc.) |

## Paths in tests

`tests/conftest.py` changes the working directory to `tests/` before tests run, so use:

- **Preferred:** `fixtures/<name>` for new tests
- **Legacy alias:** `testdata/<name>` — symlink to `fixtures/` for backward compatibility

Helper:

```python
from tests.conftest import fixture_path  # or FIXTURES_DIR

path = fixture_path("2cols6rows.csv")
```

Ephemeral outputs created during tests should use `tmp_path` when possible. Do not create or delete files named like committed fixtures under `testdata/` — it is a symlink to `fixtures/` and will remove golden files.

## Repo root

The former repo-root `testdata/` directory was merged here. Do not add a new top-level `testdata/` directory.
