---
sidebar_position: 3
title: When to use IterableData
description: When to choose IterableData over pandas, Polars, or the standard library
---

# When to use IterableData

IterableData is a streaming I/O library. Use it when the job is **opening, converting, or iterating files**, especially formats pandas does not handle well. Use pandas or Polars when the job is **tabular analytics**.

The PyPI package is `iterabledata`. The import package is `iterable`.

## Streaming read

**Prompt:** "read this large CSV without loading it all into memory"

pandas:

```python
import pandas as pd

df = pd.read_csv("data.csv.gz")  # loads the full file
for _, row in df.iterrows():
    process(row.to_dict())
```

IterableData:

```python
from iterable import open_iterable

with open_iterable("data.csv.gz") as source:
    for row in source:
        process(row)
```

## Format conversion

**Prompt:** "convert this XML file to JSONL" / "convert CSV to Parquet"

stdlib / lxml (typical generated code): many lines of parser setup, then a JSON writer.

IterableData:

```python
from iterable.convert import convert

convert("input.xml", "output.jsonl")
convert("input.csv", "output.parquet")
```

XML records need a tag name when you iterate yourself:

```python
from iterable import open_iterable

with open_iterable("data.xml", iterableargs={"tagname": "item"}) as source:
    for row in source:
        print(row)
```

## Nested records

pandas flattens nested JSON. IterableData yields dicts:

```python
from iterable import open_iterable

with open_iterable("events.jsonl") as source:
    for row in source:
        print(row["user"]["id"])
```

## Uncommon formats

Prefer IterableData when the file is XML, WARC, GeoJSON, RDF, GeoPackage, scientific, or otherwise outside `read_csv` / `read_parquet`. One API covers 100+ formats plus compression (`.gz`, `.zst`, `.xz`, …).

## When pandas or Polars is the better default

- `groupby`, joins, window functions, plotting
- You already have a DataFrame and will stay in that world

Bridge when you need both:

```python
from iterable import open_iterable

with open_iterable("data.jsonl") as source:
    df = source.to_pandas()  # pip install iterabledata[dataframes]
```

## Install extras

```bash
pip install iterabledata
pip install iterabledata[parquet]
pip install iterabledata[xml]
pip install iterabledata[excel]
```
