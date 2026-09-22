# FlatGeobuf Format

FlatGeobuf is a compact, cloud-friendly binary encoding for geospatial features. IterableData streams features through Fiona/GDAL and optionally filters with a bounding box, using the packed spatial index when present.

## File Extensions

- `.fgb` — FlatGeobuf feature collections

## Implementation Details

### Reading

- Opens a local filename (streams are not supported)
- Optional `bbox=(minx, miny, maxx, maxy)` uses the packed spatial index when present; without an index GDAL falls back to a full scan with identical filtering semantics
- Each row is `{**properties, "geometry": geojson-like geometry}`
- Files written with a spatial index are physically ordered by the packed Hilbert R-tree, so sequential read order is index order, not insertion order

### Writing

- Streams features one at a time (bounded memory; no whole-file buffering)
- The schema (geometry type and property fields) is inferred from the first record; later records are aligned to it (missing properties become `None`)
- Pass `geometry_type="Unknown"` to write mixed geometry types in one file
- Optional `crs` (e.g. `"EPSG:4326"`) and `spatial_index=False` to skip the packed index
- Accepts both the read row shape and full GeoJSON Features (`{"type": "Feature", "geometry": ..., "properties": ...}`)

### Key Features

- **Streaming**: one feature at a time in both directions
- **BBox selection**: index-accelerated window queries
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

with open_iterable(
    "out.fgb",
    mode="w",
    iterableargs={"format": "flatgeobuf", "crs": "EPSG:4326"},
) as dest:
    dest.write({"geometry": {"type": "Point", "coordinates": (1.0, 2.0)}, "name": "Origin"})
```

## Parameters

| Parameter | Type | Default | Required | Description |
|-----------|------|---------|----------|-------------|
| `bbox` | tuple of 4 floats | none | No | `(minx, miny, maxx, maxy)` spatial filter (read mode) |
| `crs` | str / mapping | none | No | CRS recorded on write (e.g. `"EPSG:4326"`) |
| `spatial_index` | bool | `True` | No | Write the packed Hilbert R-tree spatial index |
| `geometry_type` | str | inferred | No | Schema geometry type; use `"Unknown"` for mixed types |

## Error Handling

- **ImportError**: Missing Fiona/GDAL — install with `pip install iterabledata[geospatial]`
- **ValueError**: Stream input or missing filename (`FlatGeobuf requires a local filename`)
- **FormatParseError**: Corrupt or non-FlatGeobuf input (driver open failure)
- **WriteError**: Record incompatible with the established schema (e.g. geometry type mismatch without `geometry_type="Unknown"`)
- **FileNotFoundError** / Fiona errors: missing path or missing FlatGeobuf driver

See [Troubleshooting](/getting-started/troubleshooting) for more help.

## Installation

```bash
pip install 'iterabledata[geospatial]'
```

Requires Fiona with GDAL FlatGeobuf support.

## Limitations

1. **Local filename required** — streams and codec wrapping are not supported
2. **Requires Fiona/GDAL**
3. **Schema from first record** — property fields and their types are fixed by the first written feature; extra keys on later records are dropped
4. **Index order** — indexed files read back in packed R-tree order, not insertion order

## Related Formats

- [GeoParquet](geoparquet.md) — Parquet with geometry metadata (read and write)
- [GeoPackage](geopackage.md) — SQLite-based geospatial container
- [GeoJSONSeq](geojsonseq.md) — streaming JSON features
