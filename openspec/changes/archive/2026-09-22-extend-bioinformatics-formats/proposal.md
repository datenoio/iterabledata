# Change: Extend Bioinformatics Support with CRAM, BED, and GFF

## Why

Existing SAM/BAM and genomic VCF/BCF support leaves common alignment and annotation workflows incomplete. CRAM is the natural compressed alignment extension, while BED and GFF3/GTF are ubiquitous streaming interval/annotation formats. Their coordinate systems and header semantics must be explicit to avoid silent scientific errors.

## What Changes

- Add sequential CRAM reading through `pysam`, using the existing SAM/BAM alignment record shape.
- Support optional reference configuration and clear failures when a CRAM requires an unavailable reference.
- Add streaming BED3–BED12+ read/write support with 0-based half-open coordinates preserved.
- Add streaming GFF3 and GTF read/write support with 1-based closed coordinates, directives, comments, and parsed attributes.
- Add descriptors, compression composition, optional extras, fixtures, conformance, malformed-input, and memory tests.

## Dependencies

- Archive `add-genomic-vcf-format` before implementation where shared bio dependency metadata is involved.
- Coordinate capability/source metadata with `unify-format-capability-metadata`.

## Impact

- Affected specs: `alignment-formats`, `genomic-interval-formats`
- Affected code: alignment helpers, new BED/GFF datatypes, detection/registry, optional dependency metadata, docs/tests
- Dependencies: reuse optional `pysam`; GFF/BED core parsing should remain lightweight
