## ADDED Requirements

### Requirement: ESRI File Geodatabase Support

The system SHALL support reading ESRI File Geodatabase sources (`.gdb` directories and `.fgdb` path labels), expose layers through table listing, and yield GeoJSON-like feature records consistent with other geospatial iterables.

#### Scenario: Detect File Geodatabase path

- **WHEN** a user opens a `.gdb` directory or `.fgdb` path via `open_iterable`
- **THEN** the system SHALL select the File Geodatabase iterable
- **AND** SHALL use the registered geospatial optional dependency when required

#### Scenario: List and select layers

- **WHEN** a File Geodatabase contains multiple layers
- **THEN** `list_tables()` SHALL return the layer names
- **AND** opening without an explicit layer/table selection SHALL raise a clear error naming how to select a layer

#### Scenario: Stream feature rows

- **WHEN** a File Geodatabase layer is opened for reading
- **THEN** the iterable SHALL yield feature records with geometry and properties
- **AND** SHALL NOT require loading the entire layer into memory before the first row

#### Scenario: Missing File Geodatabase dependency

- **WHEN** the optional geospatial dependency is not installed
- **THEN** the system SHALL raise an `ImportError` with installation instructions for the correct extra

### Requirement: MapInfo MIF Support

The system SHALL support reading MapInfo Interchange Format (`.mif`) files, optionally paired with `.mid` attribute tables, and SHALL yield GeoJSON-like feature records.

#### Scenario: Detect and read MIF with MID

- **WHEN** a user opens a `.mif` file that has a co-located `.mid` attribute file
- **THEN** the system SHALL yield one feature per geometry
- **AND** feature properties SHALL include MID attribute columns when present

#### Scenario: MIF without MID

- **WHEN** a `.mif` file is opened and no usable `.mid` file is present
- **THEN** the system SHALL still yield geometry features
- **AND** SHALL document or surface that attributes are unavailable

#### Scenario: Missing MapInfo dependency

- **WHEN** MapInfo support is requested without its optional dependency
- **THEN** the system SHALL raise an `ImportError` with installation instructions for the correct extra
