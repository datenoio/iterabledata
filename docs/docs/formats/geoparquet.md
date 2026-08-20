# GeoParquet Format

GeoParquet is a [Parquet](parquet.md) profile that stores geospatial features with `geo` file metadata (primary geometry column, CRS, WKB encoding). IterableData reads and writes that metadata while exposing geometry as **raw WKB** unless your application decodes it.

## File Extensions

- `.parquet` — GeoParquet is a Parquet file; use `format="geoparquet"` or GeoParquet content/metadata detection
- `.geoparquet` — used when present

## Implementation Details

### Reading

- Same streaming Parquet reader as [Parquet](parquet.md)
- Loads `geo` schema metadata from the Arrow/Parquet key-value metadata
- Geometry columns remain WKB bytes (or whatever the file stored)

### Writing

- Writes Parquet row groups with GeoParquet `geo` metadata
- Default primary column name is `geometry`
- Optional `crs` is stored on the primary geometry column metadata

### Key Features

- **Metadata preservation**: version, primary column, per-column encoding/CRS
- **WKB by default**: no implicit geometry library decode
- **Parquet performance**: columnar batches, compression, projection

## Usage

```python
from iterable import open_iterable

with open_iterable("places.parquet", iterableargs={"format": "geoparquet"}) as source:
    for row in source:
        print(row.get("name"), row.get("geometry"))  # geometry is WKB

with open_iterable(
    "out.parquet",
    mode="w",
    iterableargs={"format": "geoparquet", "geometry_column": "geometry", "crs": "EPSG:4326"},
) as dest:
    dest.write({
        "name": "Origin",
        "geometry": b"\x01\x01" + b"\x00" * 16,  # application-provided WKB
    })
```

## Parameters

| Parameter | Type | Default | Required | Description |
|-----------|------|---------|----------|-------------|
| `geometry_column` | str | `"geometry"` | No | Primary geometry column name written into `geo` metadata |
| `crs` | any JSON-serializable | none | No | CRS recorded on the primary geometry column |
| *(Parquet args)* | | | | Compression, batch size, and other [Parquet](parquet.md) write options still apply |

## Installation

```bash
pip install 'iterabledata[parquet]'
```

Requires `pyarrow`. Decode WKB with a geospatial library if you need Shapely/GeoJSON geometries.

## Limitations

1. **Geometry is raw WKB** unless you decode it
2. **Requires pyarrow**
3. **Experimental geospatial extras** may still be needed for related formats (FlatGeobuf, Shapefile)


## Error Handling

- **Missing dependency**: optional libraries raise `ImportError` with an install hint (`pip install 'iterabledata[<extra>]'` when an extra exists).
- **Write mode**: read-only formats raise `WriteNotSupportedError` or `ValueError` when opened with `mode="w"`.
- **Bad or unsupported input**: may raise `ValueError`, `OSError`, or library-specific errors.
- See [Troubleshooting](/getting-started/troubleshooting) for decoding, detection, and engine issues.

## Related Formats

- [Parquet](parquet.md) — non-spatial columnar files
- [FlatGeobuf](flatgeobuf.md) — streaming indexed features
- [GeoJSON](geojson.md) / [GeoJSONSeq](geojsonseq.md) — JSON feature encodings
