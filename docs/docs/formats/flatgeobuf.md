# FlatGeobuf Format

FlatGeobuf is a compact, cloud-friendly binary encoding for geospatial features. IterableData streams features through Fiona/GDAL and optionally filters with a bounding box. It is **read-only** in this release.

## File Extensions

- `.fgb` — FlatGeobuf feature collections

## Implementation Details

### Reading

- Opens a local filename (streams are not supported)
- Optional `bbox=(minx, miny, maxx, maxy)` is passed to Fiona for spatial filtering
- Each row is `{**properties, "geometry": geojson-like geometry}`

### Writing

Writing is not supported. Use [GeoParquet](geoparquet.md) or [GeoJSONSeq](geojsonseq.md) for writeable geospatial pipelines. Attempting to write raises `WriteNotSupportedError`.

### Key Features

- **Streaming**: one feature at a time
- **BBox selection**: skip features outside a window
- **GDAL/Fiona**: uses the installed FlatGeobuf driver

## Usage

```python
from iterable import open_iterable

with open_iterable("features.fgb", iterableargs={"format": "flatgeobuf"}) as source:
    for row in source:
        print(row.get("name"), row["geometry"])

with open_iterable(
    "features.fgb",
    iterableargs={"format": "flatgeobuf", "bbox": (-10.0, 40.0, 0.0, 50.0)},
) as source:
    for row in source:
        print(row)
```

## Parameters

| Parameter | Type | Default | Required | Description |
|-----------|------|---------|----------|-------------|
| `bbox` | tuple of 4 floats | none | No | `(minx, miny, maxx, maxy)` spatial filter |

## Error Handling

- **ImportError**: Missing Fiona/GDAL — install with `pip install iterabledata[geospatial]`
- **ValueError**: Stream input or missing filename (`FlatGeobuf requires a local filename`)
- **WriteNotSupportedError**: Writing FlatGeobuf is not supported
- **FileNotFoundError** / Fiona errors: missing path, missing FlatGeobuf driver, or corrupt `.fgb`

See [Troubleshooting](/getting-started/troubleshooting) for more help.

## Installation

```bash
pip install 'iterabledata[geospatial]'
```

Requires Fiona with GDAL FlatGeobuf support.

## Limitations

1. **Read-only**
2. **Local filename required**
3. **Requires Fiona/GDAL**

## Related Formats

- [GeoParquet](geoparquet.md) — Parquet with geometry metadata (read and write)
- [GeoPackage](geopackage.md) — SQLite-based geospatial container
- [GeoJSONSeq](geojsonseq.md) — streaming JSON features
