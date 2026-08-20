# Documentation status

This file used to be a backlog. The items below were addressed in the docs
pass that aligned published Docusaurus pages with the format registry.

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

## Still incremental

- Error handling and troubleshooting sections are not uniform on every format
  page. Follow `docs/FORMAT_PAGE_TEMPLATE.md` when touching a page.
- Some parameter tables are constructor-derived one-liners; expand them when
  you next edit that format.
- Framework guides (`docs/integrations/*.md`) remain GitHub-canonical; the
  published site links them from `docs/docs/integrations/frameworks.md`.
