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

The current native adapters are Parquet and Arrow/Feather v2. Projection and
row-range/slice selection are supported; unsupported predicates or tables fall
back to the regular row/bulk loop unless `strict_native=True` is supplied.
Native transfer is intentionally disabled when flattening or validation hooks
would require row materialization. The legacy `read_bulk()`/`write_bulk()` API
remains the compatibility fallback for every format.
