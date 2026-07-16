## ADDED Requirements

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
