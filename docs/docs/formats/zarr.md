# Zarr Format

Zarr is a chunked array store for large n-dimensional data. IterableData exposes one named array as rows: scalars become `{"value": scalar}` and higher-rank slices become `{"value": list}`. Stores with more than one array require an explicit `array` name.

**Maturity**: experimental.

## File Extensions

- Directory stores (Zarr v2/v3), typically a folder path rather than a single file
- No unique filename suffix; pass `format="zarr"` or a directory that is a Zarr group

## Implementation Details

### Reading

- Opens a Zarr group from a **directory path** (streams are not supported)
- If the store has exactly one array, that array is used
- Multi-array stores require `iterableargs={"array": "name"}`
- Reads along axis 0 in bounded chunks (`chunks`, default 1024)
- `list_tables()` lists array names in the store

### Writing

- Appends chunk-sized blocks to a named array
- Records should contain a `value` field, or the field named by `array`
- Specify `array` when writing records that have more than one field
- Optional `dtype` controls the NumPy/Zarr dtype of a newly created array

### Key Features

- **Bounded memory**: chunked reads and writes
- **v2 and v3 stores**: via the `zarr` package
- **Totals**: `totals()` returns the length of axis 0
- **Streaming**: `is_streaming()` is `True`

## Usage

```python
from iterable import open_iterable

# Read a single-array store
with open_iterable("data.zarr", iterableargs={"format": "zarr"}) as source:
    for row in source:
        print(row["value"])

# Multi-array store
with open_iterable("store.zarr", iterableargs={"format": "zarr", "array": "temperature"}) as source:
    for row in source:
        print(row["value"])

# Write (creates or appends chunked blocks)
with open_iterable("out.zarr", mode="w", iterableargs={"format": "zarr", "array": "value"}) as dest:
    dest.write_bulk([{"value": 1.0}, {"value": 2.0}])
```

## Parameters

| Parameter | Type | Default | Required | Description |
|-----------|------|---------|----------|-------------|
| `array` | str | first/only array | Yes if more than one array | Array name to read or write |
| `chunks` | int | `1024` | No | Row chunk size along axis 0 |
| `dtype` | str | inferred | No | NumPy dtype when creating an array on write |

## Installation

```bash
pip install 'iterabledata[zarr]'
```

Requires `zarr` and `numpy`.

## Limitations

1. **Directory path required**: not a stream
2. **Experimental**: API and chunking defaults may change
3. **One array per iterable**: select with `array=`
4. **Rows are `{value: ...}`** unless you write with a matching field name


## Error Handling

- **Missing dependency**: optional libraries raise `ImportError` with an install hint (`pip install 'iterabledata[<extra>]'` when an extra exists).
- **Write mode**: read-only formats raise `WriteNotSupportedError` or `ValueError` when opened with `mode="w"`.
- **Bad or unsupported input**: may raise `ValueError`, `OSError`, or library-specific errors.
- See [Troubleshooting](/getting-started/troubleshooting) for decoding, detection, and engine issues.

## Related Formats

- [HDF5](hdf5.md) — hierarchical scientific arrays
- [NetCDF](nc.md) — self-describing array datasets
- [NumPy](npy.md) — `.npy` / `.npz` array rows
