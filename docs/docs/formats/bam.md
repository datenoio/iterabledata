---
title: BAM Format
description: Binary Alignment Map (BAM) in IterableData
---

# BAM Format

## Description

BAM is the compressed binary form of the Sequence Alignment/Map (SAM) format used for genomic read alignments. IterableData streams alignments with `pysam` and yields one dict per aligned segment. It is **read-only** in this release.

## File Extensions

- `.bam` — Binary Alignment Map

## Implementation Details

### Reading

- Opens with `pysam.AlignmentFile(filename, "rb")`
- Requires a local **filename** (streams are not supported)
- Yields fields: `query_name`, `flag`, `reference_id`, `reference_start`, `mapping_quality`, `cigarstring`, `next_reference_id`, `next_reference_start`, `template_length`, `query_sequence`, `query_qualities` (Phred+33 string)

### Writing

Writing is not supported.

### Key Features

- **Streaming alignments**: one read at a time via pysam
- **Shared field model** with [SAM](sam.md)
- **Binary datamode**

## Usage

```python
from iterable import open_iterable

with open_iterable("alignments.bam") as source:
    for aln in source:
        print(aln["query_name"], aln["reference_start"], aln["cigarstring"])
```

## Parameters

No format-specific `iterableargs`. A filesystem path is required.

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
4. Optional BAM tags / mate details beyond the listed fields are not exported

## Error Handling

- **ImportError**: missing `pysam` — install `iterabledata[alignment]` or `[bio]`
- **ValueError**: neither filename nor stream provided (streams still unsupported for open)
- **I/O / pysam errors**: corrupt BAM or missing index scenarios as raised by pysam
- Format is registered **writable=False**

## Related Formats

- [SAM](sam.md) — text alignments
- [FASTA](fa.md) — reference / contig sequences
- [FASTQ](fq.md) — reads with quality scores
- [Genomic intervals](genomic-intervals.md) — BED/GFF/GTF/CRAM
