---
title: TriX Format
description: TriX XML RDF triples in IterableData
---

# TriX Format

## Description

TriX is an XML serialization for RDF graphs. IterableData parses TriX with `rdflib` and yields one triple record per statement (`subject`, `predicate`, `object`). It is **read-only** in this release.

## File Extensions

- `.trix` — TriX RDF/XML-style graphs

## Implementation Details

### Reading

- Loads an `rdflib.Graph` and parses with `format="trix"`
- Accepts filename or stream text
- Materializes all triples as string-valued dicts

### Writing

Writing is not supported. Use [Turtle](turtle.md) or [RDF/XML](rdfxml.md) when write support is needed.

### Key Features

- **XML RDF**: interoperates with TriX producers
- **Triple rows**: consistent SPO dict shape with N3/TriG (without graph)
- **rdflib backed**

## Usage

```python
from iterable import open_iterable

with open_iterable("data.trix") as source:
    for triple in source:
        print(triple["subject"], triple["predicate"], triple["object"])
```

## Parameters

No format-specific `iterableargs`.

## Installation

```bash
pip install 'iterabledata[rdf]'
```

Requires `rdflib`.

## Limitations

1. **Read-only**
2. **Memory**: full graph in memory
3. **Requires rdflib**
4. Named-graph structure in TriX is flattened to triples as exposed by rdflib’s Graph parse

## Error Handling

- **ImportError**: missing `rdflib` — install `iterabledata[rdf]`
- **Parse errors**: invalid TriX from rdflib
- **I/O errors**: missing or unreadable files
- Format is registered **writable=False**

## Related Formats

- [TriG](trig.md) — TriG quads
- [N3](n3.md) — Notation3
- [RDF/XML](rdfxml.md) — RDF/XML
- [Turtle](turtle.md) — Turtle
