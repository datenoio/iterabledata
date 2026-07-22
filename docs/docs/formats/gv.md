---
title: DOT / Graphviz Format
description: Graphviz DOT graphs as node/edge records in IterableData
---

# DOT / Graphviz Format

Read Graphviz DOT (`.gv` / `.dot`) graphs as node then edge records (via NetworkX / pydot).

## Overview

| Property | Value |
|----------|-------|
| Format id | `gv` (alias `dot`) |
| Class | `DOTIterable` |
| Extensions | `.gv`, `.dot` |
| Read | Yes |
| Write | No |
| Extra | `graph` (`networkx`) |
| Maturity | stable |

## Record shape

```python
{"_type": "node", "id": "A", "label": "start"}
{"_type": "edge", "source": "A", "target": "B"}
```

Requires NetworkX with pydot support for DOT parsing.

## Usage

```python
from iterable.helpers.detect import open_iterable

with open_iterable("graph.dot") as source:
    for rec in source:
        print(rec["_type"], rec)
```

Install with `pip install iterabledata[graph]`.

## See also

- [GEXF](/formats/gexf) — GEXF graphs
- [GraphML](/formats/graphml) — GraphML graphs
- [Supported formats](/formats/)
