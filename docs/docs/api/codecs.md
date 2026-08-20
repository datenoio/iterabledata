---
sidebar_position: 12
title: Compression Codecs
description: Gzip, Brotli, Zstandard, 7z, and codec performance profiles
---

# Compression codecs

IterableData detects compression from the filename (and, when needed, from content) and wraps the underlying format reader or writer. You usually pass a path such as `data.jsonl.gz` to `open_iterable()`; you do not construct codec classes unless you need a custom stream.

Install optional codecs with:

```bash
pip install 'iterabledata[compression]'
```

Gzip, bzip2, LZMA/xz, and ZIP use the standard library and do not require the extra.

## Codec catalog

| Codec | Extensions | Extra | Notes |
|-------|------------|-------|-------|
| Gzip | `.gz` | (stdlib) | Default profile level 6 |
| Bzip2 | `.bz2` | (stdlib) | |
| LZMA | `.xz`, `.lzma` | (stdlib) | |
| ZIP | `.zip` | (stdlib) | Reads the first member by default |
| LZ4 | `.lz4` | `[compression]` | |
| Brotli | `.br` | `[compression]` | |
| Zstandard | `.zst`, `.zstd` | `[compression]` | DuckDB engine supports zstd |
| Snappy | `.snappy`, `.sz` | `[compression]` | Fixed compression level. Framed streams are bounded; legacy raw blobs buffer the whole input |
| LZO | `.lzo`, `.lzop` | `[compression]` | Writes `ILZO1` block framing (not the `lzop` container). Legacy raw LZO remains readable with full buffering |
| 7-Zip | `.7z` | `[compression]` (`py7zr`) | Opens the first archive member |

The DuckDB engine only supports **gzip** and **zstd** codecs. Use `engine="internal"` (the default) for other codecs and for [cloud storage](/api/cloud-storage).

## Usage

```python
from iterable import open_iterable

with open_iterable("data.csv.gz") as source:
    for row in source:
        print(row)

with open_iterable("out.jsonl.zst", mode="w") as dest:
    dest.write_bulk([{"id": 1}, {"id": 2}])
```

## Compression profiles

Codec constructors accept `options={"profile": "fast" | "balanced" | "max"}`.
The high-level default is `balanced`; an explicit `compression_level` always
overrides the profile. Effective settings are available on codec instances as
`effective_settings` for diagnostics.

| Profile | Goal | Typical settings |
| --- | --- | --- |
| `fast` | Lowest CPU cost | gzip 1, zstd 1, Brotli 1 |
| `balanced` | General ETL default | gzip 6, zstd 3, Brotli 5 |
| `max` | Highest ratio | gzip 9, zstd 19, Brotli 11 |

```python
from iterable.codecs.gzipcodec import GZIPCodec

codec = GZIPCodec("data.csv.gz", options={"profile": "fast"})
print(codec.effective_settings)
```

See [Performance](/getting-started/performance) for when compression helps or hurts throughput.
