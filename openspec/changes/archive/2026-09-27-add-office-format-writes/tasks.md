# Tasks

## 1. XLSX write support

- [x] 1.1 Implement buffered `write()`/`write_bulk()` for `XLSXIterable` via openpyxl, materializing on `close()`.
- [x] 1.2 Round-trip tests: values, types (numbers/booleans/dates), multiple sheets default, reader compatibility.
- [x] 1.3 Wire write-time validation hooks consistent with `validation-consistency`.

## 2. XML write support

- [x] 2.1 Implement `write()`/`write_bulk()` for `XMLIterable` honoring the configured `tagname` and root element.
- [x] 2.2 Round-trip tests including attribute/child flattening conventions of the reader.

## 3. ODS write support

- [x] 3.1 Implement buffered `write()`/`write_bulk()` for `ODSIterable` via odfpy, replacing the `WriteNotSupportedError` stubs.
- [x] 3.2 Round-trip tests with typed cells and reader compatibility.

## 4. Registry, capabilities, docs

- [x] 4.1 Flip `writable=True` and update memory-profile descriptors for xlsx/xml/ods; keep conformance tests green.
- [x] 4.2 Update format doc pages (write examples, buffering limitation) and README format table.
- [x] 4.3 Update CHANGELOG `[Unreleased]`.

## 5. Verification

- [x] 5.1 Full serial suite green; ruff/format clean; blocking mypy gate unaffected.
- [x] 5.2 Convert pipeline round-trips csv→xlsx→csv, jsonl→xml→jsonl, csv→ods→csv pass via the public API.
