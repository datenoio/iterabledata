## 1. Setup

- [x] 1.1 Add descriptors for `segy`, `grib2`, and `mseed`.
- [x] 1.2 Choose optional extra layout and ImportError messages.
- [x] 1.3 Document record schemas for traces, messages, and windows.

## 2. Implementations

- [x] 2.1 Implement SEG-Y trace iterable (read-only v1).
- [x] 2.2 Implement GRIB2 message iterable (read-only v1).
- [x] 2.3 Implement miniSEED window/trace iterable (read-only v1).

## 3. Tests and docs

- [x] 3.1 Add small fixtures for each format.
- [x] 3.2 Add detection, malformed, optional-dependency, and memory tests.
- [x] 3.3 Document formats, limitations, and examples.
- [x] 3.4 Run `openspec validate add-geophysical-formats --strict`.
