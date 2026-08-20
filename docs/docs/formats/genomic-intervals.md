# Genomic alignments and intervals

IterableData reads common genomics interval and alignment formats as dictionaries. SAM and BAM have their own pages; this page covers **CRAM**, **BED**, **GFF3**, and **GTF**.

Compressed text (`.bed.gz`, `.gff3.zst`, and similar) uses the usual filename codec detection.

## CRAM

CRAM is a reference-compressed alignment format. Rows use the same field names as [SAM](sam.md) / [BAM](bam.md).

IterableData **never downloads a reference**. Pass `reference_filename` when the file requires one.

```python
from iterable import open_iterable

with open_iterable(
    "sample.cram",
    iterableargs={"format": "cram", "reference_filename": "ref.fa"},
) as source:
    for row in source:
        print(row["qname"], row["rname"], row["pos"])
```

| Parameter | Type | Default | Required | Description |
|-----------|------|---------|----------|-------------|
| `reference_filename` | str | none | Often yes | FASTA reference; required for many CRAM files |

**Install:** `pip install 'iterabledata[alignment]'` (or `[bio]`). Requires `pysam`. **Read-only.**

## BED

BED3–BED12 interval tables with **0-based, half-open** coordinates (`start`/`end`). Optional fields map to `name`, `score`, `strand`, thick coordinates, RGB, and blocks. Extra columns are stored in `extra`. Writes are supported.

```python
from iterable import open_iterable

with open_iterable("peaks.bed") as source:
    for row in source:
        print(row["chrom"], row["start"], row["end"])

with open_iterable("out.bed", mode="w") as dest:
    dest.write({"chrom": "chr1", "start": 100, "end": 200, "name": "peak1"})
```

Invalid coordinates (`end < start`, mismatched block counts) raise `ValueError`.

## GFF3 and GTF

GFF3 and GTF are tab-separated annotations with **1-based, closed** coordinates. Directives and comments are collected on `metadata`. Attributes are parsed into an ordered map; set `attribute_mode="lossless"` to also keep the raw attribute string.

```python
from iterable import open_iterable

with open_iterable("genes.gff3", iterableargs={"attribute_mode": "parsed"}) as source:
    for row in source:
        print(row["seqid"], row["start"], row["end"], row["attributes"])

with open_iterable("genes.gtf", iterableargs={"include_comments": True}) as source:
    for row in source:
        print(row)
```

| Parameter | Type | Default | Required | Description |
|-----------|------|---------|----------|-------------|
| `attribute_mode` | `"parsed"` or `"lossless"` | `"parsed"` | No | Parse attributes, or also keep the raw string |
| `include_comments` | bool | `False` | No | Yield directive/comment lines as rows |

GFF3 and GTF support writing. **Install:** no extra for BED/GFF3/GTF (plain text). CRAM needs `[alignment]` / `[bio]`.

## Limitations

1. **CRAM is read-only** and may require a local reference FASTA
2. **BED vs GFF/GTF coordinates differ** (0-based half-open vs 1-based closed); values are not converted
3. **`.vcf` is not this page** — genomic VCF/BCF is [genomic_vcf](genomic_vcf.md); vCard is [VCF](vcf.md)

## Related Formats

- [SAM](sam.md) / [BAM](bam.md) — alignments
- [Genomic VCF/BCF](genomic_vcf.md) — variants
- [FASTA](fa.md) / [FASTQ](fq.md) — sequences
