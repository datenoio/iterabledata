# Converter

Minimal CLI script that converts data between two file formats using `iterable.convert.core.convert`.

## Script

- **convert.py** – Converts from a source file to a destination file. Format is inferred from file extensions.

## Run

From the project root:

```bash
python examples/converter/convert.py <source_file> <destination_file>
```

Examples:

```bash
python examples/converter/convert.py data.csv data.jsonl
python examples/converter/convert.py data.jsonl data.csv
python examples/converter/convert.py data.csv output.parquet
```

The script uses `convert(fromfile=..., tofile=..., silent=False, use_totals=True)`. Progress and row counts are printed.

## Full API

For more options (read/write args, progress callbacks, atomic writes, etc.), see **examples/convert/README.md** and the `iterable.convert.core.convert` API.

## Supported formats

Any format supported by IterableData (CSV, JSON, JSONL, Parquet, XML, and others). The source and destination formats are detected from the file extensions.
