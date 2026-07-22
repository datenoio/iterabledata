---
title: TriX Format
description: TriX RDF XML triples in IterableData
---

# TriX Format

Read TriX RDF/XML triples as subject/predicate/object records (via rdflib).

## Overview

| Property | Value |
|----------|-------|
| Format id | `trix` |
| Class | `TriXIterable` |
| Extensions | `.trix` |
| Read | Yes |
| Write | No |
| Extra | `rdf` (`rdflib`) |
| Maturity | stable |

## Record shape

```python
{"subject": "...", "predicate": "...", "object": "..."}
```

## Usage

```python
from iterable.helpers.detect import open_iterable

with open_iterable("graph.trix") as source:
    for triple in source:
        print(triple["subject"], triple["predicate"], triple["object"])
```

Install with `pip install iterabledata[rdf]`.

## See also

- [N3](/formats/n3) — Notation3 triples
- [TriG](/formats/trig) — named-graph quads
- [RDF/XML](/formats/rdfxml) — RDF/XML
- [Supported formats](/formats/)
