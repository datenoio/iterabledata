---
title: TriG Format
description: TriG RDF named-graph quads in IterableData
---

# TriG Format

Read TriG RDF as subject/predicate/object/graph quads (via rdflib).

## Overview

| Property | Value |
|----------|-------|
| Format id | `trig` |
| Class | `TriGIterable` |
| Extensions | `.trig` |
| Read | Yes |
| Write | No |
| Extra | `rdf` (`rdflib`) |
| Maturity | stable |

## Record shape

```python
{"subject": "...", "predicate": "...", "object": "...", "graph": "..."}
```

## Usage

```python
from iterable import open_iterable

with open_iterable("graph.trig") as source:
    for quad in source:
        print(quad["graph"], quad["subject"], quad["predicate"], quad["object"])
```

Install with `pip install iterabledata[rdf]`.

## See also

- [N3](/formats/n3) — Notation3 triples
- [TriX](/formats/trix) — TriX XML triples
- [N-Quads](/formats/nquads) — line-oriented quads
- [Supported formats](/formats/)
