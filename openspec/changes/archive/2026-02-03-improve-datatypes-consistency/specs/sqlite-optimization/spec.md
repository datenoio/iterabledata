# SQLite Optimization

## ADDED Requirements

### Requirement: Efficient bulk reading
SQLiteIterable.read_bulk MUST use `cursor.fetchmany()` for improved performance.

#### Scenario: Reading large chunks
- **WHEN** a user calls `read_bulk(1000)` on a SQLiteIterable with many records
- **THEN** the implementation SHALL use `cursor.fetchmany(1000)` (or equivalent)
- **AND** SHALL return up to 1000 records
