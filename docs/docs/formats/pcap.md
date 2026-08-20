---
title: PCAP Format
description: PCAP/PCAP-NG packet captures in IterableData
---

# PCAP Format

Stream PCAP / PCAP-NG packet captures as timestamped raw frames. PCAP is **read-only** in this release.

## Overview

| Property | Value |
|----------|-------|
| Format id | `pcap` (alias `pcapng`) |
| Class | `PCAPIterable` |
| Extensions | `.pcap`, `.pcapng` |
| Read | Yes |
| Write | No |
| Extra | `pcap` (`dpkt`) |
| Maturity | stable |

## File Extensions

- `.pcap` — classic libpcap captures
- `.pcapng` — PCAP Next Generation

## Implementation Details

### Reading

- Decodes packets incrementally via `dpkt` (streaming; the file is not fully loaded)
- Auto-detects classic PCAP vs PCAP-NG (tries `dpkt.pcap.Reader`, then `dpkt.pcapng.Reader`)
- Each row is `{"timestamp": float, "data": bytes}`

### Writing

Writing is not supported. `write()` / `write_bulk()` raise `WriteNotSupportedError`.

### Key Features

- **Streaming**: one packet at a time
- **Dual format**: classic PCAP and PCAP-NG
- **Raw frames**: payload bytes preserved for further decoding

## Usage

```python
from iterable import open_iterable

with open_iterable("capture.pcap") as source:
    for pkt in source:
        print(pkt["timestamp"], len(pkt["data"]))

with open_iterable("capture.pcapng", format="pcap") as source:
    for pkt in source:
        print(pkt["timestamp"], pkt["data"][:16])
```

## Parameters

No format-specific `iterableargs`. Standard open options (codec, encoding) still apply when relevant.

| Parameter | Type | Default | Required | Description |
|-----------|------|---------|----------|-------------|
| *(none)* | — | — | — | No format-specific parameters |

## Error Handling

- **ImportError**: Missing `dpkt` — install with `pip install iterabledata[pcap]`
- **WriteNotSupportedError**: Writing PCAP is not implemented
- **ValueError**: File object is not open when reading
- **FileNotFoundError**: Path is wrong or the file is missing
- Corrupt or truncated captures may raise `dpkt` / parse errors during iteration

See [Troubleshooting](/getting-started/troubleshooting) for more help.

## Installation

```bash
pip install 'iterabledata[pcap]'
```

## Limitations

1. **Read-only**
2. **Requires dpkt**
3. **Raw frames only** — no protocol dissection beyond timestamp + bytes

## Related Formats

- [Supported formats](/formats/)
