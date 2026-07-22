# Change: Add ESRI File Geodatabase and MapInfo MIF Support

## Why

Dateno open-data format stats show File Geodatabase (`.fgdb` / `.gdb`, ~14.5k combined) and MapInfo Interchange (`.mif`, ~16k) as the highest-frequency geospatial iterable formats not yet supported by IterableData. Both are common municipal and cadastral distribution formats and fit the existing GeoJSON-like feature row model used by Shapefile, GeoPackage, and KML.

## What Changes

- Add read support for ESRI File Geodatabase directories/archives, with layer listing via `list_tables()` and explicit layer selection.
- Add read (and write where the backend allows) support for MapInfo MIF/MID feature pairs.
- Register extensions/aliases (`fgdb`, `gdb`, `mif`), descriptors, optional geospatial extras, fixtures, and docs.
- Expose feature records consistent with other geospatial iterables (geometry + properties).

## Impact

- Affected specs: `geospatial-formats`
- Affected code: new datatypes under `iterable/datatypes/`, format registry/detection, optional deps in `pyproject.toml`, docs under `docs/docs/formats/`, tests/fixtures
- New dependencies: optional maintained FileGDB and MapInfo readers (e.g. via `pyogrio`/`fiona`/GDAL stack or dedicated libs), scoped under a geospatial extra
