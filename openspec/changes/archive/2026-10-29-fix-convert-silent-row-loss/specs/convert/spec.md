## ADDED Requirements

### Requirement: Flat Output Rows Match the Header

When the destination format is flat-only, `convert()` SHALL write each record flattened with the same key scheme used to build the header, whether or not `is_flatten` is set.

#### Scenario: Nested JSON Lines to CSV

- **WHEN** a user converts JSON Lines records shaped `{"id": 1, "meta": {"a": 1}}` to CSV without `is_flatten`
- **THEN** the CSV header SHALL contain `id` and `meta.a`
- **AND** every input record SHALL be written as one CSV row

#### Scenario: Field first seen after the schema scan

- **WHEN** a field appears only after `scan_limit` records and `extra_fields` is not set
- **THEN** `convert()` SHALL raise `WriteError` naming the field
- **AND** with `extra_fields="ignore"` the field SHALL be omitted and the row written

### Requirement: No Silent Write Failures

`convert()` and `bulk_convert()` SHALL raise when a batch cannot be written, unless the caller passes `on_write_error="skip"`. In skip mode the result SHALL report the number of skipped rows.

#### Scenario: Writer rejects a batch

- **WHEN** the destination writer raises while writing a batch and `on_write_error` is not set
- **THEN** `convert()` SHALL raise `WriteError`
- **AND** the error SHALL identify the failing batch's row range

#### Scenario: Skip mode accounting

- **WHEN** a batch fails and `on_write_error="skip"`
- **THEN** the conversion SHALL continue
- **AND** `rows_out + rows_skipped` SHALL equal `rows_in`
