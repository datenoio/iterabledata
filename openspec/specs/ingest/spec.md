# ingest Specification

## Purpose
TBD - created by archiving change add-high-level-operations. Update Purpose after archive.
## Requirements
### Requirement: Unified Database Ingestion API
The system SHALL provide a unified function to ingest data from iterables into various database systems.

#### Scenario: Ingest to PostgreSQL
- **WHEN** `ingest.to_db()` is called with `dbtype="postgresql"` and connection details
- **THEN** rows from the iterable are inserted into the specified PostgreSQL table
- **AND** ingestion handles connection management automatically
- **AND** errors are reported clearly

#### Scenario: Ingest to MongoDB
- **WHEN** `ingest.to_db()` is called with `dbtype="mongodb"` and connection details
- **THEN** rows from the iterable are inserted into the specified MongoDB collection
- **AND** ingestion handles connection management automatically
- **AND** document structure matches row structure

#### Scenario: Ingest to DuckDB
- **WHEN** `ingest.to_db()` is called with `dbtype="duckdb"` and connection details
- **THEN** rows from the iterable are inserted into the specified DuckDB table
- **AND** ingestion leverages DuckDB's efficient insertion capabilities
- **AND** table creation is supported

#### Scenario: Ingest to SQLite
- **WHEN** `ingest.to_db()` is called with `dbtype="sqlite"` and file path
- **THEN** rows from the iterable are inserted into the specified SQLite table
- **AND** ingestion handles SQLite-specific constraints
- **AND** transaction management is appropriate

#### Scenario: Ingest to MySQL
- **WHEN** `ingest.to_db()` is called with `dbtype="mysql"` and connection details
- **THEN** rows from the iterable are inserted into the specified MySQL table
- **AND** ingestion handles MySQL-specific features
- **AND** connection pooling is used when appropriate

#### Scenario: Ingest to Elasticsearch
- **WHEN** `ingest.to_db()` is called with `dbtype="elasticsearch"` and connection details
- **THEN** rows from the iterable are indexed into the specified Elasticsearch index
- **AND** ingestion handles Elasticsearch-specific features (mapping, refresh, etc.)
- **AND** document structure is appropriate for Elasticsearch

### Requirement: Batch Processing
The system SHALL support batch processing for efficient database ingestion.

#### Scenario: Ingest with batch size
- **WHEN** `ingest.to_db()` is called with `batch=5000`
- **THEN** rows are inserted in batches of 5000
- **AND** batch processing improves performance for large datasets
- **AND** memory usage is controlled

#### Scenario: Batch processing with errors
- **WHEN** a batch fails during ingestion
- **THEN** the error is reported clearly
- **AND** previous batches are committed (if transaction allows)
- **AND** error details include batch information

### Requirement: Upsert Support
The system SHALL support upsert operations (insert or update) for databases that support it.

#### Scenario: Upsert with key field
- **WHEN** `ingest.to_db()` is called with `mode="upsert"` and `upsert_key="id"`
- **THEN** existing rows with matching key are updated
- **AND** new rows are inserted
- **AND** upsert behavior is database-appropriate

#### Scenario: Upsert with multiple key fields
- **WHEN** `ingest.to_db()` is called with `mode="upsert"` and `upsert_key=["id", "date"]`
- **THEN** upsert matching uses all specified key fields
- **AND** composite key matching works correctly

### Requirement: Automatic Table Creation
The system SHALL support automatic table/collection creation when it doesn't exist.

#### Scenario: Auto-create table
- **WHEN** `ingest.to_db()` is called with `create_table=True` and table doesn't exist
- **THEN** the table is created automatically based on data schema
- **AND** appropriate data types are inferred
- **AND** table creation handles database-specific requirements

#### Scenario: Auto-create with schema
- **WHEN** `ingest.to_db()` is called with `create_table=True` and explicit schema
- **THEN** the table is created using the provided schema
- **AND** schema is applied correctly
- **AND** type mappings are database-appropriate

### Requirement: Retry with Backoff
The system SHALL support retry logic with exponential backoff for transient failures.

#### Scenario: Retry on connection error
- **WHEN** ingestion encounters a transient connection error
- **THEN** the operation is retried with exponential backoff
- **AND** retry attempts are configurable
- **AND** permanent failures are not retried indefinitely

#### Scenario: Retry with max attempts
- **WHEN** `ingest.to_db()` is called with `max_retries=3`
- **THEN** failed operations are retried up to 3 times
- **AND** after max retries, the error is reported
- **AND** retry delays increase exponentially

### Requirement: Progress Reporting
The system SHALL provide progress reporting during ingestion operations.

#### Scenario: Progress callback
- **WHEN** `ingest.to_db()` is called with a progress callback
- **THEN** the callback is invoked periodically with progress information:
  - Rows processed
  - Rows inserted
  - Elapsed time
  - Estimated time remaining
- **AND** progress reporting doesn't significantly impact performance

#### Scenario: Progress with totals
- **WHEN** `ingest.to_db()` is called with `totals=True`
- **THEN** the return value includes total statistics:
  - Total rows processed
  - Total rows inserted/updated
  - Total errors
  - Elapsed time
- **AND** statistics are accurate

### Requirement: Error Handling
The system SHALL handle errors gracefully during ingestion operations.

#### Scenario: Handle database errors
- **WHEN** ingestion encounters a database error (constraint violation, type mismatch, etc.)
- **THEN** the error is caught and reported clearly
- **AND** error messages include context (row number, field, value)
- **AND** ingestion can continue or stop based on configuration

#### Scenario: Handle data type mismatches
- **WHEN** a row contains data that doesn't match the table schema
- **THEN** the error is reported with details
- **AND** type conversion is attempted when safe
- **AND** conversion failures are clearly indicated

### Requirement: Transaction Management
The system SHALL manage transactions appropriately for each database type.

#### Scenario: Transaction for SQL databases
- **WHEN** ingesting to SQL databases (PostgreSQL, MySQL, SQLite)
- **THEN** transactions are used appropriately
- **AND** batch commits are performed for performance
- **AND** rollback occurs on critical errors

#### Scenario: Transaction for NoSQL databases
- **WHEN** ingesting to NoSQL databases (MongoDB, Elasticsearch)
- **THEN** database-appropriate consistency guarantees are used
- **AND** bulk operations are used when available
- **AND** error handling is appropriate for the database type

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

