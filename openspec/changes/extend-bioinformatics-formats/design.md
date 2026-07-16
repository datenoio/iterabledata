## Context

CRAM shares alignment semantics with SAM/BAM but may require reference sequence access. BED and GFF/GTF are tabular-looking text formats with incompatible coordinate conventions, optional fields, directives, and structured attributes.

## Goals / Non-Goals

- Goals:
  - Stream large alignment and annotation files.
  - Preserve native coordinate conventions without silent conversion.
  - Reuse existing alignment records and compression handling.
  - Preserve enough header/directive metadata for correct round trips.
- Non-Goals:
  - Perform genomic liftover or coordinate normalization by default.
  - Build a full feature database or interval query engine.
  - Download reference genomes automatically.

## Decisions

### CRAM

`CRAMIterable` uses `pysam.AlignmentFile` and the same row mapping as SAM/BAM. `reference_filename` and supported pysam reference options are explicit `iterableargs`. Sequential reading does not require an index, but a missing required reference fails with a resource-specific error.

### BED

Rows expose canonical BED columns with exact names/documentation and retain additional columns in a deterministic field. Coordinates remain 0-based, half-open. BED3 through BED12 are accepted; internal consistency of block fields is validated.

### GFF3/GTF

Rows expose the nine canonical columns and parse attributes into an ordered mapping while retaining the original attribute text when lossless round trip is requested. Coordinates remain 1-based, closed. Directives/comments are stored as iterable metadata and may optionally be yielded as typed records.

### Compression and sources

Plain text streams and existing codecs compose normally. Filename/index/reference-only constraints are declared per format. No separate command-line interface is introduced.

## Risks / Trade-offs

- CRAM reference errors can be opaque in htslib. Mitigation: preflight configuration and wrap failures with reference guidance.
- Attribute serialization can reorder/escape values. Mitigation: parsed plus raw modes and golden round trips.
- Users may assume normalized coordinates. Mitigation: explicit fields/docs and no implicit conversion.

## Migration Plan

Implement CRAM by extending alignment helpers, then BED, then GFF3/GTF. Begin with sequential iteration and round trips; indexed region APIs remain future work.

## Open Questions

- Should directives/comments be metadata only by default or yielded as typed records?
- Is GTF a profile of the GFF implementation or a separate descriptor alias with stricter attribute rules?
