---
title: DXF Format
description: AutoCAD DXF entities in IterableData
---

# DXF Format

## Description

DXF (Drawing Exchange Format) is Autodesk’s CAD interchange format for 2D/3D drawing entities. IterableData reads modelspace entities via `ezdxf` and yields one dict per entity with type-specific geometry fields. It is **read-only** in this release.

## File Extensions

- `.dxf` — Drawing Exchange Format

## Implementation Details

### Reading

- Opens via `ezdxf.readfile` (filename preferred) or `ezdxf.read` for streams
- Iterates modelspace entities
- Common fields: `dxftype`, `layer`, `color`, `handle`
- Type-specific fields for LINE, CIRCLE, ARC, POINT, TEXT, LWPOLYLINE, POLYLINE
- `totals()` counts modelspace entities

### Writing

Writing is not supported (`WriteNotSupportedError`).

### Key Features

- **Entity streaming**: one CAD entity per row
- **Geometry extraction**: coordinates and parameters for common entity types
- **Layer / color metadata**: when present on the entity

## Usage

```python
from iterable import open_iterable

with open_iterable("drawing.dxf") as source:
    for entity in source:
        print(entity["dxftype"], entity.get("layer"), entity)
```

## Parameters

No format-specific `iterableargs`.

## Installation

```bash
pip install 'iterabledata[dxf]'
```

Requires `ezdxf`.

## Limitations

1. **Read-only**
2. **Modelspace only**: paper space and complex blocks are not fully expanded
3. **Requires ezdxf**
4. Unsupported entity types still yield basic metadata without full geometry

## Error Handling

- **ImportError**: missing `ezdxf`
- **WriteNotSupportedError**: write mode
- **FormatParseError** / **ReadError**: corrupt DXF or stream read failures
- **I/O errors**: missing path

## Related Formats

- [Shapefile](shapefile.md) — GIS vector layers
- [GeoJSON](geojson.md) — JSON geographic features
- [ASCII Grid](asc.md) — raster grid cells
