---
sidebar_position: 4
title: Cookbook
description: Prompt-shaped IterableData recipes for coding models and copy-paste
---

# Cookbook

Each recipe matches a prompt coding models are often asked. Install `iterabledata`, import `iterable`. Full runnable scripts live in [`examples/cookbook/`](https://github.com/datenoio/iterabledata/tree/main/examples/cookbook). Machine-readable copy: [llms-full.txt](/llms-full.txt).

## Read a file

**Prompt:** "read this CSV" / "stream a gzip file without pandas"

```python
from iterable import open_iterable

with open_iterable("data.csv.gz") as source:
    for row in source:
        print(row)
```

## Write JSONL

**Prompt:** "write these records to jsonl"

```python
from iterable import open_iterable

with open_iterable("output.jsonl", mode="w") as dest:
    for row in rows:
        dest.write(row)
```

## Convert formats

**Prompt:** "convert CSV to parquet" / "convert XML to JSONL"

```python
from iterable.convert import convert

convert("input.csv", "output.parquet")
convert("input.xml", "output.jsonl")
```

## Open XML

**Prompt:** "parse this XML file as records"

```python
from iterable import open_iterable

with open_iterable("data.xml", iterableargs={"tagname": "item"}) as source:
    for row in source:
        print(row)
```

Use `pip install iterabledata[xml]`. Replace `item` with the repeating element name.

## Inspect an unknown file

**Prompt:** "what is in this file" / "infer the schema"

```python
from iterable.ops import inspect, schema

print(inspect.analyze("data.csv"))
print(schema.infer("data.csv"))
```

Agent tools (JSON envelopes):

```python
from iterable.tools import detect_format, read_sample, infer_schema

detect_format("data.csv")
read_sample("data.csv", n=5, redact=True)
infer_schema("data.csv")
```

## Portable skill

Copy [`skills/iterabledata/SKILL.md`](https://github.com/datenoio/iterabledata/blob/main/skills/iterabledata/SKILL.md) into another repository so coding agents generate these imports by default.

## Related

- [When to use IterableData](/getting-started/when-to-use)
- [Quick Start](/getting-started/quick-start)
- [Building AI agents](/integrations/BUILDING_AGENTS)
