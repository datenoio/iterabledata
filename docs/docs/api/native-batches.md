# Native batch conversion

Columnar formats may opt into an advanced batch protocol:

```python
from iterable.convert import BatchSelection, convert

convert(
    "input.parquet",
    "output.parquet",
    use_native_batch=True,
    selection=BatchSelection(columns=("id", "event_time"), batch_size=8192),
)
```

## Supported adapters and backends

| Format | Backend | Version requirement | Pushdown |
| --- | --- | --- | --- |
| Parquet | `pyarrow` | pyarrow >= 14 | columns, predicate, row range/slice |
| Arrow IPC / Feather v2 | `pyarrow` | pyarrow >= 14 | columns, row range/slice |
| ORC | `pyarrow.orc` (option `backend="pyarrow"`) | pyarrow >= 14 | columns, predicate (file-path sources), row range/slice |
| Delta Lake | `deltalake` + `pyarrow` | deltalake >= 0.15 | columns, predicate, row range/slice |
| Apache Iceberg | `pyiceberg` | pyiceberg >= 0.5 | columns, predicate, row range/slice |
| Lance | `pylance` | pylance >= 0.9 | columns, predicate (SQL filter), offset/limit, slice |
| NumPy (`.npy`/`.npz`) | `numpy` | numpy >= 1.24 | table (npz array), columns, row range/slice (native striding) |
| HDF5 | `h5py` | h5py >= 3.0 | table (dataset path), slice (hyperslab), columns (structured dtypes) |
| NetCDF | `netCDF4` | netCDF4 >= 1.6 | table (group), columns (variables), slice (strided reads) |

Predicates use a portable structured form — a `(field, op, value)` triple
or a list of triples combined with AND, with `op` one of `==`, `!=`, `<`,
`<=`, `>`, `>=` — translated to the backend's filter API. Backend-native
expressions (`pyarrow.compute.Expression`, PyIceberg boolean expressions,
Lance SQL filter strings) are also accepted as a trusted raw API.

ORC note: the default ORC backend is `pyorc` when installed (row path
unchanged). Pass `iterableargs={"backend": "pyarrow"}` to enable the batch
path; when `pyorc` is absent the pyarrow backend is selected automatically.

Unsupported predicates or tables fall back to the regular row/bulk loop,
which applies the selection row-wise with identical results, unless
`strict_native=True` is supplied (which raises instead). Native transfer is
intentionally disabled when flattening or validation hooks would require row
materialization. The legacy `read_bulk()`/`write_bulk()` API remains the
compatibility fallback for every format.
