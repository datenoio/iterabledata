# Ops examples

High-level operations for inspection, statistics, schema inference, transformation, and filtering.

## Scripts

- **filter_example.py** – Filter rows by expression (`filter_expr`) and regex search (`search`).
- **inspect_example.py** – Count rows, get head/tail, detect headers (`count`, `head`, `tail`).
- **stats_example.py** – Compute field statistics and frequency (`compute`, `frequency`).
- **schema_example.py** – Infer schema and export to JSON Schema (`infer`, `to_json_schema`).
- **transform_example.py** – Slice and select (`head`, `tail`, `sample_rows`, `select_columns`).

## Run

Use a CSV or JSONL file as input. Example with a local file:

```bash
# From project root, with a data file (e.g. data.csv or tests/fixtures/...)
python examples/ops/filter_example.py data.csv
python examples/ops/inspect_example.py data.csv
python examples/ops/stats_example.py data.csv
python examples/ops/schema_example.py data.csv
python examples/ops/transform_example.py data.csv
```

If no file is passed, scripts use a default path or create minimal in-memory data for demonstration.
