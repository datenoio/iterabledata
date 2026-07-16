# Compression profiles

Codec constructors accept `options={"profile": "fast" | "balanced" | "max"}`.
The high-level default is `balanced`; an explicit `compression_level` always
overrides the profile. Effective settings are available on codec instances as
`effective_settings` for diagnostics.

| Profile | Goal | Typical settings |
| --- | --- | --- |
| `fast` | Lowest CPU cost | gzip 1, zstd 1, Brotli 1 |
| `balanced` | General ETL default | gzip 6, zstd 3, Brotli 5 |
| `max` | Highest ratio | gzip 9, zstd 19, Brotli 11 |

Snappy has a fixed level. Its framed stream is bounded; legacy raw blobs are
read with a full-buffer compatibility path. LZO writes the library's `ILZO1`
block framing, which is intentionally not the `lzop` container; legacy raw LZO
files remain readable but require full buffering.
