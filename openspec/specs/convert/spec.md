# convert Specification

## Purpose
TBD - created by archiving change add-bulk-convert. Update Purpose after archive.
## Requirements
### Requirement: Bulk File Conversion
The system SHALL provide a `bulk_convert()` function that converts multiple files using glob patterns, directory paths, or file lists, reusing the existing `convert()` function internally.

#### Scenario: Convert files matching glob pattern
- **WHEN** user calls `bulk_convert('data/raw/*.csv.gz', 'data/processed/', to_ext='parquet')`
- **THEN** system expands glob pattern to find all matching files
- **AND** converts each file to Parquet format
- **AND** writes output files to `data/processed/` directory
- **AND** generates output filenames by replacing extension (e.g., `file.csv.gz` → `file.parquet`)
- **AND** returns aggregated results with per-file conversion status

#### Scenario: Convert files with custom filename pattern
- **WHEN** user calls `bulk_convert('data/*.csv', 'output/', pattern='{name}.parquet')`
- **THEN** system converts each CSV file to Parquet
- **AND** uses pattern to generate output filenames (e.g., `data.csv` → `data.parquet`)
- **AND** supports `{name}`, `{stem}`, `{ext}` placeholders in pattern
- **AND** writes all output files to specified directory

#### Scenario: Convert entire directory
- **WHEN** user calls `bulk_convert('data/raw/', 'data/processed/', to_ext='parquet')`
- **THEN** system discovers all files in source directory
- **AND** converts each file to target format
- **AND** optionally preserves directory structure in output
- **AND** creates output directory if it doesn't exist

#### Scenario: Convert with all convert() parameters
- **WHEN** user calls `bulk_convert()` with `batch_size`, `iterableargs`, `is_flatten`, etc.
- **THEN** system passes all parameters to underlying `convert()` calls
- **AND** each file conversion uses specified parameters
- **AND** parameters apply consistently across all files

#### Scenario: Error handling during bulk conversion
- **WHEN** one file fails during bulk conversion
- **THEN** system continues processing remaining files
- **AND** collects error information for failed file
- **AND** includes error details in aggregated results
- **AND** returns results for both successful and failed conversions

#### Scenario: Aggregated results from bulk conversion
- **WHEN** bulk conversion completes
- **THEN** system returns `BulkConversionResult` object
- **AND** result includes total number of files processed
- **AND** result includes total rows converted across all files
- **AND** result includes total elapsed time
- **AND** result includes per-file conversion results
- **AND** result includes list of any errors encountered

#### Scenario: Progress tracking for bulk conversion
- **WHEN** user provides progress callback to `bulk_convert()`
- **THEN** system invokes callback with progress updates
- **AND** callback receives information about current file being processed
- **AND** callback receives overall progress across all files
- **AND** callback receives aggregated statistics

#### Scenario: Output directory creation
- **WHEN** user specifies output directory that doesn't exist
- **THEN** system creates output directory and any necessary parent directories
- **AND** raises appropriate error if directory creation fails
- **AND** proceeds with conversion after directory creation

#### Scenario: Filename pattern with compression
- **WHEN** user converts compressed files with pattern like `{name}.parquet.zst`
- **THEN** system correctly handles compression extension in pattern
- **AND** generates output filenames with compression extension
- **AND** writes compressed output files

#### Scenario: Empty glob pattern or directory
- **WHEN** user provides glob pattern or directory with no matching files
- **THEN** system returns empty results without error
- **AND** result indicates zero files processed
- **AND** no output files are created

### Requirement: Native Batch Conversion Path

`convert()` SHALL select a compatible native-batch path when both endpoints support it and requested operations do not require per-row materialization. It SHALL otherwise use the existing row path without changing results.

#### Scenario: Columnar-to-columnar conversion

- **WHEN** a compatible Parquet, Arrow, ORC, or lakehouse source is converted to a compatible batch destination without row-only transforms
- **THEN** `convert()` SHALL transfer native batches
- **AND** SHALL avoid an intermediate `list[dict]` representation

#### Scenario: Flattening is requested

- **WHEN** `is_flatten=True` requires per-row transformation
- **THEN** `convert()` SHALL use the row path unless a batch transform explicitly implements identical semantics
- **AND** output SHALL match existing flattening behavior

#### Scenario: Progress and metrics

- **WHEN** conversion uses native batches
- **THEN** `rows_read`, `rows_written`, elapsed time, errors, and progress callbacks SHALL reflect logical rows consistently with the row path

### Requirement: Conversion Selection Pushdown

`convert()` SHALL pass declared projection, predicate, table/variable, range, and slice requests to capable source adapters before materialization.

#### Scenario: Supported projection and filter

- **WHEN** the source declares both projection and filter pushdown
- **THEN** `convert()` SHALL request them from the backend
- **AND** only matching selected data SHALL reach the conversion layer

#### Scenario: Selection fallback

- **WHEN** a requested operation is not supported natively
- **THEN** `convert()` SHALL either apply the documented row fallback or raise in strict mode
- **AND** it SHALL report the selected path in debug diagnostics

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

