---
title: DOT / GV Format
description: GraphViz DOT graphs in IterableData
---

# DOT / GV Format

## Description

DOT is the GraphViz textual language for describing directed and undirected graphs. IterableData reads `.gv` / `.dot` via NetworkX’s pydot bridge and yields node records then edge records. Registry id is `gv` (alias `dot`). It is **read-only** in this release.

## File Extensions

- `.gv` — GraphViz DOT (primary registry id `gv`)
- `.dot` — common DOT alias

## Implementation Details

### Reading

- Parses with `networkx.nx_pydot.read_dot`
- Converts to node then edge dicts
- Node: `{"_type": "node", "id": "...", ...}`
- Edge: `{"_type": "edge", "source": "...", "target": "...", ...}`

### Writing

Writing is not supported.

### Key Features

- **GraphViz text**: works with `.gv` / `.dot` sources
- **Shared graph row model** with GraphML and GEXF
- **Attribute passthrough** from DOT attributes

## Usage

```python
from iterable import open_iterable

with open_iterable("graph.gv") as source:
    for row in source:
        print(row["_type"], row)
```

## Parameters

No format-specific `iterableargs`.

## Installation

```bash
pip install 'iterabledata[graph]'
```

Requires `networkx`. DOT parsing also typically needs a `pydot` (or compatible) backend available to NetworkX.

## Limitations

1. **Read-only**
2. **Memory**: entire graph loaded before iteration
3. **Requires networkx** (+ pydot-compatible backend for `nx_pydot`)
4. Complex GraphViz layout attributes are stored as data, not rendered

## Error Handling

- **ImportError**: missing `networkx` — install `iterabledata[graph]`
- **Parse / I/O errors**: invalid DOT, missing pydot backend, or unreadable files
- Format is registered **writable=False**

## Related Formats

- [GraphML](graphml.md) — GraphML
- [GEXF](gexf.md) — GEXF
