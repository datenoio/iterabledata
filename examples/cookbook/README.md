# Cookbook

Short scripts that match prompts coding models are asked to generate.
Canonical imports only: `from iterable import open_iterable` and `from iterable.convert import convert`.

Run from the repo root (uses `tests/fixtures/` if you pass no path):

```bash
python examples/cookbook/read_file.py tests/fixtures/2cols6rows.csv
python examples/cookbook/read_gzip.py tests/fixtures/2cols6rows_test.csv.gz
python examples/cookbook/write_jsonl.py /tmp/out.jsonl
python examples/cookbook/convert_formats.py tests/fixtures/2cols6rows.csv /tmp/out.jsonl
python examples/cookbook/inspect_file.py tests/fixtures/2cols6rows.csv
python examples/cookbook/sample_file.py tests/fixtures/2cols6rows.csv
```

| Prompt | Script |
|--------|--------|
| Read this CSV / stream a file without pandas | `read_file.py` |
| Read a gzip CSV | `read_gzip.py` |
| Write records to JSONL | `write_jsonl.py` |
| Convert CSV to JSONL | `convert_formats.py` |
| What is in this file / infer schema | `inspect_file.py` |
| Sample rows / detect format | `sample_file.py` |

See also `docs/docs/getting-started/cookbook.md` and `llms-full.txt`.
