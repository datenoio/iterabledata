## ADDED Requirements

### Requirement: Lightweight Package Import

Importing the top-level `iterable` package SHALL NOT import optional database drivers, columnar or dataframe libraries, HTTP clients or terminal UI libraries. Such backends SHALL be imported on first use.

#### Scenario: Plain package import

- **WHEN** a fresh interpreter runs `import iterable` with all optional extras installed
- **THEN** none of `elasticsearch`, `pymongo`, `pyarrow`, `numpy`, `pandas`, `duckdb`, `httpx` or `rich` SHALL be present in `sys.modules`

#### Scenario: Database driver on demand

- **WHEN** a user opens a `postgres://` source after importing `iterable`
- **THEN** only the PostgreSQL driver module SHALL be imported to serve the request

#### Scenario: Import-time regression

- **WHEN** the performance regression gate runs
- **THEN** the measured `import iterable` time SHALL be compared with its committed baseline like other workloads
