## ADDED Requirements

### Requirement: Native CSV Batch Reader

When PyArrow is installed, CSV SHALL provide a native batch reader that yields Arrow record batches with every column typed as string, using the same dialect options as the row reader.

#### Scenario: CSV to Parquet without row materialization

- **WHEN** a user converts a CSV file to Parquet with `use_native_batch=True`
- **THEN** the conversion SHALL stream Arrow batches from the CSV reader to the Parquet writer
- **AND** the written values SHALL equal the row path's values, with empty fields as `""`
