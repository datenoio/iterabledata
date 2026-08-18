---
sidebar_position: 2
title: Quick Start
description: Get started with Iterable Data in minutes
---

# Quick Start

Install the **iterabledata** package, then import **iterable**. One function opens CSV, JSONL, Parquet, XML, and 100+ other formats (compression included).

```bash
pip install iterabledata
```

```python
from iterable import open_iterable

with open_iterable("data.csv.gz") as source:
    for row in source:
        print(row)
```

`open_iterable()` detects format and compression from the filename (and falls back to content when needed).

## Write a file

```python
from iterable import open_iterable

with open_iterable("output.jsonl.zst", mode="w") as dest:
    for item in rows:
        dest.write(item)
```

Always use a `with` statement so files and codecs close automatically.

## Convert formats

```python
from iterable.convert import convert

convert("input.jsonl.gz", "output.parquet")
```

## Common formats

```python
from iterable import open_iterable

with open_iterable("data.jsonl") as source:
    for row in source:
        print(row)

with open_iterable("data.parquet") as source:
    for row in source:
        print(row)

with open_iterable("data.xml", iterableargs={"tagname": "item"}) as source:
    for row in source:
        print(row)

with open_iterable("data.xlsx") as source:
    for row in source:
        print(row)
```

XML needs a record tag name via `iterableargs={"tagname": "..."}`. Some formats need extras, for example `pip install iterabledata[parquet]` or `iterabledata[excel]`.

## Inspect an unknown file

```python
from iterable.ops import inspect, schema

print(inspect.analyze("data.csv"))
print(schema.infer("data.csv"))
```

## What's Next?

- [When to use IterableData](/getting-started/when-to-use) — vs pandas and the standard library
- [Cookbook](/getting-started/cookbook) — prompt-shaped recipes
- [Basic Usage](/getting-started/basic-usage) — compression, encoding, pipelines
- [API Reference](/api/open-iterable) — `open_iterable()` details
