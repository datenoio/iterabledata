## ADDED Requirements

### Requirement: Runnable examples for high-level features

The project SHALL provide runnable example scripts for high-level features (ops, database reading, ingest, pipeline, validate, convert), organized under the `examples/` directory in subdirs aligned to each feature area. Each feature subdir SHALL include a README describing the feature and how to run the examples.

#### Scenario: Ops examples available

- **WHEN** a user looks under `examples/ops/`
- **THEN** they find example scripts for filter, inspect, stats, schema, and transform, plus a README explaining how to run them

#### Scenario: Ingest examples available

- **WHEN** a user looks under `examples/ingest/`
- **THEN** they find example scripts demonstrating `to_db` for at least PostgreSQL and SQLite, plus a README

#### Scenario: Database reading examples available

- **WHEN** a user looks under `examples/db/`
- **THEN** they find example scripts demonstrating reading from PostgreSQL, SQLite, and MySQL via `open_iterable(..., engine=...)`, plus a README

#### Scenario: Pipeline and validate examples available

- **WHEN** a user looks under `examples/pipeline/` and `examples/validate/`
- **THEN** they find runnable pipeline and validate examples plus READMEs

#### Scenario: Convert documented

- **WHEN** a user looks under `examples/convert/` (or `examples/converter/`)
- **THEN** they find documentation (README) for the convert API and how to run the existing converter example
