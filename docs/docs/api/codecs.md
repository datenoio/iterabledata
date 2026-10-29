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

### Listing codecs

`list_codecs()` returns every registered codec, including plugin codecs, without importing
any optional dependency:

```python
from iterable.helpers.detect import list_codecs

for codec in list_codecs():
    print(codec["id"], codec["class_name"], codec["source"])  # gz GZIPCodec builtin ...
```

Each entry has `id` (the extension that selects the codec), `module` and `class_name`
(where the class lives) and `source` (`"builtin"` or `"plugin"`). The `id` is also accepted
as `iterableargs={"codec": ...}`, together with the aliases `gzip`, `bzip2`, `zstandard`
and `brotli`.

`CODEC_REGISTRY`, `DATATYPE_REGISTRY` and `TEXT_DATA_TYPES` in `iterable.helpers.detect`
are read-only views of the built-in metadata and do not include plugins. Use
`list_codecs()` and [`iterable.catalog`](/api/catalog) (`list_formats()`,
`describe_format()`) instead of reading or changing them.

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
`effective_settings` for diagnostics. Pass the same options through
`open_iterable(..., codecargs=...)` or `convert(..., codecargs=..., tocodecargs=...)`.

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
