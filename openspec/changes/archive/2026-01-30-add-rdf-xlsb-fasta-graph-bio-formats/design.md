# Design: Add RDF, XLSB, FASTA, FASTQ, Graph, and Alignment Formats

## Context
IterableData exposes a row-based iterator API over many formats. This change adds five format families: (1) RDF formats TriG, N3, TriX via rdflib; (2) Excel Binary XLSB via pyxlsb; (3) FASTA and FASTQ (sequence formats); (4) GraphML, GEXF, DOT via NetworkX; (5) BAM and SAM via pysam. Each family has different semantics (RDF quads/triples, spreadsheet rows, sequences, graph nodes/edges, alignment records). The goal is to map each into the existing iterable-of-dicts model where sensible and to keep optional dependencies isolated.

## Goals / Non-Goals
- **Goals**: Support read (and write where practical) for the listed formats; automatic format detection by extension and content where possible; clear errors when optional deps are missing.
- **Non-Goals**: Full RDF reasoning, full Excel formula evaluation, graph algorithms beyond I/O, or alignment calling/analysis; those remain in domain libraries.

## Decisions

### RDF (TriG, N3, TriX)
- **Decision**: Use rdflib for parse/serialize. Expose rows as triples or quads (subject, predicate, object, optional graph). One iterable implementation per format (or one RDF iterable parameterized by format) in `iterable/datatypes/`, with format keyed by extension (`.trig`, `.n3`, `.trix`).
- **Alternatives**: Custom parsers — rejected to avoid duplication and to leverage rdflib’s correctness and maintenance.

### XLSB
- **Decision**: Use pyxlsb for reading. Map sheets to tables; each row yields a dict (column name or index → value). Write support optional in initial scope.
- **Alternatives**: openpyxl/xlrd — they do not support XLSB natively; pyxlsb is the standard choice for XLSB.

### FASTA / FASTQ
- **Decision**: Implement with stdlib-only parsers (no required new dependency). Yield dicts with keys such as `id`, `description`, `sequence` (FASTA) and `id`, `sequence`, `quality`, optional `description` (FASTQ). Support streaming reads.
- **Alternatives**: BioPython — could add as optional for richer metadata; not required for basic sequence iteration.

### Graph (GraphML, GEXF, DOT)
- **Decision**: Use NetworkX to read/write these formats. Expose as iterables of node records and/or edge records (e.g., two iterables or a single iterable of “element” dicts with a type field). Format detection by extension (`.graphml`, `.gexf`, `.dot`/`.gv`).
- **Alternatives**: Custom parsers — NetworkX is widely used and maintains parsers for these formats; reusing it keeps behavior consistent with the ecosystem.

### BAM / SAM
- **Decision**: Use pysam for reading (and optionally writing). Yield alignment records as dict-like rows (e.g., fields from pysam’s AlignedSegment). SAM is text; BAM is binary; both handled via pysam. Optional dependency `pysam`.
- **Alternatives**: Custom SAM parser — possible for SAM only but BAM requires binary decoding; pysam is the standard and handles both.

### Optional Dependencies
- **Decision**: Add extras in `pyproject.toml`: e.g. `rdf` (rdflib), `xlsb` (pyxlsb), `graph` (networkx), `bio` or `alignment` (pysam). FASTA/FASTQ can be in `bio` or a separate extra if we later add BioPython. Lazy import in datatype modules; raise clear ImportError with install hint when extra is missing.

## Risks / Trade-offs
- **Many optional deps**: More extras and import paths — mitigated by documenting extras and keeping each format’s import behind try/except.
- **Semantic fit**: RDF quads and graph edges are not “rows” in the same sense as CSV — we accept a best-effort mapping (e.g., one quad/edge per row) and document it.
- **Performance**: rdflib/NetworkX/pysam have their own performance characteristics; we document streaming where supported and do not promise same throughput as CSV.

## Migration Plan
- No breaking changes. New formats are additive. Existing callers unaffected. After merge, document new extras and format names in README and format docs.

## Open Questions
- Whether to expose FASTA/FASTQ under a single “bio” extra or keep them dependency-free and only add a “bio” extra when/if BioPython is introduced.
- Whether graph support should expose one iterable (nodes then edges) or two (e.g., `read_nodes()` and `read_edges()`); design can be refined in implementation to match BaseIterable patterns used elsewhere.
