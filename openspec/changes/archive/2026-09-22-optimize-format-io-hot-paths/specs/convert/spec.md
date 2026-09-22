## ADDED Requirements

### Requirement: Single Non-Destructive Total Estimation

`convert()` SHALL evaluate the source total at most once per conversion when totals are requested, cache that estimate for progress reporting, and SHALL NOT consume or repeatedly rescan the active source cursor.

#### Scenario: Progress callback uses a cached total

- **WHEN** conversion runs with `use_totals=True` and a progress callback fires multiple times
- **THEN** `totals()` SHALL be invoked at most once
- **AND** every callback SHALL receive the same cached `estimated_total`

#### Scenario: Compressed line source total

- **WHEN** conversion requests totals for a gzip- or other codec-wrapped line format
- **THEN** the estimate SHALL count logical decompressed records or be `None`
- **AND** it SHALL NOT count newline bytes in compressed data or raise because text is compared with byte delimiters

#### Scenario: Non-seekable source

- **WHEN** a source cannot provide a non-destructive total
- **THEN** conversion SHALL continue with `estimated_total=None`
- **AND** progress estimation SHALL NOT consume records or require a reset
