## Context

File Geodatabase is a directory-based multi-layer geospatial store. MapInfo MIF is a text geometry file typically paired with a MID attribute table. IterableData already exposes Shapefile, GeoPackage, FlatGeobuf, and KML/KMZ/GPX as GeoJSON-like features.

## Goals / Non-Goals

- Goals:
  - Stream feature rows from FileGDB layers and MIF/MID pairs.
  - List FileGDB layers and select one explicitly when ambiguous.
  - Keep optional GDAL-family dependencies out of the core install.
- Non-Goals:
  - Full geodatabase administration (domains, topologies, versioning, editing workflows).
  - MapInfo TAB binary workspace support (`.tab` remains TSV-oriented unless separately proposed).
  - On-the-fly CRS reprojection.

## Decisions

### File Geodatabase

Treat a `.gdb` directory (or `.fgdb` path label) as a multi-table source. `list_tables()` returns layer names; `open_iterable` requires `table=` / `layer=` when more than one layer exists, matching SQLite/DuckDB multi-table patterns. Default row shape is a GeoJSON-like Feature.

### MapInfo MIF

Detect `.mif` and optionally co-located `.mid`. Yield one feature per geometry with attributes from MID columns. Missing MID yields geometry-only features with a clear diagnostic.

### Dependency strategy

Prefer a single optional geospatial extra that can back FileGDB and MIF through a maintained OGR binding when available, with ImportError messages naming the extra. If a lighter pure-Python MIF path is viable, it MAY be used without changing the public row contract.

## Risks / Trade-offs

- GDAL/FileGDB driver availability varies by platform → document supported drivers and skip tests when absent.
- Large FileGDB layers need bounded iteration → push filtering to the backend when possible; avoid loading all features.

## Migration Plan

Ship as experimental until golden fixtures from public open-data samples pass. No breaking API changes.

## Open Questions

- Should `.fgdb` zip wrappers be auto-extracted, or require an unpacked `.gdb` directory?
- Is write support for FileGDB in scope for v1, or read-only first?
