---
title: CRAM Format
description: Reference-compressed CRAM alignments in IterableData
---

# CRAM Format

## Description

CRAM is a reference-compressed binary format for genomic read alignments. IterableData streams alignments with `pysam` and yields one dict per aligned segment, using the same field model as SAM and BAM. It is **read-only** in this release.

## File Extensions

- `.cram` — reference-Compressed Alignment Map

## Implementation Details

### Reading

- Opens with `pysam.AlignmentFile(filename, "rc", reference_filename=...)`; `reference_filename` is passed only when provided
- Requires a local **filename** (streams are not supported)
- IterableData **never downloads a reference** — pass `reference_filename` when the file requires one
- Yields fields: `query_name`, `flag`, `reference_id`, `reference_start`, `mapping_quality`, `cigarstring`, `next_reference_id`, `next_reference_start`, `template_length`, `query_sequence`, `query_qualities` (Phred+33 string)

### Writing

Writing is not supported.

### Key Features

- **Streaming alignments**: one read at a time via pysam, with bounded read memory
- **Shared field model** with [SAM](sam.md) and [BAM](bam.md)
- **Explicit reference configuration** via `reference_filename`
- **Binary datamode**

## Usage

```python
from iterable import open_iterable

with open_iterable(
    "alignments.cram",
    iterableargs={"format": "cram", "reference_filename": "ref.fa"},
) as source:
    for aln in source:
        print(aln["query_name"], aln["reference_start"], aln["cigarstring"])
```

## Parameters

| Parameter | Type | Default | Required | Description |
|-----------|------|---------|----------|-------------|
| `reference_filename` | str | none | Often yes | Local FASTA reference; required for many CRAM files |

A filesystem path for the CRAM file itself is always required.

## Installation

```bash
pip install 'iterabledata[alignment]'
# or
pip install 'iterabledata[bio]'
```

Requires `pysam`.

## Limitations

1. **Read-only**
2. **Filename required** (no stream)
3. **Requires pysam**
4. **May require a local reference FASTA** via `reference_filename`
5. Optional CRAM tags / mate details beyond the listed fields are not exported

## Error Handling

- **ImportError**: missing `pysam` — install `iterabledata[alignment]` or `[bio]`
- **ValueError**: no filename provided (streams are not supported)
- **ValueError**: unable to open CRAM — provide `reference_filename` when required
- **ValueError**: unable to decode CRAM records at read time — the file may be truncated/corrupt or require a reference; htslib's opaque decode errors are wrapped with this guidance
- **I/O / pysam errors**: other corrupt CRAM or missing reference scenarios as raised by pysam
- Format is registered **writable=False**

## Related Formats

- [SAM](sam.md) — text alignments
- [BAM](bam.md) — binary alignments
- [Genomic intervals](genomic-intervals.md) — BED/GFF3/GTF
- [Genomic VCF/BCF](genomic_vcf.md) — variants
