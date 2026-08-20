# GeoJSON Format

## Description

GeoJSON is a format for encoding geographic data structures using JSON. It's widely used for representing geographic features, their properties, and geometries. GeoJSON supports points, lines, polygons, and collections of features.

## File Extensions

- `.geojson` - GeoJSON files

## Implementation Details

### Reading

The GeoJSON implementation:
- Supports FeatureCollection (array of features)
- Supports single Feature objects
- Supports JSONL format (one GeoJSON object per line)
- Converts features to dictionaries
- Uses `geojson` library for validation (optional)

### Writing

Writing support:
- Writes GeoJSON features
- Can write FeatureCollection or individual features
- Uses `geojson` library for validation (optional)

### Key Features

- **Geographic data**: Designed for geographic/spatial data
- **Feature support**: Handles GeoJSON Feature and FeatureCollection
- **JSONL support**: Can read GeoJSON in JSONL format
- **Nested data**: Supports complex geographic structures
- **Validation**: Optional validation with geojson library

## Usage

```python
from iterable import open_iterable

# Basic reading
with open_iterable('data.geojson') as source:
    for feature in source:
        print(feature)  # Each feature is a dict with geometry and properties

# Writing
with open_iterable('output.geojson', mode='w') as dest:
    feature = {
        'type': 'Feature',
        'geometry': {'type': 'Point', 'coordinates': [102.0, 0.5]},
        'properties': {'name': 'Location'}
    }
    dest.write(feature)
```

## Parameters

- `encoding` (str): File encoding (default: `utf8`)

## Limitations

1. **geojson dependency**: Optional but recommended for validation
2. **Memory usage**: FeatureCollection format loads all features into memory
3. **Structure complexity**: Complex geometries may be difficult to work with
4. **Validation**: Without geojson library, no format validation

## Compression Support

GeoJSON files can be compressed with all supported codecs:
- GZip (`.geojson.gz`)
- BZip2 (`.geojson.bz2`)
- LZMA (`.geojson.xz`)
- LZ4 (`.geojson.lz4`)
- ZIP (`.geojson.zip`)
- Brotli (`.geojson.br`)
- ZStandard (`.geojson.zst`)

## Use Cases

- **GIS data**: Geographic information systems
- **Mapping**: Web mapping applications
- **Spatial analysis**: Geographic data analysis
- **Location data**: Storing and processing location data


## Error Handling

- **Missing dependency**: optional libraries raise `ImportError` with an install hint (`pip install 'iterabledata[<extra>]'` when an extra exists).
- **Write mode**: read-only formats raise `WriteNotSupportedError` or `ValueError` when opened with `mode="w"`.
- **Bad or unsupported input**: may raise `ValueError`, `OSError`, or library-specific errors.
- See [Troubleshooting](/getting-started/troubleshooting) for decoding, detection, and engine issues.

## Related Formats

- [JSON](json.md) - Base JSON format
- [JSONL](jsonl.md) - Line-delimited JSON
