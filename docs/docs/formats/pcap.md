---
title: PCAP Format
description: PCAP format support in IterableData
---

# PCAP Format

> Registry-generated stub. Expand with parameters, examples, and limitations.

## Overview

| Property | Value |
|----------|-------|
| Format id | `pcap` |
| Class | `PCAPIterable` |
| Extensions | `.pcap`, `.pcapng` |
| Text format | No |
| Flat rows | No |
| Read | Yes |
| Write | No |

## Usage

```python
from iterable.helpers.detect import open_iterable

with open_iterable("data.pcap") as source:
    for row in source:
        print(row)
```

## Installation

```bash
pip install 'iterabledata[pcap]'
```

## See also

- [Supported formats](/formats/)
