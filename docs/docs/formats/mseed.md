---
title: miniSEED Format
description: miniSEED seismological waveforms in IterableData
---

# miniSEED Format

Read miniSEED seismological waveform files as one trace window per record.

## Overview

| Property | Value |
|----------|-------|
| Format id | `mseed` (alias `miniseed`) |
| Class | `MiniSEEDIterable` |
| Extensions | `.mseed` |
| Read | Yes |
| Write | No |
| Extra | `geophysical` (`obspy`) |
| Maturity | experimental |

## Record shape

```python
{
    "station": "ANMO",
    "channel": "BHZ",
    "starttime": "2024-01-01T00:00:00.000000Z",
    "sampling_rate": 40.0,
    "data": [...],
    "network": "IU",
    "location": "00",
}
```

`network` and `location` may be `None`. All traces are loaded into memory via ObsPy.

## Usage

```python
from iterable import open_iterable

with open_iterable("station.mseed", format="mseed") as source:
    for trace in source:
        print(trace["station"], trace["channel"], trace["sampling_rate"], len(trace["data"]))
```

Install with `pip install iterabledata[geophysical]`.

## See also

- [SEG-Y](/formats/segy) — seismic traces
- [GRIB2](/formats/grib2) — meteorological messages
- [Supported formats](/formats/)
