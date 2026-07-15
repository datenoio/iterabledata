# Change: Make Snappy and LZO codecs stream instead of full-buffer decompression

## Why

The 2026-07-14 performance review found that `SnappyCodec` (`iterable/codecs/snappycodec.py:45-63`) and `LZOCodec` (`iterable/codecs/lzocodec.py:35-43`) read the entire compressed file and decompress it into an in-memory `BytesIO` before yielding a single byte. Any `.sz`/`.snappy`/`.lzo` compressed CSV or JSONL therefore negates the library's streaming guarantees: peak memory is O(uncompressed file size), unlike the gzip/zstd/brotli codecs which wrap the file object lazily.

## What Changes

- Rework `SnappyCodec` to use python-snappy's framed streaming API (`snappy.StreamDecompressor` / `hadoop_snappy` framing where applicable) as a lazy file-like wrapper, matching the gzip/zstd pattern.
- Rework `LZOCodec` to decompress incrementally; if `python-lzo` exposes no streaming API, decompress in bounded chunks (lzop block framing) or document the limitation and cap memory via spill-to-temp-file.
- Write paths get the same treatment: compress incrementally on `write()` instead of buffering the full payload.
- Add large-file codec tests asserting bounded memory behavior (via `tests/test_memory_profiling.py` patterns) and round-trip correctness for both codecs.

## Impact

- Affected specs: `compression-codecs` (new capability)
- Affected code: `iterable/codecs/snappycodec.py`, `iterable/codecs/lzocodec.py`, `iterable/codecs/_stream.py`, `tests/test_snappy.py`, `tests/test_lzo.py`
- No API change; memory behavior improves for compressed inputs.
