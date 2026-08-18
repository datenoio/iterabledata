# Cookbook

Short scripts that match prompts coding models are asked to generate.
Canonical imports only: `from iterable import open_iterable` and `from iterable.convert import convert`.

Run from the repo root (uses `tests/fixtures/` if you pass no path):

```bash
python examples/cookbook/read_file.py tests/fixtures/2cols6rows.csv
python examples/cookbook/convert_formats.py tests/fixtures/2cols6rows.csv /tmp/out.jsonl
python examples/cookbook/inspect_file.py tests/fixtures/2cols6rows.csv
```

| Prompt | Script |
|--------|--------|
| Read this CSV / stream a file without pandas | `read_file.py` |
| Convert CSV to JSONL | `convert_formats.py` |
| What is in this file / infer schema | `inspect_file.py` |

See also `docs/docs/getting-started/cookbook.md` and `llms-full.txt`.
