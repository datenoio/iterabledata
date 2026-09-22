## Context

Each codec currently chooses its own default level. The resulting defaults do not express a common user intent and are not benchmarked as a family. Snappy/LZO framed streams are bounded, but legacy raw inputs still require full-buffer decompression.

## Goals / Non-Goals

- Goals:
  - Give users portable intent-based tuning.
  - Make the default suitable for general ETL throughput.
  - Preserve exact codec-level configuration.
  - Protect speed, ratio, and memory together.
- Non-Goals:
  - Promise identical compressed bytes across library/backend versions.
  - Make unrelated codecs achieve identical ratios.
  - Hide legacy non-streaming behavior.

## Decisions

### Profiles and precedence

`codecargs={"profile": "fast|balanced|max"}` maps to reviewed codec-specific parameters. An explicit `compression_level` or equivalent codec parameter overrides the profile for that codec. Invalid combinations fail with supported values.

### Balanced default

High-level `open_iterable()` codec construction uses `balanced` when neither profile nor level is supplied. Direct constructor behavior may transition with a deprecation window if compatibility requires it; the final effective setting is documented and observable.

### Multi-dimensional baselines

Benchmarks record uncompressed/compressed bytes, elapsed read/write time, throughput, peak memory, codec/backend version, and profile. Both compressible text and low-compressibility binary-like fixtures are included.

### Legacy diagnostics

Snappy/LZO readers identify framed versus legacy raw input. Capability/debug output reports when a legacy full-buffer path is selected. LZO's `ILZO1` framing is documented as project-specific; `.lzop` compatibility is not claimed unless implemented and tested.

## Risks / Trade-offs

- A balanced default changes file size. Mitigation: release note, explicit `max`, and level override.
- Benchmarks vary by native library and CPU. Mitigation: paired/normalized gates on one runner and advisory cross-platform results.
- Profile mappings can drift as backends evolve. Mitigation: versioned documentation and committed benchmark metadata.

## Migration Plan

1. Add profiles without changing defaults and publish effective-setting diagnostics.
2. Establish benchmark data and review mappings.
3. Switch high-level default to balanced with release notes/deprecation where needed.
4. Enforce regression thresholds after one stable baseline cycle.

## Open Questions

- Should direct codec constructors adopt `balanced` immediately or only high-level factory use?
- Which codec/version combinations require platform-specific profile mappings?
