# Genomic alignments and intervals

`CRAMIterable` uses `pysam` and accepts an explicit
`reference_filename`; it never downloads a reference automatically. SAM, BAM,
and CRAM rows share alignment field names.

`BEDIterable` preserves BED's 0-based, half-open coordinates and validates
BED3–BED12 block fields. `GFF3Iterable` and `GTFIterable` preserve the native
1-based, closed convention, directives/comments, parsed attributes, and an
optional `attribute_mode="lossless"` raw attribute field. Existing filename
codec detection supports compressed text inputs.
