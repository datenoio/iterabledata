## ADDED Requirements

### Requirement: XYZ Format Support

The system SHALL support reading XYZ point/molecular coordinate tables and SHALL yield one record per coordinate row with element and position fields.

#### Scenario: Read XYZ file

- **WHEN** a user opens a `.xyz` file via `open_iterable`
- **THEN** the system SHALL yield records containing element and `x`/`y`/`z` fields (or documented equivalents)
- **AND** optional header comment/atom-count lines SHALL be handled without being yielded as data rows

#### Scenario: Write XYZ file

- **WHEN** supported XYZ records are written
- **THEN** the output SHALL be reopenable as XYZ with equivalent coordinates

### Requirement: CIF Format Support

The system SHALL support reading CIF files for a documented subset of crystallographic/chemical constructs and SHALL yield loop or item records according to the selected mode.

#### Scenario: Read atom_site loop

- **WHEN** a CIF file containing an `atom_site` loop is opened in the default atom mode
- **THEN** the system SHALL yield one record per atom_site row
- **AND** unsupported dialects SHALL fail with a clear error

#### Scenario: Missing CIF dependency

- **WHEN** CIF support requires an optional dependency that is not installed
- **THEN** the system SHALL raise an `ImportError` with installation instructions

### Requirement: PDB Format Support

The system SHALL support reading Protein Data Bank (`.pdb`) files as iterable ATOM/HETATM records with optional model selection.

#### Scenario: Read PDB atoms

- **WHEN** a valid `.pdb` file is opened via `open_iterable`
- **THEN** the system SHALL yield atom records including id, name, residue, and coordinates as documented

#### Scenario: Multi-model PDB

- **WHEN** a multi-model PDB is opened with a model selector
- **THEN** only records from the selected model SHALL be yielded

### Requirement: MATLAB MAT Format Support

The system SHALL support reading MATLAB `.mat` files, list variables through `list_tables()`, and iterate a selected variable using a documented array-to-row mapping.

#### Scenario: List MAT variables

- **WHEN** a `.mat` file containing multiple variables is inspected
- **THEN** `list_tables()` SHALL return the variable names

#### Scenario: Read selected MAT variable

- **WHEN** a user opens a `.mat` file with an explicit variable/table selection
- **THEN** the system SHALL yield rows according to the documented leading-axis mapping
- **AND** opening an ambiguous multi-variable file without selection SHALL raise a clear error

#### Scenario: Missing MAT dependency

- **WHEN** MAT support is requested without its optional dependency
- **THEN** the system SHALL raise an `ImportError` with installation instructions for the correct extra
