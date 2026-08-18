# Paimon Mosaic Format

## Description

Apache Paimon Mosaic is a columnar-bucket hybrid format optimized for wide tables. Columns are range-bucketed by name so projection pushdown decompresses only relevant buckets. IterableData wraps the official `paimon-mosaic` Python bindings and exposes dictionary rows through `open_iterable()`.

**Maturity**: experimental.

## File Extensions

- `.mosaic` — Mosaic data files

## Dependencies

```bash
pip install iterabledata[paimon-mosaic]
# or
pip install iterabledata[paimon]
```

Requires `paimon-mosaic>=0.2.0` and `pyarrow`. Platform wheels must be available for your OS/CPU.

## Usage

```python
from iterable import open_iterable

with open_iterable("wide.mosaic", mode="w", iterableargs={"num_buckets": 4}) as dest:
    dest.write_bulk([
        {"id": 1, "name": "Alice", "score": 1.5},
        {"id": 2, "name": "Bob", "score": 2.0},
    ])

with open_iterable("wide.mosaic") as source:
    for row in source:
        print(row)

# Projection pushdown (only requested columns / buckets)
with open_iterable("wide.mosaic", iterableargs={"columns": ["name", "score"]}) as source:
    for row in source:
        print(row)
```

## Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `columns` / `project` | list[str] | all | Column projection pushed to MosaicReader |
| `batch_size` | int | `1024` | Writer flush threshold in rows |
| `num_buckets` | int | backend default | Mosaic writer bucket count |
| `compression` | str/int | zstd | `zstd` / `none` or WriterOptions constant |
| `zstd_level` | int | backend default | Zstd level when compression is enabled |

## Detection

- Extension: `.mosaic`
- Footer magic: trailing `MOSA` on seekable sources

## Limitations

- Filename required (no plain stream mode)
- Experimental; stabilize after cross-tool golden fixtures pass
- Depends on native `paimon-mosaic` wheels

## See Also

- [Paimon Mosaic](https://paimon.apache.org/docs/mosaic/)
- [Paimon Row](/formats/paimon-row)
