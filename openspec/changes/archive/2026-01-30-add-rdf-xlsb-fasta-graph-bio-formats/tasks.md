## 1. Dependencies and project config
- [x] 1.1 Add optional dependency groups in `pyproject.toml`: `rdf` (rdflib), `xlsb` (pyxlsb), `graph` (networkx), `alignment` or `bio` (pysam). Include FASTA/FASTQ in docs; add a `bio` extra if grouping with pysam.
- [x] 1.2 Add new extras to the `all` group in `pyproject.toml` if the project maintains an aggregate extra.

## 2. RDF formats (TriG, N3, TriX)
- [x] 2.1 Implement RDF iterable(s) in `iterable/datatypes/` using rdflib (e.g. `trig.py`, `n3.py`, `trix.py` or one module parameterized by format).
- [x] 2.2 Register `.trig`, `.n3`, `.trix` (and any standard aliases) in `iterable/helpers/detect.py` and DATATYPE_REGISTRY.
- [x] 2.3 Add content-based or extension-based detection for RDF formats in `detect_file_type` if applicable.
- [x] 2.4 Add tests in `tests/test_trig.py`, `tests/test_n3.py`, `tests/test_trix.py` (or a single `test_rdf_formats.py`) covering read, optional write, and missing dependency.

## 3. XLSB format
- [x] 3.1 Implement `XLSBIterable` in `iterable/datatypes/xlsb.py` using pyxlsb.
- [x] 3.2 Register `.xlsb` in `iterable/helpers/detect.py` and DATATYPE_REGISTRY.
- [x] 3.3 Add tests in `tests/test_xlsb.py` for read and missing dependency.

## 4. FASTA format
- [x] 4.1 Implement `FASTAIterable` in `iterable/datatypes/fasta.py` (stdlib-only or minimal deps).
- [x] 4.2 Register `.fa`, `.fasta`, `.fna`, `.faa`, etc. in `iterable/helpers/detect.py` and DATATYPE_REGISTRY.
- [x] 4.3 Add tests in `tests/test_fasta.py` for read, streaming, and edge cases.

## 5. FASTQ format
- [x] 5.1 Implement `FASTQIterable` in `iterable/datatypes/fastq.py` (stdlib-only or minimal deps).
- [x] 5.2 Register `.fq`, `.fastq` in `iterable/helpers/detect.py` and DATATYPE_REGISTRY.
- [x] 5.3 Add tests in `tests/test_fastq.py` for read, streaming, and edge cases.

## 6. Graph formats (GraphML, GEXF, DOT)
- [x] 6.1 Implement graph iterables in `iterable/datatypes/` using NetworkX (e.g. `graphml.py`, `gexf.py`, `dot.py` or a shared graph module).
- [x] 6.2 Register `.graphml`, `.gexf`, `.dot`, `.gv` in `iterable/helpers/detect.py` and DATATYPE_REGISTRY.
- [x] 6.3 Add tests in `tests/test_graphml.py`, `tests/test_gexf.py`, `tests/test_dot.py` (or `tests/test_graph_formats.py`) for read, optional write, and missing dependency.

## 7. BAM and SAM formats
- [x] 7.1 Implement BAM/SAM iterable(s) in `iterable/datatypes/` using pysam (e.g. `bam.py`, `sam.py` or `alignment.py`).
- [x] 7.2 Register `.bam`, `.sam` in `iterable/helpers/detect.py` and DATATYPE_REGISTRY.
- [x] 7.3 Add tests in `tests/test_bam.py`, `tests/test_sam.py` (or `tests/test_alignment.py`) for read and missing dependency.

## 8. Documentation and capability registry
- [x] 8.1 Update README or format docs to list new formats and optional extras.
- [x] 8.2 Ensure new formats are exposed via format capability APIs if the project has a capability registry (e.g. `get_format_capabilities`).
