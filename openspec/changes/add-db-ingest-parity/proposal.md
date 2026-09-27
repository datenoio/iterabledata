# Change: Database Ingest Parity and Pooling Rollout

## Why

Read drivers outnumber ingest backends, and connection pooling is only wired
into the postgres driver (plan 2026-09 §6.3). Users can read from ClickHouse
and MSSQL but cannot ingest into them through the uniform API, and non-postgres
drivers reconnect per operation instead of pooling.

## What Changes

- Add ClickHouse and MSSQL ingest backends so every read driver has a matching
  ingest path (uniform `ingest` API surface).
- Extend the existing `iterable/db/pooling.py` pooling to the mysql, mssql,
  mongo, clickhouse, and elasticsearch drivers where the underlying client
  supports it, behind an opt-in option consistent with postgres.
- Conformance tests: ingest→read round-trips per backend using the existing
  testcontainers/docker-gated integration markers (skip when services are
  absent).

## Impact

- Affected specs: `ingest` (extended).
- Affected code: `iterable/db/clickhouse.py`, `mssql.py`, `mysql.py`,
  `mongo.py`, `elasticsearch.py`, `pooling.py`, tests.
- No new core dependencies; driver extras unchanged.

## Non-goals

- Changing default connection behavior (pooling stays opt-in outside postgres).
- Elasticsearch/Mongo query-language rewrites.
