# Zarr Format

Zarr is a chunked array store for large n-dimensional data, in v2 and v3 layouts, backed by local directories or fsspec-compatible stores. IterableData exposes one named array as a bounded stream of rows. Stores with more than one array require an explicit `array` name.

**Maturity**: experimental.

## File Extensions

- Directory stores (Zarr v2/v3), typically a `.zarr` folder rather than a single file
- fsspec-style store URLs (`memory://`, `s3://`, ...) via the `zarr`/`fsspec` stack
- No reliable content signature; detection is by `.zarr` directory name or explicit `format="zarr"`

## Row Mapping

Iteration walks one axis (default `axis=0`) and converts each slice to a row:

| Array kind | Row shape |
|------------|-----------|
| Structured (named fields) | `{"field": value, ...}` — one dict per element |
| Dense 1-D | `{"index": i, "value": scalar}` |
| Dense N-D | `{"index": i, "values": slice_as_list}` |
| Scalar (0-d) | one record `{"value": scalar}` |

`index` is the absolute index along the iteration axis, so sliced selections keep their original offsets. With `array_mode="numpy"`, values stay `numpy` scalars/arrays instead of Python conversions.

## Implementation Details

### Reading

- Opens a Zarr group from a **directory path or store URL** (streams are not supported)
- If the store has exactly one array, that array is used; multi-array stores require `iterableargs={"array": "name"}`
- `list_tables()` lists array names in the store
- Reads are bounded: each internal fetch is one array-chunk length along the iteration axis, and `read_bulk(n)` never holds more than ~one chunk plus the requested batch
- `slice=(start, stop, step)` selects a window along the iteration axis before value conversion; `totals()` reflects the selection
- `fields=[...]` (alias `columns`) projects structured arrays to a field subset
- `axis=N` iterates along a different axis

### Writing

- Records are buffered and flushed in `chunks`-sized blocks (default 1024); appends resize along axis 0
- Single-field records create/append a dense array named after the field (or `array`); multi-field records infer a **structured array** named `records` from the first batch
- Optional `dtype` (NumPy dtype spec, including structured `[("name", "i8"), ...]`) sets an explicit creation schema; `zarr_format=2` writes a v2 store
- `mode="w"` truncates an existing array of the same name
- Later batches must match the array: incompatible shapes, field sets, or dtypes that cannot be **safely** cast (e.g. `float64` into `int64`, longer strings into shorter fixed-width) raise `ValueError` instead of silently coercing

### Security

- Object-dtype arrays rely on pickle-style codecs that can execute untrusted deserialization. Reads and writes of object-dtype arrays are rejected by default; pass `allow_object=True` only for trusted stores. (zarr 3 itself refuses object arrays without a registered codec, so this mainly guards zarr 2 stores.)

### Key Features

- **Bounded memory**: chunk-bounded reads and writes
- **v2 and v3 stores**: via the `zarr` package
- **Totals**: `totals()` returns the selected row count along the iteration axis
- **Streaming**: `is_streaming()` is `True`

## Usage

```python
from iterable import open_iterable

# Read a single-array store
with open_iterable("data.zarr") as source:
    for row in source:
        print(row["value"])

# Multi-array store with a sliced selection
with open_iterable(
    "store.zarr",
    iterableargs={"format": "zarr", "array": "temperature", "slice": (1000, 2000)},
) as source:
    for row in source:
        print(row["index"], row["values"])

# Structured array, projected to one field
with open_iterable("store.zarr", iterableargs={"format": "zarr", "array": "records", "fields": ["name"]}) as source:
    for row in source:
        print(row["name"])

# Write (infers a dense or structured array from the records)
with open_iterable("out.zarr", mode="w", iterableargs={"format": "zarr", "array": "value"}) as dest:
    dest.write_bulk([{"value": 1.0}, {"value": 2.0}])

# fsspec-backed store URL (pass URLs to ZarrIterable directly;
# open_iterable() covers local directories and registered cloud schemes)
from iterable.datatypes.zarr import ZarrIterable

with ZarrIterable("memory://bucket/store.zarr", array="value") as source:
    print(source.read_bulk(10))
```

## Parameters

| Parameter | Type | Default | Required | Description |
|-----------|------|---------|----------|-------------|
| `array` | str | first/only array | Yes if more than one array | Array name to read or write |
| `axis` | int | `0` | No | Iteration axis |
| `slice` | tuple | none | No | `(start, stop[, step])` window along the iteration axis |
| `fields` / `columns` | list | all fields | No | Structured-array field projection |
| `chunks` | int | `1024` | No | Write chunk size along the append axis |
| `dtype` | str/list | inferred | No | NumPy dtype when creating an array on write |
| `array_mode` | str | `"python"` | No | `"python"` converts to lists/scalars; `"numpy"` keeps arrays |
| `allow_object` | bool | `False` | No | Opt-in to object-dtype arrays (trusted stores only) |
| `zarr_format` | int | zarr default (3) | No | Store version when writing (`2` or `3`) |
| `storage_options` | dict | none | No | fsspec storage options for URL stores |

## Installation

```bash
pip install 'iterabledata[zarr]'
```

Requires `zarr` and `numpy`.

## Limitations

1. **Directory/URL path required**: streams are not supported
2. **Experimental**: API and chunking defaults may change
3. **One array per iterable**: select with `array=`
4. **Append axis**: writes append along axis 0 only
5. **No destructive coercion**: widening appends (e.g. `int32` into `int64`) are allowed; narrowing or truncating appends fail — pass an explicit `dtype` up front when later batches may widen
6. **`open_iterable()` URL reads**: fsspec-style URLs that are not registered cloud schemes (e.g. `memory://`) work through `ZarrIterable` directly; `open_iterable()` reads require a local directory

## Performance

- Keep the array's chunk length along the iteration axis close to your typical `read_bulk(n)` size; very large chunks raise peak memory, very small chunks increase per-chunk overhead
- Prefer `read_bulk()` over per-row `read()` for large arrays
- `slice` selections still skip data before conversion but fetch whole chunks intersecting the window

## Error Handling

- **Missing dependency**: raises `ImportError` naming the extra (`pip install 'iterabledata[zarr]'`)
- **Missing store**: `FileNotFoundError`; a directory or URL without valid Zarr metadata raises `ValueError` ("not a valid Zarr store")
- **Ambiguous store**: `ValueError` listing available arrays; unknown `array=` raises `KeyError`
- **Schema/shape/dtype mismatch on append**: `ValueError`; no silent destructive coercion
- **Object-dtype arrays**: `ValueError` unless `allow_object=True`
- See [Troubleshooting](/getting-started/troubleshooting) for decoding, detection, and engine issues.

## Related Formats

- [HDF5](hdf5.md) — hierarchical scientific arrays
- [NetCDF](nc.md) — self-describing array datasets
- [NumPy](npy.md) — `.npy` / `.npz` array rows
