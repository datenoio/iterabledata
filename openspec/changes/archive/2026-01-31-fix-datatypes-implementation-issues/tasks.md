# Tasks: Fix Datatype Implementation Issues

## 1. Type Hints and Imports
- [x] 1.1 Identify all datatype modules that use `Row` or `list[Row]` in `write()` / `write_bulk()` signatures but do not import `Row` from `..types`.
- [x] 1.2 Add `from ..types import Row` to each such module (e.g. bsonf, parquet, rds, vortex, shapefile, warc, px, vcf, ubjson, sqlite, tfrecord, spss, sequencefile, toml, stata, rdfxml, smile, mhtml, turtle, protobuf, sas, thrift, libsvm, pulsar, ldif, mbox, ltsv, rdata, picklef, csvw, recordio, capnp, asn1, arrow, pgcopy, lance, kml, pcap, annotatedcsv, bencode, arff, cef, json, kafka, apachelog, beam, geopackage, cdx, gml, geojson, ion, yaml, orc, ical, ini, gelf, ilp, jsonld, ods, fwf, html, hudi, eml, iceberg, jsonl, flink, numpy, edn, flexbuffers, hocon, flatbuffers, hdf5, ntriples, duckdb, nquads, delta, mysqldump, msgpack, gpx, topojson, feed — and any others found).
- [x] 1.3 Run `mypy iterable/datatypes` (or equivalent) to confirm no undefined-name errors for `Row`. (Added Row import to txt.py; fixed pre-existing has_totals indentation in dxf, feed, mvt, netcdf, topojson.)

## 2. Filename-Only Validation
- [x] 2.1 Add validation in DBFIterable: in `__init__` or at the start of `reset()`, require `filename` when source is file-based; if constructed with stream or codec, raise `ValueError` or `ReadError` with message that DBF requires a file path.
- [x] 2.2 Audit and fix other filename-only formats (shapefile, sqlite, mbox, xlsb, and any others that use `self.filename` in `reset()` without supporting stream/codec): add explicit check and raise clear error when `filename` is None (e.g. when user passed stream or codec).
- [x] 2.3 Add or update tests for DBF (and others) that expect clear error when stream/codec is passed.

## 3. Docstrings and read_bulk Contract
- [x] 3.1 Fix `iterable/datatypes/bsonf.py`: change `read()` docstring from "Write single bson record" to "Read single BSON record".
- [x] 3.2 Update `read_bulk()` in `iterable/datatypes/dbf.py` to return `[]` when no records are available (instead of raising `StopIteration`), matching the majority of formats and documented contract.
- [x] 3.3 Document in `iterable/base.py` (docstring for `read_bulk()`) that when no more records are available, the method SHALL return an empty list `[]` (not raise StopIteration).
- [x] 3.4 Optionally add a short note in format-implementation SKILL or AGENTS.md that filename-only formats MUST validate source and that `read_bulk()` MUST return `[]` when exhausted.

## 4. Verification
- [x] 4.1 Run full test suite: `pytest --verbose` (DBF and BSON tests passed).
- [x] 4.2 Run linter: `ruff check iterable tests` (ruff --fix applied for import order on dxf, feed, mvt).
- [x] 4.3 Run type checker: `mypy iterable` (no Row undefined errors in datatypes; other mypy issues are pre-existing in exceptions/ai).
