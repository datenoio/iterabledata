# Change: Add genomic Variant Call Format (VCF/BCF) as a distinct format

## Why

The `.vcf` extension is currently handled only as vCard (`iterable/datatypes/vcf.py`, `BEGIN:VCARD`). Bioinformatics pipelines emit genomic Variant Call Format files that also use `.vcf`, and these are silently mis-detected as vCard. The review recommends splitting genomic VCF into its own format keyed on content magic (`##fileformat=VCF`) so both meanings coexist without collision, and adding related genomic formats (BCF) behind a `bio` extra.

## What Changes

- Add a new `genomic_vcf` format descriptor and `GenomicVCFIterable` in `iterable/datatypes/genomic_vcf.py`, backed by `pysam` (or `cyvcf2`), yielding one record per variant with parsed INFO/FORMAT/sample columns.
- Add content-based detection: `.vcf` files are classified as `genomic_vcf` when the header contains `##fileformat=VCF`, and as vCard `vcf` when content begins with `BEGIN:VCARD`.
- Add BCF (binary VCF) read support under the same module where `pysam` provides it.
- Add a `bio` optional-dependency extra (`pysam`) in `pyproject.toml` and include it in `[all]` where pip-installable.
- Read-only initially; streaming record iteration over variants.
- Docs page and fixtures (a tiny `##fileformat=VCFv4.2` sample).

## Impact

- Affected specs: `genomic-vcf-format` (new capability)
- Affected code: `iterable/datatypes/genomic_vcf.py` (new), `iterable/helpers/format_registry.py` (descriptor + magic), `iterable/helpers/content_detection.py`, `pyproject.toml`, `docs/docs/formats/genomic_vcf.md`, `tests/test_genomic_vcf.py`
- The existing vCard `vcf` format is unchanged except that content detection now disambiguates the two.
