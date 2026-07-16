## 1. Profile model

- [x] 1.1 Define `fast`, `balanced`, and `max` profiles and codec-specific mappings.
- [x] 1.2 Define precedence between profile and explicit codec parameters.
- [x] 1.3 Validate unsupported profiles/parameters with actionable messages.
- [x] 1.4 Expose effective settings through debug/observability metadata.

## 2. Codec integration

- [x] 2.1 Apply profiles to gzip, Zstandard, LZ4, Brotli, bzip2, and XZ where meaningful.
- [x] 2.2 Document fixed-performance codecs such as Snappy and LZO appropriately.
- [x] 2.3 Add framed/legacy-path diagnostics for Snappy and LZO.
- [x] 2.4 Correct/document `ILZO1` versus `.lzop` interoperability claims.
- [x] 2.5 Adopt the reviewed balanced high-level default with migration notes.

## 3. Performance and memory coverage

- [ ] 3.1 Add compressible and low-compressibility fixtures.
- [ ] 3.2 Benchmark read/write throughput, ratio, peak memory, and reset cost for primary codecs/profiles.
- [ ] 3.3 Add normalized/paired regression thresholds and preserve advisory platform results.
- [ ] 3.4 Test explicit-level overrides and round-trip compatibility.

## 4. Documentation and verification

- [x] 4.1 Publish a profile/codec matrix with effective parameters and trade-offs.
- [x] 4.2 Document legacy full-buffer paths and interoperability boundaries.
- [ ] 4.3 Run codec tests, memory tests, performance gate, full suite, and strict OpenSpec validation.
