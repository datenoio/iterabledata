---
title: miniSEED Format
description: miniSEED seismological waveforms in IterableData
---

# miniSEED Format

## Description

miniSEED is a compact binary format for continuous seismological time-series (waveforms). IterableData reads files with ObsPy and yields one record per trace. It is **read-only**, **experimental**, and registered under the `geophysical` extra. Aliases: `miniseed`.

## File Extensions

- `.mseed` — miniSEED
- `.miniseed` — alias

## Implementation Details

### Reading

- Uses `obspy.read(..., format="MSEED")`
- Prefers a filename; stream/codec input is buffered to bytes then parsed
- Each row: `station`, `channel`, `starttime`, `sampling_rate`, `data` (sample list), plus optional `network`, `location`
- Loads all traces into memory before iteration (`is_streaming()` is `False`)

### Writing

Writing is not supported (`WriteNotSupportedError`).

### Key Features

- **Trace-oriented rows**: one waveform segment per record
- **ObsPy backed**: standard seismology stack
- **Sample arrays** as Python lists

## Usage

```python
from iterable import open_iterable

with open_iterable("event.mseed") as source:
    for tr in source:
        print(tr["station"], tr["channel"], tr["starttime"], len(tr["data"]))
```

## Parameters

No format-specific `iterableargs`.

## Installation

```bash
pip install 'iterabledata[geophysical]'
```

Requires `obspy` (included in the `geophysical` extra).

## Limitations

1. **Read-only**
2. **Memory**: all traces (including sample arrays) loaded up front
3. **Experimental** maturity
4. **Requires obspy**
5. Large continuous archives may be memory-heavy

## Error Handling

- **ImportError**: missing `obspy` — install `iterabledata[geophysical]`
- **WriteNotSupportedError**: write mode or `write()` / `write_bulk()`
- **ReadError**: no filename, stream, or codec provided
- **I/O / ObsPy errors**: corrupt miniSEED or missing files

## Related Formats

- [SEG-Y](segy.md) — seismic traces
- [GRIB2](grib2.md) — meteorological messages
- [NetCDF](nc.md) — array-oriented scientific data
