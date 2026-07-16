## 1. Dependency and registration

- [x] 1.1 Add a `zarr` optional extra and complete descriptor metadata with experimental maturity.
- [x] 1.2 Implement local `.zarr` and supported store detection without mistaking ordinary directories for Zarr.
- [x] 1.3 Add clear missing-dependency and unsupported-store errors.

## 2. Read and table behavior

- [x] 2.1 Implement group/array discovery and `list_tables()` array paths.
- [x] 2.2 Implement array selection and deterministic structured/dense/scalar row mappings.
- [ ] 2.3 Implement axis, slice, field, and chunk-aware bounded reading for v2 and v3 fixtures.
- [x] 2.4 Implement `read()`, `read_bulk()`, `reset()`, totals, and capability declarations consistently.

## 3. Write behavior

- [x] 3.1 Define explicit and first-batch schema/shape/dtype creation paths.
- [x] 3.2 Implement chunk-bounded writes and append along a declared axis.
- [ ] 3.3 Add clear shape/dtype/schema mismatch failures and safe object-codec defaults.

## 4. Tests and docs

- [ ] 4.1 Add small committed v2/v3 golden fixtures and generated large/chunked temporary fixtures.
- [ ] 4.2 Add read, bulk, reset, table, slice, write/round-trip, malformed, missing-dependency, and bounded-memory tests.
- [ ] 4.3 Add local and representative fsspec/cloud-store tests without live credentials where possible.
- [x] 4.4 Document row mappings, selection, stores, security, limitations, and performance guidance.
- [ ] 4.5 Run representative scientific-extra CI and strict OpenSpec validation.
