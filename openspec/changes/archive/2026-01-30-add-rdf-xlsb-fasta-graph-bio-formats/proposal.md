# Change: Add TriG, N3, TriX, XLSB, FASTA, FASTQ, GraphML, GEXF, DOT, BAM, and SAM Format Support

## Why
Users need to process additional data formats commonly used in semantic web (RDF), spreadsheets (binary Excel), bioinformatics (FASTA/FASTQ, BAM/SAM), and graph analytics (GraphML, GEXF, DOT). IterableData already supports Turtle, N-Quads, N-Triples, and RDF/XML; adding TriG, N3, and TriX via rdflib completes the RDF suite. XLSB support via pyxlsb enables reading binary Excel workbooks. FASTA and FASTQ are simple, widely used sequence formats. GraphML, GEXF, and DOT via NetworkX cover common graph interchange formats. BAM/SAM via pysam supports alignment data in bioinformatics pipelines. These additions extend the library's usefulness without changing existing behavior.

## What Changes
- Add TriG, N3, and TriX format support using rdflib (optional dependency).
- Add XLSB format support using pyxlsb (optional dependency).
- Add FASTA and FASTQ format support (simple parsers; no new dependency for core parsing, or minimal stdlib-only).
- Add GraphML, GEXF, and DOT format support using NetworkX (optional dependency).
- Add BAM and SAM format support using pysam (optional dependency).
- Register all new formats in `iterable/helpers/detect.py` and extend `detect_file_type` for appropriate extensions and content detection.
- Add optional dependency groups in `pyproject.toml` for rdflib, pyxlsb, networkx, and pysam.
- Add iterable classes in `iterable/datatypes/` and tests in `tests/` for each format or format group.

## Impact
- **New capabilities**: rdf-formats (TriG, N3, TriX), xlsb-format, fasta-format, fastq-format, graph-formats (GraphML, GEXF, DOT), alignment-formats (BAM, SAM).
- **Affected specs**: New spec deltas under `specs/rdf-formats`, `specs/xlsb-format`, `specs/fasta-format`, `specs/fastq-format`, `specs/graph-formats`, `specs/alignment-formats`.
- **Affected code**:
  - `pyproject.toml` (optional dependencies)
  - `iterable/helpers/detect.py` (format detection and DATATYPE_REGISTRY)
  - `iterable/datatypes/` (new or extended modules: trig/n3/trix, xlsb, fasta, fastq, graphml/gexf/dot, bam/sam)
  - `tests/test_*.py` (new tests)
  - Documentation (README, format docs as needed)
