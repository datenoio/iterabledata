---
title: FASTA Format
description: FASTA biological sequences in IterableData
---

# FASTA Format

Read FASTA sequence files as one record per sequence (stdlib; no extra).

## Overview

| Property | Value |
|----------|-------|
| Format id | `fa` (aliases `fasta`, `fna`, `faa`) |
| Class | `FASTAIterable` |
| Extensions | `.fa`, `.fasta`, `.fna`, `.faa` |
| Read | Yes |
| Write | No |
| Extra | none (stdlib) |
| Maturity | stable |

## Record shape

```python
{"id": "seq1", "description": "example protein", "sequence": "MKTAYIAK..."}
```

## Usage

```python
from iterable import open_iterable

with open_iterable("genes.fa") as source:
    for rec in source:
        print(rec["id"], len(rec["sequence"]))
```

## See also

- [FASTQ](/formats/fq) — sequences with quality scores
- [Supported formats](/formats/)

## Parameters

| Parameter | Type | Default | Required | Description |
|-----------|------|---------|----------|-------------|
| `encoding` | str | `'utf-8'` | No | Passed via `iterableargs`. |

