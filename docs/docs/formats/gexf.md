---
title: GEXF Format
description: GEXF network graphs as node/edge records in IterableData
---

# GEXF Format

Read GEXF graphs as node records followed by edge records (via NetworkX).

## Overview

| Property | Value |
|----------|-------|
| Format id | `gexf` |
| Class | `GEXFIterable` |
| Extensions | `.gexf` |
| Read | Yes |
| Write | No |
| Extra | `graph` (`networkx`) |
| Maturity | stable |

## Record shape

```python
{"_type": "node", "id": "n0", "label": "A"}
{"_type": "edge", "source": "n0", "target": "n1", "weight": 1.0}
```

Node/edge attributes from the file are merged into each record.

## Usage

```python
from iterable import open_iterable

with open_iterable("network.gexf") as source:
    for rec in source:
        print(rec["_type"], rec)
```

Install with `pip install iterabledata[graph]`.

## See also

- [GraphML](/formats/graphml) — GraphML graphs
- [DOT / Graphviz](/formats/gv) — DOT graphs
- [Supported formats](/formats/)
