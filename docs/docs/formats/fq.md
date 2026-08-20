---
title: FASTQ Format
description: FASTQ reads with quality scores in IterableData
---

# FASTQ Format

## Description

FASTQ stores sequencing reads as four-line blocks: identifier, sequence, separator, and quality string. IterableData yields one dict per read with `id`, `description`, `sequence`, and `quality`. Registry id is `fq` (alias `fastq`). It is **read-only** in this release. Stdlib only — no optional dependency.

## File Extensions

- `.fq` — FASTQ (registry id `fq`)
- `.fastq` — common alias

## Implementation Details

### Reading

- Parses classic four-line FASTQ blocks
- `@` header split into `id` and optional `description`
- Skips incomplete trailing blocks
- Streams from filename or text stream; supports `encoding`

### Writing

Writing is not supported.

### Key Features

- **Quality-aware reads**: Phred ASCII quality string preserved as-is
- **Zero extras**: base install only
- **Flat records**: one dict per read

## Usage

```python
from iterable import open_iterable

with open_iterable("reads.fq") as source:
    for rec in source:
        print(rec["id"], len(rec["sequence"]), rec["quality"][:10])
```

## Parameters

| Parameter | Type | Default | Required | Description |
|-----------|------|---------|----------|-------------|
| `encoding` | str | `utf-8` | No | Text encoding for the file |

## Installation

```bash
pip install iterabledata
```

No format-specific extra.

## Limitations

1. **Read-only**
2. **Classic 4-line blocks** only (multi-line sequence/quality variants not supported)
3. Does not validate that sequence and quality lengths match

## Error Handling

- No **ImportError** for missing third-party deps
- Format is registered **writable=False**
- **I/O errors**: missing or unreadable files
- Truncated files stop at the last complete block

## Related Formats

- [FASTA](fa.md) — sequences without qualities
- [BAM](bam.md) / [SAM](sam.md) — alignments
