## 1. Registry and shared patterns

- [x] 1.1 Add descriptors/aliases for `xyz`, `cif`, `pdb`, and `mat`.
- [x] 1.2 Document row mappings and MAT/CIF modes.
- [x] 1.3 Add optional extras and ImportError messaging.

## 2. Implementations

- [x] 2.1 Implement XYZ reader/writer for common point-table variants.
- [x] 2.2 Implement CIF reader for documented atom_site/data-block subset.
- [x] 2.3 Implement PDB ATOM/HETATM reader with optional model selection.
- [x] 2.4 Implement MAT reader with `list_tables()` and variable selection.

## 3. Tests and docs

- [x] 3.1 Add fixtures for XYZ, CIF, PDB, and MAT (v5 and v7.3 if feasible).
- [x] 3.2 Add detection, malformed, multi-variable, and optional-dependency tests.
- [x] 3.3 Document formats, schemas, and limitations.
- [x] 3.4 Run `openspec validate add-scientific-structure-formats --strict`.
