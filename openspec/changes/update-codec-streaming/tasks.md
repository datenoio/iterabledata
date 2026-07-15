## 1. Snappy codec

- [x] 1.1 Replace full-buffer read in `SnappyCodec.open()` with a lazy file-like wrapper using snappy framed/stream decompression
- [x] 1.2 Make `SnappyCodec` write path compress incrementally
- [x] 1.3 Verify `.sz` and `.snappy` extension handling and existing fixtures still round-trip

## 2. LZO codec

- [x] 2.1 Investigate streaming support in `python-lzo`; implement chunked decompression or bounded spill strategy
- [x] 2.2 Make `LZOCodec` write path incremental where the library allows
- [x] 2.3 Document any residual memory limitation in the codec docstring if true streaming is impossible

## 3. Tests

- [x] 3.1 Round-trip tests for both codecs over CSV and JSONL, including multi-megabyte generated payloads
- [x] 3.2 Memory-bound test: decompressing a large file keeps peak RSS well below uncompressed size (skip if `memory-profiler` absent)
- [x] 3.3 Run full codec test suite and lint
