## 1. Format implementation

- [x] 1.1 Create `iterable/datatypes/genomic_vcf.py` with `GenomicVCFIterable(BaseFileIterable)` using `pysam.VariantFile`
- [x] 1.2 Yield one record per variant with CHROM/POS/ID/REF/ALT/QUAL/FILTER and parsed INFO + per-sample FORMAT fields
- [x] 1.3 Add BCF read support via the same `pysam.VariantFile` path
- [x] 1.4 Raise a clear `ImportError` with the `bio` extra hint when `pysam` is missing

## 2. Registry and detection

- [x] 2.1 Add `genomic_vcf` descriptor to `format_registry.py` (read-only, text, streaming)
- [x] 2.2 Add content magic: `##fileformat=VCF` → `genomic_vcf`; `BEGIN:VCARD` → `vcf`
- [x] 2.3 Ensure extension-based `.vcf` detection defers to content detection when ambiguous

## 3. Packaging and docs

- [x] 3.1 Add `bio` extra (`pysam`) to `pyproject.toml`; add to `[all]`
- [x] 3.2 Write `docs/docs/formats/genomic_vcf.md` clarifying the vCard vs genomic distinction

## 4. Tests

- [x] 4.1 Add fixture `tests/fixtures/sample.genomic.vcf` (`##fileformat=VCFv4.2`, a few variants)
- [x] 4.2 Detection test: genomic sample → `genomic_vcf`, vCard sample → `vcf`
- [x] 4.3 Read test asserting variant fields; skip if `pysam` absent
- [x] 4.4 Run suite and lint
