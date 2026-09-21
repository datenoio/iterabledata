# Genomic alignments and intervals

IterableData reads common genomics interval and alignment formats as dictionaries. SAM, BAM, and CRAM have their own pages; this page covers **BED**, **GFF3**, and **GTF**.

Compressed text (`.bed.gz`, `.gff3.zst`, and similar) uses the usual filename codec detection.

## CRAM

CRAM is a reference-compressed alignment format with its own page: [CRAM](cram.md).

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

### Parameters (BED)

| Parameter | Type | Default | Required | Description |
|-----------|------|---------|----------|-------------|
| `headers` | list[str] | `[]` | No | Optional collected track/browser/`#` header lines (also filled while reading) |

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

### Parameters (GFF3 / GTF)

| Parameter | Type | Default | Required | Description |
|-----------|------|---------|----------|-------------|
| `attribute_mode` | `"parsed"` or `"lossless"` | `"parsed"` | No | Parse attributes, or also keep the raw string as `attributes_raw` |
| `include_comments` | bool | `False` | No | Yield directive/comment lines as `{"record_type": "directive", "value": ...}` |

GFF3 and GTF support writing. **Install:** no extra for BED/GFF3/GTF (plain text).

## Error Handling

- **ValueError** (BED): Fewer than three columns, `end < start`, or `block_count` mismatch
- **ValueError** (GFF3/GTF): Wrong column count, invalid coordinates, bad `attribute_mode`, or malformed GFF3 attributes
- **FileNotFoundError**: Path is wrong or the file is missing

See [Troubleshooting](/getting-started/troubleshooting) for more help.

## Limitations

1. **BED vs GFF/GTF coordinates differ** (0-based half-open vs 1-based closed); values are not converted
2. **`.vcf` is not this page** — genomic VCF/BCF is [genomic_vcf](genomic_vcf.md); vCard is [VCF](vcf.md)

## Related Formats

- [SAM](sam.md) / [BAM](bam.md) / [CRAM](cram.md) — alignments
- [Genomic VCF/BCF](genomic_vcf.md) — variants
- [FASTA](fa.md) / [FASTQ](fq.md) — sequences
