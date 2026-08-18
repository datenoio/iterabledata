---
title: SAM Format
description: Sequence Alignment/Map text alignments in IterableData
---

# SAM Format

Stream SAM (Sequence Alignment/Map) text alignments as one record per read.

## Overview

| Property | Value |
|----------|-------|
| Format id | `sam` |
| Class | `SAMIterable` |
| Extensions | `.sam` |
| Read | Yes |
| Write | No |
| Extra | `alignment` (`pysam`) |
| Maturity | stable |

## Record shape

Same fields as BAM:

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
from iterable import open_iterable

with open_iterable("alignments.sam", format="sam") as source:
    for aln in source:
        print(aln["query_name"], aln["reference_start"])
```

Install with `pip install iterabledata[alignment]`.

## See also

- [BAM](/formats/bam) — binary alignments
- [Supported formats](/formats/)
