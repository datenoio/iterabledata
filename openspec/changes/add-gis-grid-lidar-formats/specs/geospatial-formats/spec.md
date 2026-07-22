## ADDED Requirements

### Requirement: Esri ASCII Grid Support

The system SHALL support reading Esri ASCII Grid datasets (including `.asc` files with recognizable grid headers) and SHALL yield documented cell or row records without requiring the full grid in memory before iteration starts.

#### Scenario: Detect and read ASCII Grid

- **WHEN** a user opens a valid Esri ASCII Grid / `.asc` file via `open_iterable`
- **THEN** the system SHALL select the ASCII Grid iterable
- **AND** SHALL yield records according to the documented cell or row mapping

#### Scenario: Nodata handling

- **WHEN** the grid declares a nodata value
- **THEN** the reader SHALL either omit nodata cells or flag them consistently as documented
- **AND** SHALL NOT silently treat nodata as ordinary measurements

### Requirement: ArcInfo E00 Support

The system SHALL provide experimental read support for ArcInfo Interchange (`.e00`) exports and SHALL fail clearly for unsupported coverage constructs.

#### Scenario: Read supported E00 export

- **WHEN** a supported `.e00` file is opened
- **THEN** the system SHALL yield iterable feature or coverage records as documented
- **AND** detection SHALL recognize the `.e00` extension

#### Scenario: Unsupported E00 construct

- **WHEN** the file contains constructs outside the supported subset
- **THEN** the system SHALL raise a clear error identifying the limitation

### Requirement: LAS Point Cloud Support

The system SHALL support reading LAS LiDAR files as one record per point with at least coordinates and commonly present point attributes.

#### Scenario: Read LAS points

- **WHEN** a valid `.las` file is opened via `open_iterable`
- **THEN** each yielded record SHALL include `x`, `y`, and `z` (or equivalent)
- **AND** iteration SHALL NOT require loading all points before the first yield

#### Scenario: Missing LiDAR dependency

- **WHEN** LAS support is requested without its optional dependency
- **THEN** the system SHALL raise an `ImportError` with installation instructions for the correct extra

### Requirement: BAG Bathymetry Support

The system SHALL support reading BAG bathymetric products and SHALL expose iterable elevation/sample records, using table listing when multiple datasets are present.

#### Scenario: Read BAG samples

- **WHEN** a valid BAG file is opened
- **THEN** the system SHALL yield documented sample or cell records
- **AND** `list_tables()` SHALL be available when multiple arrays/datasets exist

### Requirement: CZML Packet Support

The system SHALL support reading Cesium CZML documents as an iterable of packet objects.

#### Scenario: Read CZML packets

- **WHEN** a valid `.czml` file is opened via `open_iterable`
- **THEN** the system SHALL yield one record per CZML packet object
- **AND** records SHALL preserve packet fields needed for downstream conversion
