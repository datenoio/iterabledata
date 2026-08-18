---
title: PCAP Format
description: PCAP/PCAP-NG packet captures in IterableData
---

# PCAP Format

Stream PCAP / PCAP-NG packet captures as timestamped raw frames.

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

## Record shape

```python
{"timestamp": 1700000000.123, "data": b"..."}
```

Packets are decoded incrementally (streaming). Auto-detects classic PCAP vs PCAP-NG.

## Usage

```python
from iterable import open_iterable

with open_iterable("capture.pcap") as source:
    for pkt in source:
        print(pkt["timestamp"], len(pkt["data"]))
```

Install with `pip install iterabledata[pcap]`.

## See also

- [Supported formats](/formats/)
