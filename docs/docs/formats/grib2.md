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

Install with `pip install iterabledata[geophysical]`.

## See also

- [NetCDF](/formats/nc) — gridded scientific data
- [SEG-Y](/formats/segy) — seismic traces
- [miniSEED](/formats/mseed) — seismological waveforms
- [Supported formats](/formats/)
