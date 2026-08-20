# Genomic VCF / BCF Format

## Description

Genomic **Variant Call Format** (VCF) and its binary form **BCF** describe
sequence variants produced by bioinformatics pipelines. VCF files declare
`##fileformat=VCFv4.x` in their header and list one variant per line with the
columns `CHROM`, `POS`, `ID`, `REF`, `ALT`, `QUAL`, `FILTER`, `INFO`, and
optional per-sample `FORMAT` fields. This format is **read-only**.

> **`.vcf` is a shared extension.** The same extension is used by
> [vCard contact files](vcf.md). IterableData disambiguates by content:
>
> - Content starting with `##fileformat=VCF` → **`genomic_vcf`** (this format)
> - Content starting with `BEGIN:VCARD` → **`vcf`** (vCard)
>
> Detection reads the file header, so `open_iterable('variants.vcf')` routes to
> the correct reader automatically.

## File Extensions

- `.vcf` - Variant Call Format (text; disambiguated from vCard by content)
- `.bcf` - Binary Call Format

## Implementation Details

### Reading

- Backed by `pysam.VariantFile`, which auto-detects plain VCF, bgzipped VCF,
  and BCF from content
- **Streaming**: variants are read incrementally; the file is never fully
  materialized in memory
- Requires a file path; stream input is not supported (`pysam` needs a
  seekable/indexable file)

### Writing

Writing is not supported. Attempting to write raises `WriteNotSupportedError`.

### Key Features

- **Content detection**: disambiguates genomic VCF from vCard `.vcf`
- **Sample fields**: per-sample FORMAT values under `SAMPLES`
- **INFO parsing**: INFO keys become a dictionary

## Usage

```python
from iterable import open_iterable

with open_iterable("variants.vcf") as source:
    for variant in source:
        print(variant["CHROM"], variant["POS"], variant["REF"], "->", variant["ALT"])
        print("  INFO:", variant["INFO"])
        print("  samples:", variant["SAMPLES"])
```

Each record is a dictionary:

| Key       | Description                                        |
| --------- | -------------------------------------------------- |
| `CHROM`   | Chromosome / contig name                           |
| `POS`     | 1-based position                                   |
| `ID`      | Variant identifier (e.g. dbSNP `rs...`) or `None`  |
| `REF`     | Reference allele                                   |
| `ALT`     | List of alternate alleles                          |
| `QUAL`    | Phred-scaled quality score or `None`               |
| `FILTER`  | List of filter names (e.g. `["PASS"]`)             |
| `INFO`    | Parsed INFO dictionary                             |
| `SAMPLES` | Mapping of sample name to its FORMAT fields        |

## Parameters

No format-specific `iterableargs`. Pass a filename.

| Parameter | Type | Default | Required | Description |
|-----------|------|---------|----------|-------------|
| *(none)* | — | — | — | Filename required; no format-specific parameters |

## Error Handling

- **ImportError**: Missing `pysam` — install with `pip install iterabledata[bio]`
- **ValueError**: Stream / missing filename (`Genomic VCF format requires a filename`)
- **WriteNotSupportedError**: Writing genomic VCF/BCF is not supported
- **FileNotFoundError** / pysam errors: missing path or corrupt VCF/BCF

See [Troubleshooting](/getting-started/troubleshooting) for more help.

## Installation

Genomic VCF/BCF support requires [`pysam`](https://pysam.readthedocs.io):

```bash
pip install 'iterabledata[bio]'
```

If `pysam` is not installed, opening a genomic VCF raises an `ImportError`
naming the `bio` extra.

## Limitations

- Read-only.
- Requires the `pysam` optional dependency (`bio` extra).
- Stream/file-object input is not supported; pass a filename.

## Related Formats

- [Genomic intervals](genomic-intervals.md) — CRAM, BED, GFF3, GTF
- [SAM](sam.md) / [BAM](bam.md) — alignments
- [vCard VCF](vcf.md) — contact cards (same `.vcf` extension)
