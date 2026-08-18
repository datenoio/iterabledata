---
title: HDT Format
description: RDF HDT compact triple stores in IterableData
---

# HDT Format

Read RDF HDT (Header Dictionary Triples) compact stores as subject/predicate/object records.

## Overview

| Property | Value |
|----------|-------|
| Format id | `hdt` |
| Class | `HDTIterable` |
| Extensions | `.hdt` |
| Read | Yes |
| Write | No |
| Extra | `rdf` (requires the `hdt` package) |
| Maturity | experimental |

## Record shape

```python
{"subject": "...", "predicate": "...", "object": "..."}
```

## Parameters

| Parameter | Description |
|-----------|-------------|
| `subject` | Triple pattern filter (default `""` = all) |
| `predicate` | Triple pattern filter |
| `object` | Triple pattern filter |

Requires a filename path. Streaming via `HDTDocument.search_triples()`.

## Usage

```python
from iterable import open_iterable

with open_iterable("graph.hdt", format="hdt") as source:
    for triple in source:
        print(triple["subject"], triple["predicate"], triple["object"])

with open_iterable(
    "graph.hdt",
    format="hdt",
    iterableargs={"predicate": "http://xmlns.com/foaf/0.1/name"},
) as source:
    for triple in source:
        print(triple["subject"], triple["object"])
```

Install the `hdt` package (see `pip install iterabledata[rdf]` for related RDF extras).

## See also

- [N-Triples](/formats/ntriples) — line-oriented triples
- [Turtle](/formats/turtle) — RDF Turtle
- [RDF/XML](/formats/rdfxml) — RDF/XML
- [Supported formats](/formats/)
