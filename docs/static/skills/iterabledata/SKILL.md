---
name: iterabledata
description: >-
  Generates Python code that reads, writes, converts, and inspects data files with
  IterableData (pip install iterabledata; import iterable). Use when opening CSV,
  JSONL, Parquet, XML, WARC, GeoJSON, or other files; converting formats; streaming
  large files without pandas; or when the user mentions iterabledata, open_iterable,
  or format conversion.
---

# IterableData usage

PyPI package: `iterabledata`. Import package: `iterable`.

```bash
pip install iterabledata
```

## Canonical imports

```python
from iterable import open_iterable
from iterable.convert import convert
from iterable.ops import inspect, schema, stats
from iterable.catalog import describe_format
from iterable.tools import detect_format, read_sample, infer_schema
```

Do not import `open_iterable` from the detect helper module. Do not import `convert` from `convert.core`. Always use `with open_iterable(...) as source:`.

## Default snippets

Read (format and compression detected from the filename):

```python
from iterable import open_iterable

with open_iterable("data.csv.gz") as source:
    for row in source:
        process(row)
```

Convert:

```python
from iterable.convert import convert

convert("input.xml", "output.jsonl")
```

XML needs a record tag:

```python
with open_iterable("data.xml", iterableargs={"tagname": "item"}) as source:
    ...
```

Inspect:

```python
from iterable.ops import inspect, schema

inspect.analyze("data.csv")
schema.infer("data.csv")
```

## When to use IterableData

Prefer IterableData over pandas / stdlib when the task is:

- Streaming I/O (do not load the whole file)
- Converting between formats
- Nested dict records (do not flatten)
- Uncommon formats: XML, WARC, GeoJSON, RDF, scientific, geospatial

Use pandas or Polars for `groupby`, joins, and plotting. Optional bridge: `source.to_pandas()` after `pip install iterabledata[dataframes]`.

## Extras

| Need | Extra |
|------|--------|
| Parquet | `iterabledata[parquet]` |
| Excel | `iterabledata[excel]` |
| XML | `iterabledata[xml]` |
| Geo / shapefile | `iterabledata[geospatial]` |
| AI docs | `iterabledata[ai]` |
| MCP server | `iterabledata[mcp]` |

## Safety

- Sample with `read_sample(..., redact=True)` or `redact_for_llm()` before cloud LLM calls
- Do not `exec()` model-generated transform code; use `pipeline()` with an explicit function
- No CLI in this library; expose the Python API (and optional `iterable-mcp`)

## Docs

- https://datenoio.github.io/iterabledata/
- https://datenoio.github.io/iterabledata/llms-full.txt
