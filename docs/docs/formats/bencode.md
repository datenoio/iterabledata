# Bencode Format

## Description

Bencode (pronounced "B-encode") is the encoding format used by the BitTorrent protocol. It's a simple format for encoding data structures (strings, integers, lists, and dictionaries) in a compact binary format. Bencode is commonly used in .torrent files.

## File Extensions

- `.torrent` - BitTorrent files (uses Bencode)

## Implementation Details

### Reading

The Bencode implementation:
- Uses `bencode` or `bencodepy` library for decoding
- Parses Bencode-encoded data
- Handles torrent file structures
- Converts Bencode data to Python objects

### Writing

Writing support:
- Encodes Python objects to Bencode format
- Writes binary Bencode data
- Supports nested structures

### Key Features

- **BitTorrent format**: Used by BitTorrent protocol
- **Simple encoding**: Compact binary format
- **Nested data**: Supports lists and dictionaries
- **Type preservation**: Maintains data types

## Usage

```python
from iterable import open_iterable

# Basic reading
source = open_iterable('file.torrent')
for row in source:
    print(row)  # Contains torrent metadata
source.close()

# Writing
dest = open_iterable('output.torrent', mode='w')
dest.write({'info': {...}, 'announce': 'http://...'})
dest.close()
```

## Parameters

No specific parameters required.

## Limitations

1. **Dependency**: Requires `bencode` or `bencodepy` package
2. **Binary format**: Not human-readable
3. **BitTorrent-specific**: Primarily used for BitTorrent files
4. **Memory usage**: Entire file may be loaded into memory

## Compression Support

Bencode files can be compressed with all supported codecs:
- GZip (`.torrent.gz`)
- BZip2 (`.torrent.bz2`)
- LZMA (`.torrent.xz`)
- LZ4 (`.torrent.lz4`)
- ZIP (`.torrent.zip`)
- Brotli (`.torrent.br`)
- ZStandard (`.torrent.zst`)

Note: Torrent files are typically not compressed.

## Use Cases

- **BitTorrent**: Working with .torrent files
- **P2P protocols**: Peer-to-peer protocol data
- **File sharing**: BitTorrent file sharing

## Related Formats

- [JSON](json.md) - Similar structure, text-based
- [MessagePack](msgpack.md) - Another binary format
