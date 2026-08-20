---
title: GraphML Format
description: GraphML network graphs in IterableData
---

# GraphML Format

## Description

GraphML is an XML format for attributed graphs used in network analysis and visualization tools. IterableData reads GraphML via NetworkX and yields node records first, then edge records. It is **read-only** in this release.

## File Extensions

- `.graphml` — GraphML documents

## Implementation Details

### Reading

- Parses with `networkx.read_graphml`
- Converts the graph to a flat list: nodes then edges
- Node rows: `{"_type": "node", "id": "...", ...attributes}`
- Edge rows: `{"_type": "edge", "source": "...", "target": "...", ...attributes}`

### Writing

Writing is not supported.

### Key Features

- **Node + edge stream**: uniform dict records with `_type`
- **Attribute passthrough**: GraphML keys become record fields
- **NetworkX backed**

## Usage

```python
from iterable import open_iterable

with open_iterable("network.graphml") as source:
    for row in source:
        if row["_type"] == "node":
            print("node", row["id"])
        else:
            print("edge", row["source"], "->", row["target"])
```

## Parameters

No format-specific `iterableargs`.

## Installation

```bash
pip install 'iterabledata[graph]'
```

Requires `networkx`.

## Limitations

1. **Read-only**
2. **Memory**: entire graph loaded before iteration
3. **Requires networkx**
4. Hypergraphs / exotic GraphML extensions depend on NetworkX support

## Error Handling

- **ImportError**: missing `networkx` — install `iterabledata[graph]`
- **Parse / I/O errors**: invalid GraphML or missing files raise NetworkX or file exceptions
- Format is registered **writable=False**

## Related Formats

- [GEXF](gexf.md) — Graph Exchange XML Format
- [DOT / GV](gv.md) — GraphViz DOT
