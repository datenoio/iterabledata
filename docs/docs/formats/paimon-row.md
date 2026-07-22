# Paimon Row Format

## Description

Apache Paimon Row (`.row`) is a row-oriented file format optimized for O(1) random access by row number. Data is stored in ZSTD-compressed blocks with a compact null-bitmap row encoding, a delta/ZigZag/varint block index, and a fixed 32-byte footer ending in the `ROWS` magic.

**Maturity**: experimental.

## File Extensions

- `.row` — Paimon Row data files

**Important**: The format does **not** embed schema. Reads require an explicit schema.

## Dependencies

```bash
pip install iterabledata[paimon-row]
# or
pip install iterabledata[paimon]
```

Requires `zstandard`. Nested/VARIANT types are not supported in the first experimental cut.

## Usage

```python
from iterable.helpers.detect import open_iterable

schema = [("id", "bigint"), ("name", "string"), ("score", "double")]

with open_iterable("people.row", mode="w", iterableargs={"schema": schema}) as dest:
    dest.write_bulk([
        {"id": 1, "name": "Alice", "score": 1.5},
        {"id": 2, "name": "Bob", "score": 2.0},
    ])

with open_iterable("people.row", iterableargs={"schema": schema}) as source:
    for row in source:
        print(row)
```

## Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `schema` | list/dict/pyarrow.Schema | required on read | Physical field order and types |
| `block_size` | int | `65536` | Uncompressed block flush threshold (bytes) |

Supported primitive types: `boolean`, `tinyint`, `smallint`, `int`/`date`/`time`, `bigint`, `float`, `double`, `string`, `binary`.

## Detection

- Extension: `.row`
- Footer magic: trailing `ROWS` (`0x524F5753` as ASCII bytes) on seekable sources

## Limitations

- Schema must be provided for reads
- Nested ARRAY/MAP/ROW and VARIANT are not supported yet
- Stream mode without a filename is not the preferred path; use filenames for footer-based I/O

## See Also

- [Paimon Row Format Spec](https://paimon.apache.org/docs/master/concepts/spec/rowformat/)
- [Paimon Mosaic](/formats/paimon-mosaic)
