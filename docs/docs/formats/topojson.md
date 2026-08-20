---
title: TopoJSON Format
description: TopoJSON topology features in IterableData
---

# TopoJSON Format

Read TopoJSON topologies as GeoJSON-like features (when `topojson` is installed); write buffered geometries as a Topology on close.

## Overview

| Property | Value |
|----------|-------|
| Format id | `topojson` |
| Class | `TopoJSONIterable` |
| Extensions | `.topojson` |
| Read | Yes |
| Write | Yes |
| Extra | `topojson` (`topojson`) |
| Maturity | stable |

## File Extensions

- `.topojson` — TopoJSON topology documents

## Implementation Details

### Reading

- Small files: `json.load`, then (if `topojson` is installed) convert topology objects to GeoJSON features
- Large files (> ~10MB) or non-seekable streams: optional `ijson` streaming over `objects.item` (raw topology objects; full Topology→GeoJSON conversion needs the whole file)
- Without the `topojson` library, yields the raw topology structure

### Writing

- Buffers geometry dicts in memory
- On `close()`, writes a single `Topology` with a `GeometryCollection` under `objects.collection`
- Nested write uses JSON text encoding

### Key Features

- **Read and write**
- **Optional conversion**: TopoJSON → GeoJSON features when the library is present
- **Streaming fallback**: `ijson` for large files (raw objects)

## Usage

```python
from iterable import open_iterable

with open_iterable("map.topojson") as source:
    for feature in source:
        print(feature.get("type"), feature.get("geometry"))

with open_iterable("out.topojson", mode="w") as dest:
    dest.write({"type": "Point", "coordinates": [0.0, 0.0]})
    dest.write({"type": "Point", "coordinates": [1.0, 1.0]})
```

## Parameters

| Parameter | Type | Default | Required | Description |
|-----------|------|---------|----------|-------------|
| `encoding` | str | `'utf8'` | No | Text encoding for the JSON document |

## Error Handling

- **FormatParseError**: Invalid JSON TopoJSON document
- **ImportError**: Optional — full GeoJSON conversion needs `topojson` (`pip install iterabledata[topojson]`); reading raw topology still works without it for small files
- **FileNotFoundError**: Path is wrong or the file is missing
- Corrupt streaming input may fall back to non-streaming load or raise parse errors

See [Troubleshooting](/getting-started/troubleshooting) for more help.

## Installation

```bash
pip install 'iterabledata[topojson]'
```

For large-file streaming reads, also install `ijson` (included in the `json` extra): `pip install iterabledata[json]`.

## Limitations

1. **Write buffers until close** — one Topology document per file
2. **Streaming reads skip full Topology→GeoJSON conversion**
3. **Optional topojson library** for feature conversion

## Related Formats

- [GeoJSON](geojson.md) — GeoJSON features
- [MVT](mvt.md) — Mapbox Vector Tiles
- [FlatGeobuf](flatgeobuf.md) — binary geospatial features
- [Supported formats](/formats/)
