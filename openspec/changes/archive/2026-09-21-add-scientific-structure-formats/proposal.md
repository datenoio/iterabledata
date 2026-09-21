# Change: Add Scientific Structure Formats (XYZ, CIF, PDB, MATLAB MAT)

## Why

Open-data stats show frequent scientific structure formats still missing from IterableData: XYZ coordinate tables (~17k), crystallographic/chemical CIF (~1.2k), Protein Data Bank (`.pdb`), and MATLAB `.mat` (~1k). These are natural row/array iterables adjacent to existing NetCDF/HDF5/NumPy support.

## What Changes

- Add XYZ molecular/point-table reading (and writing where straightforward).
- Add CIF reading for crystallographic or chemical CIF records with a documented row mapping.
- Add PDB reading yielding atom/heterogen records (and optional model selection).
- Add MATLAB `.mat` reading with array/variable listing via `list_tables()` and explicit variable selection.
- Register formats, optional deps, fixtures, tests, and docs.

## Impact

- Affected specs: `scientific-structure-formats` (new)
- Affected code: new datatypes, registry/detection, optional extras, docs/tests
- New dependencies: optional scientific stack pieces (e.g. `scipy`/`h5py` for MAT v7.3, lightweight CIF/PDB parsers where possible)
