---
title: GRIB2 Format
description: GRIB2 meteorological messages in IterableData
---

# GRIB2 Format

Read GRIB2 meteorological messages as dictionaries (one message per record).

## Overview

| Property | Value |
|----------|-------|
| Format id | `grib2` (alias `grib`) |
| Class | `GRIB2Iterable` |
| Extensions | `.grib2`, `.grb2`, `.grib` |
| Read | Yes |
| Write | No |
| Extra | `geophysical` |
| Maturity | experimental |

## Record shape

Backend-dependent. Records always include `shortName` and `values`. With cfgrib, coordinates such as `time`, `step`, `level`, `latitude`, and `longitude` may also appear.

Backend preference: cfgrib (+ xarray) → pygrib → eccodes. All messages are loaded into memory; a filename path is required.

## Usage

```python
from iterable import open_iterable

with open_iterable("forecast.grib2", format="grib2") as source:
    for msg in source:
        print(msg["shortName"], len(msg["values"]))
```

Install with `pip install iterabledata[geophysical]`, or install a backend directly (`cfgrib` + `xarray`, `pygrib`, or `eccodes`).

## Parameters

No format-specific `iterableargs`. A filesystem path is required (streams and codecs are not supported). Backend preference: cfgrib + xarray → pygrib → eccodes.

## Error Handling

- **Missing dependency**: optional libraries raise `ImportError` with an install hint (`pip install 'iterabledata[<extra>]'` when an extra exists).
- **Read-only**: opening with `mode="w"` raises `WriteNotSupportedError` or `ValueError`.
- **Bad or unsupported input**: may raise `ValueError`, `OSError`, or library-specific errors.
- See [Troubleshooting](/getting-started/troubleshooting) for decoding, detection, and engine issues.

## See also

- [NetCDF](/formats/nc) — gridded scientific data
- [SEG-Y](/formats/segy) — seismic traces
- [miniSEED](/formats/mseed) — seismological waveforms
- [Supported formats](/formats/)
