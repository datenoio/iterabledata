## 1. Setup

- [x] 1.1 Add descriptors/aliases for `edi`, `mdb` (and `accdb` if in scope), and `123`.
- [x] 1.2 Add optional extras and ImportError messaging.
- [x] 1.3 Document EDI record granularity and spreadsheet header behavior.

## 2. Implementations

- [x] 2.1 Implement EDI iterable for the documented X12/EDIFACT subset.
- [x] 2.2 Implement Access MDB iterable with `list_tables()` and table selection.
- [x] 2.3 Implement Lotus 1-2-3 `.123` reader as row dicts.

## 3. Tests and docs

- [x] 3.1 Add fixtures for EDI, MDB, and Lotus 123.
- [x] 3.2 Add detection, multi-table, malformed, and optional-dependency tests.
- [x] 3.3 Document formats, limitations, and examples.
- [x] 3.4 Run `openspec validate add-business-exchange-formats --strict`.
