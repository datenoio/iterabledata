---
title: FASTA Format
description: FASTA biological sequences in IterableData
---

# FASTA Format

## Description

FASTA is a text format for biological sequences (DNA, RNA, protein). IterableData streams one record per sequence header with `id`, `description`, and `sequence`. Registry id is `fa` (aliases: `fasta`, `fna`, `faa`). It is **read-only** in this release. No optional dependency — stdlib only.

## File Extensions

- `.fa` — FASTA (registry id `fa`)
- `.fasta` — common alias
- `.fna` — nucleic acid FASTA alias
- `.faa` — amino acid FASTA alias

## Implementation Details

### Reading

- Line-oriented parser: `>` headers start a new record
- Header split into first token (`id`) and remainder (`description`)
- Sequence lines are concatenated (blank lines skipped)
- Streams from filename or text stream; supports `encoding`

### Writing

Writing is not supported.

### Key Features

- **Streaming sequences**: does not require loading the whole file as a single string
- **Zero extras**: no pip optional beyond base `iterabledata`
- **Flat records**: one dict per sequence

## Usage

```python
from iterable import open_iterable

with open_iterable("genes.fa") as source:
    for rec in source:
        print(rec["id"], len(rec["sequence"]), rec.get("description"))
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
2. **Multi-line quality / wrapped formats** other than classic FASTA are not handled
3. Very large single sequences still allocate the full sequence string in memory per record

## Error Handling

- No **ImportError** for missing third-party deps (stdlib parser)
- Write mode does not produce records; format is registered **writable=False**
- **I/O errors**: missing or unreadable files
- Malformed files may yield incomplete last records or skip empty content

## Related Formats

- [FASTQ](fq.md) — sequences with quality scores
- [BAM](bam.md) / [SAM](sam.md) — alignments
- [Genomic intervals](genomic-intervals.md) — BED/GFF/GTF
