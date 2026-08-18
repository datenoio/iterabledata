# Convert

Convert data between file formats (and from database sources to files) using `iterable.convert.convert`.

## Minimal script

See **examples/converter/convert.py** for a minimal CLI that converts between two files:

```bash
python examples/converter/convert.py source.csv output.jsonl
```

## API

```python
from iterable.convert import convert

result = convert(
    fromfile="data.csv",
    tofile="data.jsonl",
    iterableargs=None,      # optional read options (e.g. delimiter, encoding)
    toiterableargs=None,    # optional write options (e.g. keys for CSV)
    silent=True,
    is_flatten=False,
    use_totals=False,
    progress=None,
    show_progress=False,
    atomic=False,
)
print(result.rows_in, result.rows_out)
```

- **fromfile**: Path to source file, or database URL (e.g. `postgresql://...`, `mongodb://...`) with `iterableargs` specifying engine and query/table.
- **tofile**: Path to destination file. Format is inferred from extension (e.g. `.csv`, `.jsonl`, `.parquet`).
- **iterableargs**: Format-specific read options; for DB sources include `engine` and DB-specific params.
- **toiterableargs**: Format-specific write options (e.g. `keys` for CSV/JSONL).

Supported formats include CSV, JSON, JSONL, Parquet, XML, and others; see the main docs for the full list.
