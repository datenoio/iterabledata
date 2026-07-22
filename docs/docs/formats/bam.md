---
title: BAM Format
description: Binary Alignment Map genomic reads in IterableData
---

# BAM Format

Stream BAM (Binary Alignment/Map) alignments as one record per read.

## Overview

| Property | Value |
|----------|-------|
| Format id | `bam` |
| Class | `BAMIterable` |
| Extensions | `.bam` |
| Read | Yes |
| Write | No |
| Extra | `alignment` (`pysam`) |
| Maturity | stable |

## Record shape

```python
{
    "query_name": "read1",
    "flag": 0,
    "reference_id": 0,
    "reference_start": 100,
    "mapping_quality": 60,
    "cigarstring": "50M",
    "next_reference_id": -1,
    "next_reference_start": -1,
    "template_length": 0,
    "query_sequence": "ACGT...",
    "query_qualities": "IIII...",
}
```

Requires a filename (streams not supported).

## Usage

```python
from iterable.helpers.detect import open_iterable

with open_iterable("alignments.bam", format="bam") as source:
    for aln in source:
        print(aln["query_name"], aln["reference_start"], aln["cigarstring"])
```

Install with `pip install iterabledata[alignment]`.

## See also

- [SAM](/formats/sam) — text Sequence Alignment/Map
- [Supported formats](/formats/)
