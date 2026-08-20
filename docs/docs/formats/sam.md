---
title: SAM Format
description: Sequence Alignment/Map (SAM) text in IterableData
---

# SAM Format

## Description

SAM is the tab-delimited text format for genomic sequence alignments. IterableData reads SAM with `pysam` and yields the same alignment dicts as BAM. It is **read-only** in this release.

## File Extensions

- `.sam` — Sequence Alignment/Map text

## Implementation Details

### Reading

- Opens with `pysam.AlignmentFile(filename, "r")`
- Requires a local **filename** (streams are not supported)
- Yields: `query_name`, `flag`, `reference_id`, `reference_start`, `mapping_quality`, `cigarstring`, `next_reference_id`, `next_reference_start`, `template_length`, `query_sequence`, `query_qualities`

### Writing

Writing is not supported.

### Key Features

- **Text alignments**: human-inspectable SAM
- **Same record shape** as [BAM](bam.md)
- **pysam iteration**

## Usage

```python
from iterable import open_iterable

with open_iterable("alignments.sam") as source:
    for aln in source:
        print(aln["query_name"], aln["flag"], aln["query_sequence"])
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
4. Optional SAM tags beyond the listed fields are not exported

## Error Handling

- **ImportError**: missing `pysam` — install `iterabledata[alignment]` or `[bio]`
- **ValueError**: no filename provided
- **I/O / pysam errors**: malformed SAM or missing references as raised by pysam
- Format is registered **writable=False**

## Related Formats

- [BAM](bam.md) — binary alignments
- [FASTA](fa.md) — sequences
- [FASTQ](fq.md) — reads with qualities
