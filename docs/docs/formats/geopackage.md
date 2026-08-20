# GeoPackage Format

## Description

GeoPackage is an open, standards-based, platform-independent, portable, self-describing, compact format for transferring geospatial information. It's built on SQLite and can contain multiple layers (tables) of geographic data. GeoPackage is an OGC standard and is increasingly used as an alternative to shapefiles.

## File Extensions

- `.gpkg` - GeoPackage files
- `.geopackage` - GeoPackage files (alias)

## Implementation Details

### Reading

The GeoPackage implementation:
- Reads GeoPackage files using `fiona` library
- Supports multiple layers (tables) in a single file
- Extracts geometry and attributes
- Converts to GeoJSON-like feature format
- Uses GDAL/OGR drivers through fiona

### Writing

Writing support:
- Writes GeoPackage files with geometry and attributes
- Automatically determines schema from first record
- Supports multiple geometry types
- Creates proper GeoPackage structure
- Uses WGS84 (EPSG:4326) coordinate system by default

### Key Features

- **OGC standard**: Official OGC standard
- **SQLite-based**: Built on SQLite database
- **Multiple layers**: Can contain multiple feature layers
- **Self-contained**: Single file contains all data and metadata
- **Efficient**: More efficient than shapefiles for large datasets

## Usage

```python
from iterable import open_iterable

# Basic reading
with open_iterable('data.gpkg') as source:
    for feature in source:
        print(feature)  # Each feature is a dict with geometry and properties
        # feature['type'] == 'Feature'
        # feature['geometry'] contains geometry data
        # feature['properties'] contains attributes

# List available layers
from iterable.datatypes.geopackage import GeoPackageIterable

# Discover layers before opening
layers = GeoPackageIterable('data.gpkg').list_tables('data.gpkg')
print(f"Available layers: {layers}")  # e.g., ['roads', 'buildings', 'parcels']

# Reading specific layer
with open_iterable('data.gpkg', iterableargs={'layer': 'layer_name'}) as source:
    for feature in source:
        print(feature)

# Process all layers
for layer_name in layers:
    with open_iterable('data.gpkg', iterableargs={'layer': layer_name}) as source:
        print(f"Processing layer: {layer_name}")
        for feature in source:
            process(feature)

# Writing
with open_iterable('output.gpkg', mode='w') as dest:
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

- `layer` (str): Layer name to read/write (optional, uses first layer if not specified)
- `encoding` (str): File encoding (default: `utf8`)

## Limitations

1. **fiona dependency**: Requires `fiona` package (which requires GDAL)
2. **File path required**: Requires filename, not stream
3. **GDAL dependency**: fiona requires GDAL/OGR libraries
4. **Memory usage**: All features are loaded into memory during reading
5. **CRS**: Defaults to WGS84; CRS transformations not handled

## Compression Support

GeoPackage files are already compressed (SQLite format), so additional compression is typically not needed. However, they can be compressed with all supported codecs if needed:
- GZip (`.gpkg.gz`)
- BZip2 (`.gpkg.bz2`)
- LZMA (`.gpkg.xz`)
- LZ4 (`.gpkg.lz4`)
- ZIP (`.gpkg.zip`)
- Brotli (`.gpkg.br`)
- ZStandard (`.gpkg.zst`)

## Use Cases

- **Modern GIS**: Preferred format in modern GIS applications
- **Mobile applications**: Used in mobile mapping applications
- **Data exchange**: Standard format for exchanging geographic data
- **Multi-layer data**: When you need multiple layers in one file
- **Large datasets**: More efficient than shapefiles for large datasets


## Error Handling

- **Missing dependency**: optional libraries raise `ImportError` with an install hint (`pip install 'iterabledata[<extra>]'` when an extra exists).
- **Write mode**: read-only formats raise `WriteNotSupportedError` or `ValueError` when opened with `mode="w"`.
- **Bad or unsupported input**: may raise `ValueError`, `OSError`, or library-specific errors.
- See [Troubleshooting](/getting-started/troubleshooting) for decoding, detection, and engine issues.

## Related Formats

- [Shapefile](shapefile.md) - ESRI Shapefile format
- [GeoJSON](geojson.md) - JSON-based geographic format
- [KML](kml.md) - Keyhole Markup Language
- [GML](gml.md) - Geography Markup Language
- [SQLite](sqlite.md) - Base SQLite format
