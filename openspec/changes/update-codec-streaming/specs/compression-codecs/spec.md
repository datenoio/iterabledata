## ADDED Requirements

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
