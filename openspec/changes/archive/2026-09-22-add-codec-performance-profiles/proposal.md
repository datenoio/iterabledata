# Change: Add Codec Performance Profiles and Baselines

## Why

Codec defaults are inconsistent and several favor maximum compression over conversion throughput, including Zstandard level 19, Brotli quality 11, and high-compression LZ4. The enforced performance gate exercises gzip only indirectly, so codec throughput, ratio, memory, reset cost, and legacy fallback behavior can regress unnoticed.

## What Changes

- Add documented `fast`, `balanced`, and `max` performance profiles with codec-specific mappings.
- Use `balanced` as the high-level default while preserving explicit compression-level overrides.
- Report effective codec/profile settings and whether a legacy full-buffer fallback is active.
- Add throughput, compression-ratio, peak-memory, and reset/reopen benchmarks for primary codecs.
- Clarify LZO custom framing versus `lzop` interoperability.

## Dependencies

- Archive `update-codec-streaming` before implementation so its `compression-codecs` capability is current.
- Coordinate benchmark jobs with `optimize-format-io-hot-paths`.

## Impact

- Affected specs: `compression-codecs`
- Affected code: codec constructors/options, detection/open wiring, catalog/docs, performance tests
- Behavioral change: callers relying on implicit high-compression defaults may see faster writes and larger files; explicit levels retain exact control
