# Change: Add fst, RDF HDT, and IATI Formats

## Why

Three niche but high-confidence structured gaps remain from the Dateno stats review: R `fst` columnar frames, RDF HDT compact triple stores, and IATI aid-transparency XML activities. Volumes are smaller than GIS gaps, but each has a clear row/triple/activity iteration model and complements existing R data (`rdata`/`rds`) and RDF (Turtle/N-Triples/RDF/XML) support.

## What Changes

- Add read support for R `fst` files as dict-row iterables (columnar scan friendly).
- Add read support for RDF HDT files as iterable triples/quads aligned with existing RDF record shapes.
- Add read support for IATI activity XML as iterable activity (or transaction) records.
- Register formats, optional deps, fixtures, tests, and docs.

## Impact

- Affected specs: `fst-format` (new), `rdf-formats`, `iati-format` (new)
- Affected code: new datatypes, registry/detection, optional extras, docs/tests
- New dependencies: optional `fst`/HDT/IATI libraries or lightweight XML parsing for IATI
