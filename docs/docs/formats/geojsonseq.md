# GeoJSONSeq Format (GeoJSON Text Sequences)

## Description

GeoJSON Text Sequences (RFC 8142) store one GeoJSON Feature object per line. It is the streaming-friendly counterpart to [GeoJSON](geojson.md): instead of a single `FeatureCollection` document, each feature is an independent JSON text, so files of any size can be processed with constant memory. Each line may optionally begin with the ASCII record separator control character (`0x1E`), as required by RFC 8142; both plain-line (`.geojsonl`) and separator-prefixed (`.geojsons`) variants are read transparently.

## File Extensions

- `.geojsonl` - GeoJSON Lines (one feature per line)
- `.geojsons` - GeoJSON Text Sequence (RFC 8142)

## Implementation Details

### Reading

- Reads one line at a time; peak memory is bounded by a single feature
- Strips the optional `0x1E` record separator prefix from each line
- Each feature is returned as a dictionary (full GeoJSON structure preserved)
- Parse errors go through the standard error-handling hooks (raise/skip/warn)

### Writing

- `write()` / `write_bulk()` serialize each record as a single-line JSON object
- Output is one feature per line and re-readable by the same format

### Key Features

- **True streaming**: `is_streaming()` returns `True` for both read and write
- **No dependencies**: implemented with the standard library `json` module
- **Content detection**: files whose lines are JSON objects with `"type": "Feature"` are detected as `geojsonseq` even without a known extension

## Usage

```python
from iterable.helpers.detect import open_iterable

# Read features one at a time
with open_iterable('features.geojsonl') as source:
    for feature in source:
        print(feature['properties'], feature['geometry'])

# Write features
features = [
    {"type": "Feature", "properties": {"id": "1"}, "geometry": {"type": "Point", "coordinates": [0, 0]}},
]
with open_iterable('out.geojsonl', mode='w') as dest:
    dest.write_bulk(features)
```

## Parameters

- `encoding` (str): File encoding (default: `utf8`)

## Compression Support

GeoJSONSeq files can be compressed with all supported codecs:
- GZip (`.geojsonl.gz`)
- BZip2 (`.geojsonl.bz2`)
- LZMA (`.geojsonl.xz`)
- ZStandard (`.geojsonl.zst`)

## Use Cases

- **Tiling pipelines**: streaming feature input for `tippecanoe` and similar tools
- **Geospatial ETL**: converting large feature sets without loading them into memory
- **Data exchange**: line-oriented output of PostGIS, GDAL/OGR (`ogr2ogr -f GeoJSONSeq`)

## Related Formats

- [GeoJSON](geojson.md) - Document-oriented FeatureCollection format
- [JSON Lines](jsonl.md) - Generic line-oriented JSON records
