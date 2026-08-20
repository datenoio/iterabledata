---
title: SEG-Y Format
description: SEG-Y seismic traces in IterableData
---

# SEG-Y Format

Stream SEG-Y seismic volumes as one trace per record.

## Overview

| Property | Value |
|----------|-------|
| Format id | `segy` |
| Class | `SEGYIterable` |
| Extensions | `.segy`, `.sgy` |
| Read | Yes |
| Write | No |
| Extra | `geophysical` (`segyio`) |
| Maturity | experimental |

## Record shape

```python
{
    "trace_index": 0,
    "samples": [...],
    "inline": 100,
    "crossline": 200,
}
```

`inline` / `crossline` may be absent depending on geometry headers.

## Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `ignore_geometry` | `True` | Passed to `segyio.open()` |

Requires a filename. Streaming one trace at a time.

## Usage

```python
from iterable import open_iterable

with open_iterable("volume.segy", format="segy") as source:
    for trace in source:
        print(trace["trace_index"], len(trace["samples"]))
```

Install with `pip install iterabledata[geophysical]`.


## Error Handling

- **Missing dependency**: optional libraries raise `ImportError` with an install hint (`pip install 'iterabledata[<extra>]'` when an extra exists).
- **Read-only**: opening with `mode="w"` raises `WriteNotSupportedError` or `ValueError`.
- **Bad or unsupported input**: may raise `ValueError`, `OSError`, or library-specific errors.
- See [Troubleshooting](/getting-started/troubleshooting) for decoding, detection, and engine issues.

## See also

- [miniSEED](/formats/mseed) — seismological waveforms
- [GRIB2](/formats/grib2) — meteorological messages
- [Supported formats](/formats/)
