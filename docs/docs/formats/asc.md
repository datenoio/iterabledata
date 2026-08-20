---
title: ASCII Grid Format
description: Esri ASCII Grid rasters in IterableData
---

# ASCII Grid (ASC) Format

## Description

Esri ASCII Grid (`.asc`) is a text raster format with a small header (`ncols`, `nrows`, `cellsize`, corner/center, optional `NODATA_value`) followed by cell values. IterableData streams cells (default) or whole rows, and can **write** cell-mode records back to ASC. Marked **experimental**. Aliases: `ascii-grid`, `asciigrid`.

## File Extensions

- `.asc` — Esri ASCII Grid
- Registry id: `asc`

## Implementation Details

### Reading

- Parses the header, then streams numeric tokens
- Default `mode="cell"`: yields `{row, col, x, y, value}` and **skips** nodata cells
- `mode="row"`: yields `{row, values: [...]}` including nodata
- Computes cell centers from `xllcorner`/`yllcorner` or `xllcenter`/`yllcenter`

### Writing

- Supported in **cell mode** only (`mode="w"` with `iterableargs={"mode": "cell"}` or default)
- Buffers cell records and flushes an ASC grid on close (via context manager)
- Infers `ncols`/`nrows`/`cellsize`/origin from buffered cells; uses `NODATA_value -9999` for gaps
- Row mode writing raises `WriteNotSupportedError`

### Key Features

- **Cell or row iteration**
- **Writable** (cell mode)
- **Stdlib only**: no geospatial extra required
- **Streaming read** for cell/row tokens

## Usage

```python
from iterable import open_iterable

# Read cells (skip NODATA)
with open_iterable("dem.asc") as source:
    for cell in source:
        print(cell["x"], cell["y"], cell["value"])

# Read full rows
with open_iterable("dem.asc", iterableargs={"mode": "row"}) as source:
    for row in source:
        print(row["row"], len(row["values"]))

# Write cell mode
with open_iterable("out.asc", mode="w") as dest:
    dest.write({"row": 0, "col": 0, "x": 0.5, "y": 1.5, "value": 42.0})
    dest.write({"row": 0, "col": 1, "x": 1.5, "y": 1.5, "value": 43.0})
```

## Parameters

| Parameter | Type | Default | Required | Description |
|-----------|------|---------|----------|-------------|
| `mode` | str | `cell` | No | `cell` (per-cell records) or `row` (per-row value lists). Passed via `iterableargs` — not the file open mode. |
| `encoding` | str | `utf-8` | No | Text encoding |

## Installation

```bash
pip install iterabledata
```

No format-specific extra.

## Limitations

1. **Experimental** maturity
2. **Write is cell-mode only**; row-mode write is rejected
3. Write rebuilds a dense grid from buffered cells (memory scales with extent)
4. Incomplete data lines raise `ValueError`
5. Not a full GDAL raster stack (CRS, multi-band, etc. unsupported)

## Error Handling

- **WriteNotSupportedError**: writing while opened read-only, or writing in row mode
- **ValueError**: invalid/missing header fields, incomplete data, or no filename/stream for read
- **I/O errors**: missing or unreadable paths
- No third-party **ImportError** for this format

## Related Formats

- [XYZ](xyz.md) — point XYZ text grids
- [NetCDF](nc.md) — array-oriented scientific rasters
- [File Geodatabase](fgdb.md) — ESRI geodatabase layers
- [DXF](dxf.md) — CAD entities
