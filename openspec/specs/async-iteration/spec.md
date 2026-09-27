# async-iteration Specification

## Purpose
TBD - created by archiving change add-genuine-async-iteration. Update Purpose after archive.
## Requirements
### Requirement: Non-blocking async open

`aopen_iterable()` SHALL NOT run blocking detection or iteration on the event
loop; blocking work SHALL be offloaded to a thread pool.

#### Scenario: Event loop stays responsive

- **WHEN** two sources are opened and read concurrently with asyncio
- **THEN** their iterations interleave without one blocking the other

### Requirement: Public export

`aopen_iterable` SHALL be importable from the package root.

#### Scenario: Root import works

- **WHEN** a user runs `from iterable import aopen_iterable`
- **THEN** the import succeeds and matches `iterable.helpers.async_detect.aopen_iterable`

### Requirement: Result parity with sync API

Async iteration SHALL yield the same records as the synchronous API for the
same source.

#### Scenario: CSV/JSONL parity

- **WHEN** the same csv or jsonl file is read via `open_iterable` and
  `aopen_iterable`
- **THEN** both yield identical record lists

