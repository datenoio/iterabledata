# Geospatial Formats Specification

## Purpose
Defines support for KMZ (KML Zipped) and GPX (GPS Exchange Format) in IterableData. KMZ is read from a ZIP archive containing a root KML document; GPX is read as waypoints, route points, and track points with consistent record fields.
## Requirements
### Requirement: KMZ Format Support
The system SHALL support reading KMZ (KML Zipped) files by treating them as ZIP archives that contain a root KML document (e.g. `doc.kml` or the first `.kml` entry), and SHALL expose the same iterable record shape as the existing KML format (e.g. GeoJSON-like features).

#### Scenario: Read KMZ file with automatic detection
- **WHEN** user opens a file with extension `.kmz` via `open_iterable`
- **THEN** the system selects the KMZ iterable and yields feature records equivalent to reading the contained KML

#### Scenario: Read valid KMZ content
- **WHEN** reading a valid KMZ file (ZIP containing at least one `.kml` file)
- **THEN** the system SHALL locate the root KML (e.g. `doc.kml` or first `.kml` in the archive)
- **AND** yielded records SHALL match the KML iterable record shape (e.g. geometry, properties)
- **AND** the system SHALL use stdlib `zipfile` for the container and existing KML parsing (lxml) when the xml extra is installed

#### Scenario: Missing lxml dependency for KMZ
- **WHEN** lxml is not installed and user attempts to read a KMZ file
- **THEN** the system SHALL raise an ImportError with a message instructing to install the xml extra (e.g. `pip install iterabledata[xml]`)

#### Scenario: KMZ with no KML entry
- **WHEN** a KMZ file is opened that does not contain any `.kml` entry
- **THEN** the system SHALL raise a clear error (e.g. ValueError) indicating that no KML document was found in the archive

### Requirement: GPX Format Support
The system SHALL support reading GPX (GPS Exchange Format) 1.0 and 1.1 files using lxml, exposing waypoints, route points, and track points as iterable records with consistent fields (e.g. lat, lon, ele, time, name, description).

#### Scenario: Read GPX file with automatic detection
- **WHEN** user opens a file with extension `.gpx` via `open_iterable`
- **THEN** the system selects the GPX iterable and yields one record per waypoint, route point, or track point (as defined by the implementation)

#### Scenario: Read valid GPX content
- **WHEN** reading a valid GPX file (1.0 or 1.1)
- **THEN** yielded records SHALL include at least latitude and longitude (e.g. `lat`, `lon` or equivalent)
- **AND** records MAY include elevation (`ele`), time (`time`), name, description, and type as defined by the implementation
- **AND** the system SHALL use lxml for parsing when the xml extra is installed

#### Scenario: Missing lxml dependency for GPX
- **WHEN** lxml is not installed and user attempts to read a GPX file
- **THEN** the system SHALL raise an ImportError with install instructions for the xml extra

#### Scenario: GPX with waypoints, routes, and tracks
- **WHEN** reading a GPX file that contains `<wpt>`, `<rtept>`, and/or `<trkpt>` elements
- **THEN** the system SHALL yield records for each such point with a consistent schema (e.g. type or source field distinguishing waypoint, route point, track point)

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

### Requirement: GeoJSON Text Sequence Support

The system SHALL provide a `geojsonseq` format that reads and writes GeoJSON Text Sequences (RFC 8142), where each line is a single GeoJSON Feature object, optionally prefixed by the record-separator control character `\x1e`. Reading and writing SHALL stream one feature at a time.

#### Scenario: Read features line by line

- **WHEN** a `.geojsonl` file with one Feature per line is opened via `open_iterable()`
- **THEN** iteration SHALL yield one record per feature
- **AND** peak memory SHALL be bounded by a single feature, not the file size

#### Scenario: Tolerate RFC 8142 record separator

- **WHEN** a GeoJSON sequence uses the `\x1e` record separator before each JSON text
- **THEN** the reader SHALL strip the separator and parse each feature correctly

#### Scenario: Write one feature per line

- **WHEN** records are written to a `geojsonseq` target
- **THEN** each record SHALL be serialized as a single-line GeoJSON Feature object
- **AND** the output SHALL be re-readable by the same format

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

