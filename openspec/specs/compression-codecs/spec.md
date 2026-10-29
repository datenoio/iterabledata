# compression-codecs Specification

## Purpose
TBD - created by archiving change update-codec-streaming. Update Purpose after archive.
## Requirements
### Requirement: Streaming Codec Decompression

Compression codecs SHALL expose the decompressed content as a lazy file-like stream whose peak memory usage is bounded by a fixed buffer size, not by the uncompressed payload size. A codec MAY fall back to bounded chunked decompression when the underlying library offers no streaming API, but SHALL NOT load the entire decompressed payload into memory before the first byte is readable.

#### Scenario: Snappy-compressed file streams

- **WHEN** a `.sz` or `.snappy` compressed CSV/JSONL file is opened via `open_iterable()`
- **THEN** records SHALL be yielded without first materializing the full decompressed payload in memory
- **AND** peak memory SHALL remain bounded by the codec's buffer size

#### Scenario: LZO-compressed file streams or documents its bound

- **WHEN** a `.lzo`/`.lzop` compressed file is opened
- **THEN** decompression SHALL proceed in bounded chunks
- **AND** if the underlying library forces a non-streaming path, the codec docstring and format documentation SHALL state the memory bound explicitly

#### Scenario: Streaming write path

- **WHEN** records are written through a codec-wrapped iterable
- **THEN** compression SHALL happen incrementally as data is written
- **AND** the codec SHALL NOT buffer the entire output payload before compressing

### Requirement: Intent-Based Codec Performance Profiles

Codec construction through the public factory SHALL support `fast`, `balanced`, and `max` profiles with documented codec-specific settings. `balanced` SHALL be the high-level default when no profile or explicit level is provided.

#### Scenario: Balanced default

- **WHEN** a user writes through a supported codec without profile or level options
- **THEN** the factory SHALL apply that codec's documented balanced settings
- **AND** effective settings SHALL be available in debug diagnostics

#### Scenario: Explicit fast profile

- **WHEN** a user passes `codecargs={"profile": "fast"}`
- **THEN** the codec SHALL prioritize write/read throughput according to its documented mapping
- **AND** logical round-trip data SHALL remain unchanged

#### Scenario: Explicit codec level overrides profile

- **WHEN** a user supplies both a profile and a supported explicit compression level
- **THEN** the explicit codec level SHALL take precedence
- **AND** diagnostics SHALL report the effective level

#### Scenario: Codec has no tunable level

- **WHEN** a fixed-performance codec receives a profile
- **THEN** it SHALL use its fixed algorithm safely
- **AND** documentation/diagnostics SHALL state that the profile does not change its compression level

### Requirement: Codec Performance and Ratio Regression Coverage

The project SHALL benchmark representative primary codecs for read/write throughput, compression ratio, peak memory, and reset/reopen cost using both compressible and low-compressibility data.

#### Scenario: Codec benchmark result

- **WHEN** a codec/profile workload runs
- **THEN** its result SHALL record input bytes, output bytes, elapsed time or throughput, peak memory, profile, and backend version
- **AND** committed regression checks SHALL use reviewed tolerances

#### Scenario: Throughput improves by sacrificing ratio

- **WHEN** a fast profile is compared with max on compressible input
- **THEN** results SHALL report both throughput and ratio
- **AND** acceptance SHALL not consider elapsed time alone

### Requirement: Legacy and Interoperability Diagnostics

Codecs with legacy non-streaming inputs or project-specific framing SHALL identify those paths accurately in documentation and runtime diagnostics.

#### Scenario: Legacy raw Snappy or LZO input

- **WHEN** a legacy raw input requires full-buffer decompression
- **THEN** diagnostics SHALL identify the non-streaming fallback
- **AND** capability/documentation metadata SHALL not claim bounded memory for that input variant

#### Scenario: Project-specific LZO frame

- **WHEN** the library writes `ILZO1` framed LZO data
- **THEN** documentation SHALL identify it as project-specific
- **AND** `.lzop` interoperability SHALL be claimed only if a tested `lzop` container implementation is used

### Requirement: Optional Accelerated Gzip Backend

When ISA-L (`isal`) is installed, the gzip codec SHALL compress with it at the levels where its ratio matches zlib's (levels 1-2, the `fast` profile) and SHALL keep zlib at other levels unless the `backend="isal"` codec option requests ISA-L. Without ISA-L it SHALL use the standard library. Output SHALL remain a valid gzip stream readable by the standard library.

#### Scenario: Writing gzip with isal installed

- **WHEN** a user writes `out.jsonl.gz` with `codecargs={"profile": "fast"}` and `isal` installed
- **THEN** the codec SHALL compress with ISA-L
- **AND** `gzip.open("out.jsonl.gz")` SHALL read back the same records

#### Scenario: isal not installed

- **WHEN** `isal` is not importable
- **THEN** the codec SHALL compress with the standard-library `gzip` module without warnings

