---
title: MVT Format
description: Mapbox Vector Tiles in IterableData
---

# MVT Format

## Description

Mapbox Vector Tiles (MVT) are compact binary tiles that encode layered vector features for web maps. IterableData decodes a tile with `mapbox-vector-tile` and flattens features from all layers into row dicts. It is **read-only** in this release. Aliases: `pbf`.

## File Extensions

- `.mvt` — Mapbox Vector Tile
- `.pbf` — Protocol Buffer tile alias (same decoder)

## Implementation Details

### Reading

- Reads the entire tile as binary, then `mapbox_vector_tile.decode(...)`
- Iterates every layer and yields one dict per feature
- Record shape: `layer`, `geometry`, `properties`, `type`, `id`
- `totals()` sums features across layers

### Writing

Writing is not supported (`WriteNotSupportedError`). Produce tiles with dedicated MVT tooling, or use [GeoJSONSeq](geojsonseq.md) / [GeoParquet](geoparquet.md) for writeable feature pipelines.

### Key Features

- **Multi-layer flatten**: all layers in one iterator
- **Layer name preserved**: each feature includes its source `layer`
- **Binary datamode**: codec wrappers apply when present

## Usage

```python
from iterable import open_iterable

with open_iterable("tile.mvt") as source:
    for feature in source:
        print(feature["layer"], feature.get("properties"), feature.get("geometry"))
```

## Parameters

No format-specific `iterableargs`.

## Installation

```bash
pip install 'iterabledata[mvt]'
# or (includes mapbox-vector-tile among other geospatial deps)
pip install 'iterabledata[geospatial]'
```

## Limitations

1. **Read-only**
2. **Whole-tile decode**: the tile is loaded into memory
3. **Requires mapbox-vector-tile**
4. Geometry coordinates are in tile-local space as returned by the decoder

## Error Handling

- **ImportError**: missing `mapbox-vector-tile`
- **WriteNotSupportedError**: any write mode
- **FormatParseError**: tile bytes that fail to decode
- **I/O errors**: missing or unreadable files

## Related Formats

- [TopoJSON](topojson.md) — topology-encoded vector data
- [GeoJSON](geojson.md) — JSON features
- [FlatGeobuf](flatgeobuf.md) — cloud-friendly binary features
