# GML Format

## Description

GML (Geography Markup Language) is an XML-based standard for encoding geographic information. It's an OGC (Open Geospatial Consortium) standard used for exchanging geographic data. GML supports complex geographic features with multiple geometry types.

## File Extensions

- `.gml` - GML files

## Implementation Details

### Reading

The GML implementation:
- Parses GML FeatureCollection elements
- Extracts featureMember elements
- Supports GML 2.0 and 3.2 namespaces
- Extracts geometry (Point, LineString, Polygon, MultiPoint, MultiLineString, MultiPolygon)
- Extracts feature properties
- Converts to GeoJSON-like feature format
- Uses `lxml` library for XML parsing

### Writing

Writing support:
- Writes GML FeatureCollection structure
- Converts GeoJSON-like features to GML
- Supports Point, LineString, Polygon geometries
- Uses GML 3.2 namespace
- Writes properties as feature attributes

### Key Features

- **OGC standard**: Official OGC standard for geographic data
- **Multiple geometries**: Supports Point, LineString, Polygon, MultiPoint, MultiLineString, MultiPolygon
- **Feature properties**: Extracts and writes feature attributes
- **Namespace support**: Handles GML 2.0 and 3.2 namespaces
- **Complex structures**: Supports nested geographic structures

## Usage

```python
from iterable import open_iterable

# Basic reading
with open_iterable('data.gml') as source:
    for feature in source:
        print(feature)  # Each feature is a dict with geometry and properties
        # feature['type'] == 'Feature'
        # feature['geometry'] contains geometry data
        # feature['properties'] contains attributes

# Writing
with open_iterable('output.gml', mode='w') as dest:
    feature = {
        'type': 'Feature',
        'geometry': {'type': 'Point', 'coordinates': [102.0, 0.5]},
        'properties': {
            'name': 'Location',
            'id': '1'
        }
    }
    dest.write(feature)
```

## Parameters

- `prefix_strip` (bool): Strip XML namespace prefixes (default: `True`)
- `feature_member` (str): Name of feature member element (default: `featureMember`)
- `encoding` (str): File encoding (default: `utf8`)

## Limitations

1. **lxml dependency**: Requires `lxml` package for XML parsing
2. **Memory usage**: All features are loaded into memory during reading
3. **GML complexity**: Full GML standard is very complex; this is a simplified implementation
4. **Coordinate systems**: Does not handle CRS (Coordinate Reference System) transformations

## Compression Support

GML files can be compressed with all supported codecs:
- GZip (`.gml.gz`)
- BZip2 (`.gml.bz2`)
- LZMA (`.gml.xz`)
- LZ4 (`.gml.lz4`)
- ZIP (`.gml.zip`)
- Brotli (`.gml.br`)
- ZStandard (`.gml.zst`)

## Use Cases

- **OGC workflows**: Working with OGC-compliant geographic data
- **GIS systems**: Exchanging data between GIS systems
- **Spatial data**: Processing spatial data in standard format
- **Government data**: Many government agencies use GML


## Error Handling

- **Missing dependency**: optional libraries raise `ImportError` with an install hint (`pip install 'iterabledata[<extra>]'` when an extra exists).
- **Write mode**: read-only formats raise `WriteNotSupportedError` or `ValueError` when opened with `mode="w"`.
- **Bad or unsupported input**: may raise `ValueError`, `OSError`, or library-specific errors.
- See [Troubleshooting](/getting-started/troubleshooting) for decoding, detection, and engine issues.

## Related Formats

- [KML](kml.md) - Keyhole Markup Language
- [GeoJSON](geojson.md) - JSON-based geographic format
- [Shapefile](shapefile.md) - ESRI Shapefile format
- [GeoPackage](geopackage.md) - SQLite-based geospatial format
- [XML](xml.md) - Base XML format
