# examples Specification

## Purpose

Provide runnable example scripts and READMEs for high-level features (ops, database reading, ingest, pipeline, validate, convert) under `examples/`, so users can discover and run usage patterns without reading API docs alone.
## Requirements
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

### Requirement: Prompt-shaped cookbook examples
The project SHALL provide a cookbook of short runnable examples under `examples/cookbook/` that
match common LLM generation prompts (read a file, convert formats, inspect a dataset). Cookbook
scripts SHALL use canonical public imports and context managers.

#### Scenario: Cookbook directory present
- **WHEN** a user looks under `examples/cookbook/`
- **THEN** they find at least one script each for reading, converting, and inspecting
- **AND** a README that lists the prompt each script answers

#### Scenario: Cookbook uses public imports
- **WHEN** CI inspects Python files under `examples/cookbook/`
- **THEN** those files import `open_iterable` from `iterable` or `convert` from `iterable.convert`
- **AND** they do not import `open_iterable` from `iterable.helpers.detect`

#### Scenario: Cookbook scripts run against fixtures
- **WHEN** the cookbook smoke test runs
- **THEN** the read and inspect examples complete successfully against a committed CSV fixture

### Requirement: Gzip, JSONL write, and sample cookbook scripts
The cookbook SHALL include short runnable scripts for reading a gzip CSV,
writing JSONL, and sampling rows via `iterable.tools.read_sample`, using only
canonical public imports.

#### Scenario: Gzip read cookbook runs on a committed fixture
- **WHEN** the gzip-read cookbook script is invoked on a committed `.csv.gz` fixture
- **THEN** it yields at least one dict row without loading pandas

#### Scenario: JSONL write cookbook produces a file
- **WHEN** the JSONL-write cookbook script is invoked with a destination path
- **THEN** the destination exists and contains at least one JSON object per line

#### Scenario: Sample cookbook uses tools.read_sample
- **WHEN** the sample cookbook script is invoked on a committed CSV fixture
- **THEN** it returns a successful tool envelope with a list of row dicts

