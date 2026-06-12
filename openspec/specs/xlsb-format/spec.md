# xlsb-format Specification

## Purpose
TBD - created by archiving change add-rdf-xlsb-fasta-graph-bio-formats. Update Purpose after archive.
## Requirements
### Requirement: XLSB Format Reading
The system SHALL support reading Excel Binary (.xlsb) workbooks using pyxlsb, yielding row records as dictionaries keyed by column name or index.

#### Scenario: Read XLSB file with automatic detection
- **WHEN** user opens a file with extension `.xlsb` via `open_iterable`
- **THEN** the system selects the XLSB iterable and yields sheet rows as dicts

#### Scenario: Read sheet rows from XLSB
- **WHEN** reading a valid XLSB file
- **THEN** each yielded record SHALL represent one row with keys corresponding to column names or indices
- **AND** multiple sheets MAY be exposed (e.g. via table/sheet selection or sequential iteration) as defined by the implementation

#### Scenario: Missing pyxlsb dependency
- **WHEN** pyxlsb is not installed and user attempts to read an XLSB file
- **THEN** the system SHALL raise an ImportError with a message instructing to install the xlsb extra (e.g. `pip install iterabledata[xlsb]`)

#### Scenario: Empty or single-row XLSB
- **WHEN** opening an XLSB file with an empty sheet or only a header row
- **THEN** the system SHALL yield zero or one record as appropriate and SHALL NOT raise for empty sheets

