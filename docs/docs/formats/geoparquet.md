# GeoParquet Format

GeoParquet is a [Parquet](parquet.md) profile that stores geospatial features with `geo` file metadata (primary geometry column, CRS, WKB encoding). IterableData reads and writes that metadata, exposes geometry as **raw WKB** by default, and can decode it to GeoJSON-like feature rows on request.

## File Extensions

- `.parquet` — GeoParquet is a Parquet file; use `format="geoparquet"` or GeoParquet content/metadata detection
- `.geoparquet` — used when present

## Implementation Details

### Reading

- Same streaming Parquet reader as [Parquet](parquet.md) — batch and projection pushdown are unchanged in the default `wkb` mode
- Loads and validates `geo` schema metadata from the Parquet footer (no row scan); a file without valid `geo` metadata raises `FormatParseError` unless `validate_metadata=False`
- Row modes:
  - `geometry_mode="wkb"` (default): rows pass through with raw WKB geometry bytes
  - `geometry_mode="feature"`: the primary geometry column is decoded (requires Shapely) and rows take the shared feature shape `{"geometry": geojson-like mapping, **properties}`
- Metadata accessors: `primary_geometry_column`, `crs()`, `geometry_encoding()`, `geometry_types()`, `bbox()`, plus the raw `geo_metadata` dict

### Writing

- Writes Parquet row groups with GeoParquet `geo` metadata
- Default primary column name is `geometry`; optional `crs`, `encoding`, `geometry_types`, and `bbox` are recorded on it
- `geometry_columns={name: {...}}` declares additional geometry columns; inconsistent metadata (non-dict column entries, non-serializable CRS) fails with a clear `ValueError`
- Unknown existing metadata fields are preserved when reopening a file for append-style writes

### Key Features

- **Metadata preservation**: version, primary column, per-column encoding/CRS/types/bbox
- **WKB by default**: no implicit geometry library decode
- **Parquet performance**: columnar batches, compression, projection

## Usage

```python
from iterable import open_iterable

with open_iterable("places.parquet", iterableargs={"format": "geoparquet"}) as source:
    print(source.crs(), source.geometry_types(), source.bbox())
    for row in source:
        print(row.get("name"), row.get("geometry"))  # geometry is WKB

with open_iterable(
    "places.parquet", iterableargs={"format": "geoparquet", "geometry_mode": "feature"}
) as source:
    for row in source:
        print(row["geometry"]["type"], row.get("name"))  # decoded geometry

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
| `geometry_mode` | `"wkb"` / `"feature"` | `"wkb"` | No | Raw WKB passthrough or Shapely-decoded feature rows (read mode) |
| `encoding` | str | `"WKB"` | No | Geometry encoding declared in `geo` metadata (write mode) |
| `geometry_types` | list of str | none | No | Geometry types declared for the primary column (write mode) |
| `bbox` | list of 4 floats | none | No | Bounding box declared for the primary column (write mode) |
| `geometry_columns` | dict | none | No | Metadata for additional geometry columns (write mode) |
| `validate_metadata` | bool | `True` | No | Reject files without valid `geo` metadata (read mode) |
| *(Parquet args)* | | | | Compression, batch size, and other [Parquet](parquet.md) write options still apply |

## Installation

```bash
pip install 'iterabledata[parquet]'
```

Requires `pyarrow`. `geometry_mode="feature"` additionally requires Shapely (`pip install 'iterabledata[geospatial]'`).

## Limitations

1. **Geometry is raw WKB** unless you request `geometry_mode="feature"`
2. **Requires pyarrow**; feature decoding requires Shapely
3. **Experimental geospatial extras** may still be needed for related formats (FlatGeobuf, Shapefile)


## Error Handling

- **Missing dependency**: optional libraries raise `ImportError` with an install hint (`pip install 'iterabledata[<extra>]'` when an extra exists).
- **Profile validation**: files without valid `geo` metadata raise `FormatParseError`; open them as `format="parquet"` or pass `validate_metadata=False`.
- **Bad or unsupported input**: may raise `ValueError`, `OSError`, or library-specific errors.
- See [Troubleshooting](/getting-started/troubleshooting) for decoding, detection, and engine issues.

## Related Formats

- [Parquet](parquet.md) — non-spatial columnar files
- [FlatGeobuf](flatgeobuf.md) — streaming indexed features
- [GeoJSON](geojson.md) / [GeoJSONSeq](geojsonseq.md) — JSON feature encodings
