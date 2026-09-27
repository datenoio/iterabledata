# Spec Delta: ingest

## ADDED Requirements

### Requirement: Backend parity for read drivers

Every database read driver SHALL have a matching ingest backend with the same
uniform API surface.

#### Scenario: ClickHouse and MSSQL ingest

- **WHEN** a user ingests records into ClickHouse or MSSQL through the uniform
  ingest API (with the service available)
- **THEN** the records are readable through the corresponding read driver

### Requirement: Opt-in connection pooling

Connection pooling SHALL be available for mysql, mssql, mongo, clickhouse, and
elasticsearch drivers, off by default, using the shared pooling machinery.

#### Scenario: Pooling reuses connections

- **WHEN** pooling is enabled and multiple operations run on one driver
- **THEN** connections are drawn from the shared pool and returned on teardown
