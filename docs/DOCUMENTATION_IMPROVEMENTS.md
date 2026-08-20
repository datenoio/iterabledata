# Documentation status

This file tracks documentation backlog for the Docusaurus site under `docs/docs/`.

## Done

- Context managers are the primary example style on format pages. A few pages
  still show `close()` under an "Alternative: Manual close" heading.
- Format index and sidebar include HTML, TAR, ZIPXML, GeoJSONSeq, GeoParquet,
  FlatGeobuf, Zarr, OTLP, genomic VCF, and CRAM/BED/GFF3/GTF.
- Stub pages for Zarr, GeoParquet, FlatGeobuf, OTLP, and genomic intervals were
  expanded to the format template (Usage, Parameters, extras).
- API pages for async, codecs, cloud storage, database engines, DataFrame
  bridges, native batches, observability, and plugins are in the sidebar and
  homepage contents.
- Read/write flags: XLSX and ODS are read-only; SQLite is writable. The XLSX
  and ODS pages no longer document writers.
- `DOC_FILENAMES` maps OTLP, CRAM/BED/GFF3/GTF, FlatGeobuf, Paimon row/mosaic,
  and common aliases to real pages.
- Codecs page is a catalog (including `.7z`), not only compression profiles.
- Installation documents extras by area, not five sample extras.
- Development sidebar has contributing and adding-formats.
- Leftover template alias pages (`dta.md`, `htm.md`, …) redirect to the
  canonical format page.
- Write flags, extras, and API signatures aligned with the code (Avro/WARC/MBOX
  and other implemented writers; Kafka/Pulsar described as on-disk dumps;
  troubleshooting frontmatter restored).
- Registry stub format pages (KMZ, GPX, MVT, DXF, RDF TriG/N3/TriX, GraphML/GEXF/DOT,
  BAM/SAM, FASTA/FASTQ, FileGDB, miniSEED, EDI, ASCII Grid) expanded to the full
  template with Parameters and Error Handling.
- Thin pages (CDF, PCAP, NetCDF, FlatGeobuf, genomic VCF, TopoJSON, XLSB, LIBSVM,
  NumPy, RSS/Atom, ARFF, genomic intervals, Kafka, Pulsar, BAG, MIF, GRIB2) given
  Parameters and Error Handling.
- Every content format page now has `## Parameters` and `## Error Handling`
  (or Troubleshooting).
- `adding-formats.md` includes a worked in-tree example and points at plugins.
- `frameworks.md` summarizes in-docs vs GitHub guides; `plugins.md` has a
  reference plugin package walkthrough.

## Still incremental

- Some parameter tables remain constructor-derived one-liners; expand narrative
  when you next edit that format.
- Framework provider guides (`docs/integrations/*.md`) remain GitHub-canonical;
  the published site links and summarizes them from `frameworks.md`.
- A real published reference plugin package on PyPI is still a product goal
  (IMPROVEMENT_PLAN 6.5); docs now describe the layout.
