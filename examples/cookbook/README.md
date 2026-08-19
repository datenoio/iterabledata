# Cookbook

Short scripts that match prompts coding models are asked to generate.
Canonical imports only: `from iterable import open_iterable` and `from iterable.convert import convert`.

Run from the repo root (uses `tests/fixtures/` if you pass no path):

```bash
python examples/cookbook/read_file.py tests/fixtures/2cols6rows.csv
python examples/cookbook/read_gzip.py tests/fixtures/2cols6rows_test.csv.gz
python examples/cookbook/read_jsonl.py tests/fixtures/2cols6rows_test.jsonl
python examples/cookbook/read_bulk.py tests/fixtures/2cols6rows.csv
python examples/cookbook/read_xml.py tests/fixtures/books.xml book
python examples/cookbook/write_jsonl.py /tmp/out.jsonl
python examples/cookbook/write_csv.py /tmp/out.csv
python examples/cookbook/convert_formats.py tests/fixtures/2cols6rows.csv /tmp/out.jsonl
python examples/cookbook/filter_rows.py tests/fixtures/2cols6rows.csv name Mary
python examples/cookbook/count_rows.py tests/fixtures/2cols6rows.csv
python examples/cookbook/inspect_file.py tests/fixtures/2cols6rows.csv
python examples/cookbook/stats_file.py tests/fixtures/2cols6rows.csv
python examples/cookbook/infer_schema.py tests/fixtures/2cols6rows.csv
python examples/cookbook/sample_file.py tests/fixtures/2cols6rows.csv
python examples/cookbook/describe_format.py csv
```

| Prompt | Script |
|--------|--------|
| Read this CSV / stream a file without pandas | `read_file.py` |
| Read a gzip CSV | `read_gzip.py` |
| Read a JSONL file | `read_jsonl.py` |
| Read a file in batches / chunks | `read_bulk.py` |
| Parse XML as records | `read_xml.py` |
| Write records to JSONL | `write_jsonl.py` |
| Write records to CSV | `write_csv.py` |
| Convert CSV to JSONL | `convert_formats.py` |
| Filter rows by a field value | `filter_rows.py` |
| Count rows in a file | `count_rows.py` |
| What is in this file / infer schema | `inspect_file.py` |
| Compute stats on a file | `stats_file.py` |
| Infer schema via agent tools | `infer_schema.py` |
| Sample rows / detect format | `sample_file.py` |
| Describe a format in the catalog | `describe_format.py` |

See also `docs/docs/getting-started/cookbook.md` and `llms-full.txt`.
