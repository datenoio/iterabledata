## Context

IterableData already covers NetCDF, HDF5, CDF, and NumPy `.npy`. XYZ/CIF/PDB are text-oriented scientific structure formats; MATLAB MAT spans v4/v5 and HDF5-based v7.3.

## Goals / Non-Goals

- Goals:
  - Stream atom/row/point records from XYZ, CIF, and PDB.
  - Expose MAT variables as listable arrays with explicit selection and a documented leading-axis row mapping (aligned with Zarr/NumPy patterns).
- Non-Goals:
  - Full computational chemistry toolkits or structure validation suites.
  - MATLAB class-object reconstruction beyond arrays/structs that map cleanly to rows.

## Decisions

### XYZ

Treat as whitespace-delimited point tables: optional atom count/comment header, then rows of element + coordinates (+ optional properties). Default record: `element`, `x`, `y`, `z`.

### CIF / PDB

- CIF: iterate data blocks/items or atom_site loops depending on documented mode; start with `atom_site` loop rows when present.
- PDB: iterate ATOM/HETATM records; MODEL groups selectable when multi-model.

### MAT

Use `list_tables()` for variable names. Require `table=` when multiple variables exist. Map numeric arrays by leading axis into dict rows or `{ "values": ... }` records as documented. Prefer read-only in v1.

## Risks / Trade-offs

- CIF dialect diversity (core vs DDL) → support a documented subset; fail clearly otherwise.
- MAT v7.3 needs HDF5 stack → optional extra; older MAT via scipy.io when available.

## Migration Plan

Experimental until fixtures cover common public samples. No breaking changes.

## Open Questions

- Should chemical CIF and crystallographic CIF share one format id with modes, or separate ids?
- Default MAT row mapping for rank>2 arrays: flatten trailing dims or require explicit axis?
