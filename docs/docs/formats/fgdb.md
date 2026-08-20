---
title: File Geodatabase Format
description: ESRI File Geodatabase layers in IterableData
---

# File Geodatabase (FGDB) Format

## Description

ESRI File Geodatabase (`.gdb`) is a directory-based geospatial container for feature classes and tables. IterableData streams a selected layer through Fiona’s OpenFileGDB driver as GeoJSON-like Features. It is **read-only** and marked **experimental**. Aliases: `gdb`.

## File Extensions

- `.gdb` — File Geodatabase directory (path to the `.gdb` folder)
- Registry id: `fgdb`

## Implementation Details

### Reading

- Requires a **directory path** (filename); streams/codecs are not supported
- Lists layers with `fiona.listlayers`
- Selects layer via `layer` or `table` in `iterableargs`
- If exactly one layer exists, it is used automatically; multiple layers require an explicit selection
- Yields `{"type": "Feature", "id", "properties", "geometry"}`
- Streaming: features are not preloaded into a list

### Writing

Writing is not supported (`WriteNotSupportedError`).

### Key Features

- **Layer selection**: `layer` / `table`
- **Streaming features**: Fiona collection iteration
- **`list_tables()`**: discover layer names

## Usage

```python
from iterable import open_iterable

with open_iterable(
    "data.gdb",
    iterableargs={"format": "fgdb", "layer": "roads"},
) as source:
    for feature in source:
        print(feature["properties"], feature["geometry"])
```

## Parameters

| Parameter | Type | Default | Required | Description |
|-----------|------|---------|----------|-------------|
| `layer` | str | none | Conditional | Layer / feature class name |
| `table` | str | none | Conditional | Alias for `layer` |

Required when the geodatabase contains more than one layer.

## Installation

```bash
pip install 'iterabledata[geospatial]'
```

Requires Fiona with OpenFileGDB support (GDAL).

## Limitations

1. **Read-only**
2. **Directory path required** (not a single flat file stream)
3. **Experimental** maturity
4. **Requires Fiona/GDAL** OpenFileGDB driver
5. Multi-layer GDB without `layer`/`table` raises `ValueError`

## Error Handling

- **ImportError**: missing `fiona` — install `iterabledata[geospatial]`
- **WriteNotSupportedError**: any write mode or `write()` / `write_bulk()`
- **ReadError**: stream/codec-only open without a path
- **ValueError**: no layers, or multiple layers without selection
- **I/O / Fiona errors**: missing path or unsupported driver

## Related Formats

- [GeoPackage](geopackage.md) — SQLite geospatial container
- [FlatGeobuf](flatgeobuf.md) — binary feature collections
- [Shapefile](shapefile.md) — ESRI shapefile
- [GeoParquet](geoparquet.md) — Parquet with geometry
