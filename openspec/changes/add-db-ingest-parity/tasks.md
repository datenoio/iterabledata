# Tasks

## 1. Missing ingest backends

- [x] 1.1 Implement ClickHouse ingest (batch INSERT, schema inference consistent with existing backends).
- [x] 1.2 Implement MSSQL ingest with the same surface.
- [x] 1.3 Integration tests (docker-gated, skip without services) covering ingest→read round-trips.

## 2. Pooling rollout

- [x] 2.1 Extend pooling.py support to mysql, mssql, mongo, clickhouse, elasticsearch behind an opt-in option.
- [x] 2.2 Tests proving connection reuse and correct teardown per driver (mocked clients acceptable).

## 3. Verification

- [x] 3.1 `ingest` spec conformance and full serial suite green (skips expected without docker).
- [x] 3.2 Docs (database engines page) and CHANGELOG updated.
