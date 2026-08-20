# Shapefile Format

## Description

Shapefile is a popular geospatial vector data format developed by ESRI. Despite its name, a shapefile actually consists of multiple files (`.shp`, `.shx`, `.dbf`, etc.) that work together. This implementation uses the `pyshp` library to read and write shapefiles.

## File Extensions

- `.shp` - Shapefile main file
- `.shapefile` - Shapefile (alias)

## Implementation Details

### Reading

The Shapefile implementation:
- Reads `.shp` files using `pyshp` library
- Extracts geometry (Point, LineString, Polygon, MultiPoint)
- Extracts attribute data from associated `.dbf` file
- Converts to GeoJSON-like feature format
- Handles multiple geometry types

### Writing

Writing support:
- Writes shapefiles with geometry and attributes
- Automatically determines shape type from first record
- Creates field definitions based on property types
- Supports Point, LineString, Polygon, MultiPoint geometries
- Creates all necessary shapefile components (.shp, .shx, .dbf)

### Key Features

- **Industry standard**: Widely used in GIS industry
- **Multiple files**: Automatically handles multiple component files
- **Geometry types**: Supports Point, LineString, Polygon, MultiPoint
- **Attributes**: Full attribute data support
- **Type detection**: Automatically detects geometry and attribute types

## Usage

```python
from iterable import open_iterable

# Basic reading
with open_iterable('data.shp') as source:
    for feature in source:
        print(feature)  # Each feature is a dict with geometry and properties
        # feature['type'] == 'Feature'
        # feature['geometry'] contains geometry data
        # feature['properties'] contains attributes

# Writing
with open_iterable('output.shp', mode='w') as dest:
    feature = {
        'type': 'Feature',
        'geometry': {'type': 'Point', 'coordinates': [102.0, 0.5]},
        'properties': {
            'id': '1',
            'name': 'Location'
        }
    }
    dest.write(feature)
```

## Parameters

- `encoding` (str): File encoding (default: `utf8`)

## Limitations

1. **pyshp dependency**: Requires `pyshp` package
2. **File path required**: Requires filename, not stream
3. **Multiple files**: Shapefile consists of multiple files (.shp, .shx, .dbf, etc.)
4. **Geometry types**: Limited to Point, LineString, Polygon, MultiPoint
5. **Field types**: Field types are determined from first record
6. **Memory usage**: All features are loaded into memory during reading

## Compression Support

Shapefiles cannot be directly compressed as they consist of multiple files. However, you can compress the entire directory or use ZIP format for the shapefile components.

## Use Cases

- **GIS workflows**: Standard format in GIS applications
- **ESRI compatibility**: Working with ESRI ArcGIS data
- **Spatial analysis**: Geographic data analysis
- **Data exchange**: Common format for exchanging geographic data
- **Cartography**: Creating maps and visualizations


## Error Handling

- **Missing dependency**: optional libraries raise `ImportError` with an install hint (`pip install 'iterabledata[<extra>]'` when an extra exists).
- **Write mode**: read-only formats raise `WriteNotSupportedError` or `ValueError` when opened with `mode="w"`.
- **Bad or unsupported input**: may raise `ValueError`, `OSError`, or library-specific errors.
- See [Troubleshooting](/getting-started/troubleshooting) for decoding, detection, and engine issues.

## Related Formats

- [GeoJSON](geojson.md) - JSON-based geographic format
- [KML](kml.md) - Keyhole Markup Language
- [GML](gml.md) - Geography Markup Language
- [GeoPackage](geopackage.md) - SQLite-based geospatial format
