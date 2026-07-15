## ADDED Requirements

### Requirement: Genomic VCF Reading

The system SHALL provide a `genomic_vcf` format that reads genomic Variant Call Format (and BCF where the backend supports it) files, yielding one record per variant with the standard columns (CHROM, POS, ID, REF, ALT, QUAL, FILTER), parsed INFO fields, and per-sample FORMAT fields. Reading SHALL stream variant by variant.

#### Scenario: Read variants from a VCF file

- **WHEN** a file whose header contains `##fileformat=VCF` is opened via `open_iterable()`
- **THEN** iteration SHALL yield one record per variant line
- **AND** each record SHALL include CHROM, POS, REF, ALT and parsed INFO fields

#### Scenario: Missing backend raises a resolvable hint

- **WHEN** a genomic VCF file is opened and `pysam` is not installed
- **THEN** the system SHALL raise `ImportError`
- **AND** the message SHALL name the `bio` extra declared in `pyproject.toml`

### Requirement: VCF Content Disambiguation

Because the `.vcf` extension is shared by genomic Variant Call Format and vCard, the system SHALL disambiguate by content: files whose header contains `##fileformat=VCF` SHALL be detected as `genomic_vcf`, and files whose content begins with `BEGIN:VCARD` SHALL be detected as the vCard `vcf` format.

#### Scenario: Genomic content detected as genomic_vcf

- **WHEN** `.vcf` content starts with `##fileformat=VCFv4.2`
- **THEN** format detection SHALL resolve to `genomic_vcf`
- **AND** SHALL NOT resolve to the vCard `vcf` format

#### Scenario: vCard content detected as vcf

- **WHEN** `.vcf` content starts with `BEGIN:VCARD`
- **THEN** format detection SHALL resolve to the vCard `vcf` format
- **AND** SHALL NOT resolve to `genomic_vcf`
