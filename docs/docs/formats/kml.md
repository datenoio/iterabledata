# KML Format

## Description

KML (Keyhole Markup Language) is an XML-based format for representing geographic data. It's widely used by Google Earth and other mapping applications. KML files contain placemarks with geometries (points, lines, polygons) and associated properties.

## File Extensions

- `.kml` - KML files

## Implementation Details

### Reading

The KML implementation:
- Parses KML Placemark elements
- Extracts geometry (Point, LineString, Polygon)
- Extracts properties (name, description, ExtendedData)
- Converts to GeoJSON-like feature format
- Uses `lxml` library for XML parsing

### Writing

Writing support:
- Writes KML Placemark elements
- Converts GeoJSON-like features to KML
- Supports Point, LineString, and Polygon geometries
- Writes properties as ExtendedData
- Creates proper KML document structure with namespaces

### Key Features

- **Geographic data**: Designed for geographic/spatial data visualization
- **Placemark support**: Handles KML Placemark elements
- **Multiple geometries**: Supports Point, LineString, Polygon
- **Properties**: Extracts name, description, and ExtendedData
- **Namespace handling**: Proper KML 2.2 namespace support

## Usage

```python
from iterable import open_iterable

# Basic reading
with open_iterable('data.kml') as source:
    for feature in source:
        print(feature)  # Each feature is a dict with geometry and properties
        # feature['type'] == 'Feature'
        # feature['geometry'] contains geometry data
        # feature['properties'] contains attributes

# Writing
with open_iterable('output.kml', mode='w') as dest:
    feature = {
        'type': 'Feature',
        'geometry': {'type': 'Point', 'coordinates': [102.0, 0.5]},
        'properties': {
            'name': 'Location',
            'description': 'A point location'
        }
    }
    dest.write(feature)
```

## Parameters

- `prefix_strip` (bool): Strip XML namespace prefixes (default: `True`)
- `encoding` (str): File encoding (default: `utf8`)

## Limitations

1. **lxml dependency**: Requires `lxml` package for XML parsing
2. **Memory usage**: All features are loaded into memory during reading
3. **Geometry types**: Currently supports Point, LineString, Polygon (not MultiGeometry)
4. **ExtendedData**: Properties are stored in ExtendedData elements

## Compression Support

KML files can be compressed with all supported codecs:
- GZip (`.kml.gz`)
- BZip2 (`.kml.bz2`)
- LZMA (`.kml.xz`)
- LZ4 (`.kml.lz4`)
- ZIP (`.kml.zip`)
- Brotli (`.kml.br`)
- ZStandard (`.kml.zst`)

## Use Cases

- **Google Earth**: Creating data for Google Earth visualization
- **Mapping applications**: Geographic data for mapping tools
- **Location data**: Storing and processing location-based data
- **GIS workflows**: Converting between GIS formats

## Related Formats

- [GML](gml.md) - Geography Markup Language
- [GeoJSON](geojson.md) - JSON-based geographic format
- [Shapefile](shapefile.md) - ESRI Shapefile format
- [XML](xml.md) - Base XML format
