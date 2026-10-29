## ADDED Requirements

### Requirement: Public Helpers for Downstream Tools

Functionality that downstream tools need SHALL be available under public, documented names. Private names that were previously used downstream SHALL remain as aliases for at least one minor release.

#### Scenario: Listing codecs

- **WHEN** a caller needs the registered codec ids and extensions
- **THEN** `iterable.helpers.detect.list_codecs()` SHALL return them
- **AND** the caller SHALL NOT need `_get_codec_registry()`

#### Scenario: Downstream contract test

- **WHEN** a public helper used by undatum is renamed or removed
- **THEN** `tests/test_downstream_contract.py` SHALL fail in this repository
