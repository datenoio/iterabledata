## ADDED Requirements

### Requirement: GeoParquet Profile Support

The system SHALL support GeoParquet as a metadata-aware profile of Parquet, detect valid GeoParquet metadata without scanning all rows, and expose geometry plus properties using documented feature or raw-WKB row modes.

#### Scenario: Automatic GeoParquet metadata detection

- **WHEN** a `.parquet` file contains valid GeoParquet metadata
- **THEN** `open_iterable()` SHALL recognize the GeoParquet profile
- **AND** detection SHALL require only file metadata/footer access

#### Scenario: Read feature rows

- **WHEN** GeoParquet is opened in default feature mode
- **THEN** each record SHALL contain a geometry and properties consistent with other geospatial iterables
- **AND** CRS, primary geometry column, encoding, geometry types, and bbox metadata SHALL remain accessible

#### Scenario: Read raw WKB batches

- **WHEN** `geometry_mode="wkb"` is requested
- **THEN** geometry bytes SHALL be returned without GeoJSON conversion
- **AND** projection/batch reading SHALL remain available

#### Scenario: Missing or invalid geo metadata

- **WHEN** a Parquet file has no valid GeoParquet metadata and GeoParquet is explicitly requested
- **THEN** the system SHALL raise a clear profile-validation error
- **AND** ordinary Parquet reading SHALL remain available

### Requirement: GeoParquet Metadata-Preserving Writes

The system SHALL write valid GeoParquet files from supported feature or WKB records and preserve declared geospatial metadata across round trips.

#### Scenario: Write feature collection

- **WHEN** feature rows with a declared CRS and geometry column are written
- **THEN** the output SHALL contain valid GeoParquet metadata and encoded geometry
- **AND** reopening it SHALL yield equivalent feature records

#### Scenario: Multiple geometry columns

- **WHEN** multiple geometry columns are configured
- **THEN** the writer SHALL identify the primary geometry and metadata for each column
- **AND** SHALL fail clearly if required metadata is inconsistent

### Requirement: FlatGeobuf Streaming Support

The system SHALL detect, read, and write FlatGeobuf feature collections incrementally and SHALL expose GeoJSON-like feature records consistent with other geospatial formats.

#### Scenario: Detect and stream FlatGeobuf

- **WHEN** a valid `.fgb` file is opened by extension or magic bytes
- **THEN** the FlatGeobuf iterable SHALL yield features without materializing the whole file
- **AND** `read_bulk()` exhaustion SHALL follow the standard partial-batch then empty-list contract

#### Scenario: Bounding-box query with index

- **WHEN** a `bbox` selection is provided and the file contains a spatial index
- **THEN** the backend SHALL use the index to read matching features
- **AND** unrelated features SHALL not be decoded into Python rows

#### Scenario: FlatGeobuf round trip

- **WHEN** supported features are written and reopened
- **THEN** geometry, properties, CRS/metadata supported by the backend, and record order SHALL round-trip according to documentation

#### Scenario: Missing dependency

- **WHEN** FlatGeobuf support is requested without its optional dependency
- **THEN** an `ImportError` SHALL name the correct geospatial extra
