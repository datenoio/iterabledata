---
title: FASTQ Format
description: FASTQ sequencing reads with qualities in IterableData
---

# FASTQ Format

Read FASTQ reads as one record per four-line block (stdlib; no extra).

## Overview

| Property | Value |
|----------|-------|
| Format id | `fq` (alias `fastq`) |
| Class | `FASTQIterable` |
| Extensions | `.fq`, `.fastq` |
| Read | Yes |
| Write | No |
| Extra | none (stdlib) |
| Maturity | stable |

## Record shape

```python
{
    "id": "read1",
    "description": "",
    "sequence": "ACGTACGT",
    "quality": "IIIIIIII",
}
```

## Usage

```python
from iterable import open_iterable

with open_iterable("reads.fq") as source:
    for rec in source:
        print(rec["id"], rec["sequence"], rec["quality"])
```

## See also

- [FASTA](/formats/fa) — sequences without qualities
- [Supported formats](/formats/)
