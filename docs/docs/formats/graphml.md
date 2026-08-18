---
title: GraphML Format
description: GraphML network graphs as node/edge records in IterableData
---

# GraphML Format

Read GraphML graphs as node records followed by edge records (via NetworkX).

## Overview

| Property | Value |
|----------|-------|
| Format id | `graphml` |
| Class | `GraphMLIterable` |
| Extensions | `.graphml` |
| Read | Yes |
| Write | No |
| Extra | `graph` (`networkx`) |
| Maturity | stable |

## Record shape

```python
{"_type": "node", "id": "n0"}
{"_type": "edge", "source": "n0", "target": "n1"}
```

Node/edge attributes from the file are merged into each record.

## Usage

```python
from iterable import open_iterable

with open_iterable("network.graphml") as source:
    for rec in source:
        print(rec["_type"], rec)
```

Install with `pip install iterabledata[graph]`.

## See also

- [GEXF](/formats/gexf) — GEXF graphs
- [DOT / Graphviz](/formats/gv) — DOT graphs
- [Supported formats](/formats/)
