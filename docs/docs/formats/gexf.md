---
title: GEXF Format
description: GEXF network graphs in IterableData
---

# GEXF Format

## Description

GEXF (Graph Exchange XML Format) is an XML graph format popularized by Gephi for dynamic and attributed networks. IterableData reads GEXF via NetworkX and yields node records first, then edge records. It is **read-only** in this release.

## File Extensions

- `.gexf` — Graph Exchange XML Format

## Implementation Details

### Reading

- Parses with `networkx.read_gexf`
- Converts to node then edge dicts (same shape as GraphML)
- Node: `{"_type": "node", "id": "...", ...}`
- Edge: `{"_type": "edge", "source": "...", "target": "...", ...}`

### Writing

Writing is not supported.

### Key Features

- **Gephi-friendly**: common interchange for network tools
- **Attributed nodes/edges**: attributes appear on records
- **Shared record model** with GraphML and DOT

## Usage

```python
from iterable import open_iterable

with open_iterable("network.gexf") as source:
    for row in source:
        print(row["_type"], row)
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
4. Dynamic GEXF timelines may be simplified by the NetworkX reader

## Error Handling

- **ImportError**: missing `networkx` — install `iterabledata[graph]`
- **Parse / I/O errors**: invalid GEXF or missing files
- Format is registered **writable=False**

## Related Formats

- [GraphML](graphml.md) — GraphML
- [DOT / GV](gv.md) — GraphViz DOT
