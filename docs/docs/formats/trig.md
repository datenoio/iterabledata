---
title: TriG Format
description: RDF TriG quads in IterableData
---

# TriG Format

## Description

TriG is a text serialization of RDF datasets that extends Turtle with named graphs. IterableData parses TriG with `rdflib` and yields one record per quad (`subject`, `predicate`, `object`, `graph`). It is **read-only** in this release.

## File Extensions

- `.trig` — TriG RDF datasets

## Implementation Details

### Reading

- Loads a `ConjunctiveGraph` via `rdflib`
- Parses from filename or stream text (`format="trig"`)
- Materializes all quads as string-valued dicts
- Flat records: one row per quad

### Writing

Writing is not supported. Use [Turtle](turtle.md) when you need writable RDF in IterableData.

### Key Features

- **Quad model**: includes graph/context URI
- **rdflib backed**: standard RDF term stringification
- **Text format**: works with codecs on compressed `.trig.*` files

## Usage

```python
from iterable import open_iterable

with open_iterable("data.trig") as source:
    for quad in source:
        print(quad["graph"], quad["subject"], quad["predicate"], quad["object"])
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
2. **Memory**: entire graph loaded before iteration
3. **Requires rdflib**
4. Terms are stringified; typed literals / language tags are not structured fields

## Error Handling

- **ImportError**: missing `rdflib` — install `iterabledata[rdf]`
- **Write / parse failures**: invalid TriG raises rdflib parse errors; write pipelines should treat the format as read-only
- **I/O errors**: missing or unreadable files

## Related Formats

- [N3](n3.md) — Notation3
- [TriX](trix.md) — XML RDF triples
- [Turtle](turtle.md) — Turtle triples (read/write)
- [N-Quads](nquads.md) — line-oriented quads
