## 1. Setup

- [x] 1.1 Add descriptors for `fst`, `hdt`, and `iati`.
- [x] 1.2 Add optional extras / reuse XML extra for IATI.
- [x] 1.3 Document record shapes for rows, triples, and activities.

## 2. Implementations

- [x] 2.1 Implement fst row iterable (read-only v1).
- [x] 2.2 Implement HDT triple iterable aligned with RDF record conventions.
- [x] 2.3 Implement IATI activity iterable with streaming XML parsing.

## 3. Tests and docs

- [x] 3.1 Add fixtures for fst, HDT, and IATI.
- [x] 3.2 Add detection, malformed, optional-dependency, and streaming tests.
- [x] 3.3 Document formats, limitations, and examples.
- [x] 3.4 Run `openspec validate add-fst-hdt-iati-formats --strict`.
