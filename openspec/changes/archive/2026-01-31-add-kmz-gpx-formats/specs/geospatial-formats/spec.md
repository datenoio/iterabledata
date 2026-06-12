## ADDED Requirements

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
