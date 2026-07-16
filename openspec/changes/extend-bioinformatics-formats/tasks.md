## 1. Shared bio infrastructure

- [x] 1.1 Define shared alignment row mapping and reference/resource errors for CRAM.
- [x] 1.2 Define coordinate-convention metadata and exact BED/GFF row schemas.
- [x] 1.3 Add/verify optional bio/alignment extras and complete descriptors.

## 2. CRAM

- [x] 2.1 Add extension/detection and sequential `pysam.AlignmentFile` reading.
- [x] 2.2 Support explicit reference configuration without automatic downloads.
- [x] 2.3 Match SAM/BAM row semantics, reset, totals where cheap, and read-bulk behavior.
- [ ] 2.4 Add reference-present, reference-missing, indexed, unindexed, truncated, and memory tests.

## 3. BED

- [x] 3.1 Implement streaming BED3–BED12+ parsing and writing.
- [x] 3.2 Validate optional field and block consistency without changing coordinates.
- [ ] 3.3 Add compressed, header/browser/track, malformed, empty, round-trip, and large-stream tests.

## 4. GFF3/GTF

- [x] 4.1 Implement streaming nine-column parsing with directive/comment metadata.
- [x] 4.2 Implement parsed and lossless/raw attribute modes for GFF3 and GTF.
- [x] 4.3 Implement bounded writes with correct escaping and header/directive preservation.
- [ ] 4.4 Add malformed attributes, FASTA-tail policy, compressed, round-trip, and memory tests.

## 5. Documentation and verification

- [x] 5.1 Document coordinate conventions, schemas, references, compression, and limitations prominently.
- [ ] 5.2 Add representative fixtures and bio-family CI coverage.
- [ ] 5.3 Run Ruff, focused/full tests, memory tests, and strict OpenSpec validation.
