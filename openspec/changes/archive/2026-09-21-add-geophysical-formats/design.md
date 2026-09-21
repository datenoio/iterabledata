## Context

SEG-Y, GRIB2, and miniSEED are binary domain formats where "a row" is a trace, message, or waveform window rather than a tabular spreadsheet row. IterableData should expose stable dict records and push heavy decoding to optional backends.

## Goals / Non-Goals

- Goals:
  - Stream traces/messages/windows with bounded memory.
  - Preserve key headers needed for downstream conversion.
- Non-Goals:
  - Full seismic processing, NWP model I/O suites, or write-round-trips for every revision in v1.
  - Automatic resampling/regridding.

## Decisions

### SEG-Y

One record per trace: textual/binary header subset + `samples` array (or deferred sample access mode). Support common endianness/revision detection via backend.

### GRIB2

One record per message with keys such as shortName/level/time and either flattened values or a documented values reference. Large grids MUST stream message-by-message.

### miniSEED

One record per continuous window/tracelet with station/channel/starttime/sampling_rate/data. Compose with existing codecs when files are `.mseed.gz`.

## Risks / Trade-offs

- Optional deps are heavy → separate extras (`seismic`, `grib`, `seismo`) or one `geophysical` extra.
- Sample arrays can dominate memory → document bulk APIs and optional sample omission.

## Migration Plan

Experimental read-only first. Enable writes only with golden round-trip fixtures.

## Open Questions

- Single `geophysical` extra vs per-format extras?
- Default SEG-Y record: inline samples vs header-only with lazy sample fetch?
