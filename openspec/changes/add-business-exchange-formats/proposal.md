# Change: Add Business Exchange Formats (EDI, Access MDB, Lotus 123)

## Why

Dateno stats highlight business/desktop tabular gaps: EDI transaction sets (~1.9k), Microsoft Access `.mdb` (~950), and Lotus 1-2-3 (`.123`, ~600). These are record-oriented formats commonly found in government and enterprise open-data mirrors and fit IterableData's dict-row model beside XLS/XLSX/ODS/SQLite.

## What Changes

- Add EDI reading for a documented X12/EDIFACT subset as iterable transaction/segment records.
- Add Microsoft Access `.mdb` (and `.accdb` if practical) reading with table listing and selection.
- Add Lotus 1-2-3 `.123` spreadsheet reading as row dicts (read-oriented).
- Register formats, optional deps, fixtures, tests, and docs.

## Impact

- Affected specs: `business-exchange-formats` (new)
- Affected code: new datatypes, registry/detection, optional extras, docs/tests
- New dependencies: optional Access/Lotus/EDI libraries kept out of core
