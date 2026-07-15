# TAR Format (Multi-File Container)

## Description

TAR is the ubiquitous archive container used to package datasets (`.tar`, `.tar.gz`, `.tar.zst`, ...). The `tar` format treats a tarball as a container of data files: it iterates the archive members in order, detects each member's format from its name (CSV, JSONL, Parquet, compressed members like `.csv.gz`, etc.), and yields that member's records. Every record is tagged with the originating member name.

Members are read as in-memory streams directly from the archive — nothing is ever extracted to disk.

## File Extensions

- `.tar` - plain TAR archive
- `.tar.gz` / `.tgz` - gzip-compressed
- `.tar.bz2` - bzip2-compressed
- `.tar.xz` - LZMA-compressed
- `.tar.zst` - ZStandard-compressed (requires the `[compression]` extra)

## Implementation Details

### Reading

- Uses the standard library `tarfile`; no extra dependencies for plain/gz/bz2/xz
- Members are visited in archive order and streamed one at a time
- Each member's format is detected from its filename and delegated to that format's reader
- Compressed members (e.g. `data.csv.gz` inside the tar) are decompressed via the matching codec
- Members whose format cannot be detected (e.g. READMEs) are skipped
- Records are tagged with the member name under the `_member` key (configurable)

### Writing

Writing is not supported; the TAR container is read-only.

### Safety

- Members with absolute paths or `..` traversal components are skipped with a warning
- No member content is ever written to the filesystem

## Usage

```python
from iterable.helpers.detect import open_iterable

# Iterate all data members
with open_iterable('dataset.tar.gz') as source:
    for row in source:
        print(row['_member'], row)

# Read only specific members (exact name or glob)
with open_iterable('dataset.tar', iterableargs={'members': '*.jsonl'}) as source:
    for row in source:
        ...

# Change or disable the member tag
with open_iterable('dataset.tar', iterableargs={'member_key': '_src'}) as source:
    ...
with open_iterable('dataset.tar', iterableargs={'member_key': None}) as source:
    ...
```

## Parameters

- `members` (str | list[str]): Exact member name(s) or glob pattern(s) to read. Default: all data members
- `member_key` (str | None): Record key holding the member name (default: `_member`; `None` disables tagging)
- `encoding` (str): Text encoding for text members (default: `utf8`)

## Limitations

1. **Read-only**: Writing TAR archives is not supported
2. **Member order**: Members are read strictly in archive order (stream-friendly)
3. **Undetected members are skipped**: Only members with recognizable data formats are read

## Related Formats

- [ZIP XML](zipxml.md) - XML inside ZIP archives
- [Parquet](parquet.md), [CSV](csv.md), [JSON Lines](jsonl.md) - typical member formats
