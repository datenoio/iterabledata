# Tasks

## 1. XLSX write support

- [ ] 1.1 Implement buffered `write()`/`write_bulk()` for `XLSXIterable` via openpyxl, materializing on `close()`.
- [ ] 1.2 Round-trip tests: values, types (numbers/booleans/dates), multiple sheets default, reader compatibility.
- [ ] 1.3 Wire write-time validation hooks consistent with `validation-consistency`.

## 2. XML write support

- [ ] 2.1 Implement `write()`/`write_bulk()` for `XMLIterable` honoring the configured `tagname` and root element.
- [ ] 2.2 Round-trip tests including attribute/child flattening conventions of the reader.

## 3. ODS write support

- [ ] 3.1 Implement buffered `write()`/`write_bulk()` for `ODSIterable` via odfpy, replacing the `WriteNotSupportedError` stubs.
- [ ] 3.2 Round-trip tests with typed cells and reader compatibility.

## 4. Registry, capabilities, docs

- [ ] 4.1 Flip `writable=True` and update memory-profile descriptors for xlsx/xml/ods; keep conformance tests green.
- [ ] 4.2 Update format doc pages (write examples, buffering limitation) and README format table.
- [ ] 4.3 Update CHANGELOG `[Unreleased]`.

## 5. Verification

- [ ] 5.1 Full serial suite green; ruff/format clean; blocking mypy gate unaffected.
- [ ] 5.2 Convert pipeline round-trips csv→xlsx→csv, jsonl→xml→jsonl, csv→ods→csv pass via the public API.
