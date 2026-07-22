# Change: Add Geophysical Formats (SEG-Y, GRIB2, miniSEED)

## Why

Geophysical open data frequently uses SEG-Y seismic (`segy`), GRIB2 weather (`grib2`), and miniSEED seismology (`.mseed`). These are high-confidence iterable gaps in Dateno stats and complement existing scientific array formats (NetCDF, HDF5) with domain-standard trace/message/stream semantics.

## What Changes

- Add SEG-Y trace reading with header fields + samples mapped to documented records.
- Add GRIB2 message reading as iterable weather messages/grids with documented field extraction.
- Add miniSEED reading as iterable waveform records/windows.
- Register formats, optional deps, fixtures, tests, and docs (read-oriented v1).

## Impact

- Affected specs: `geophysical-formats` (new)
- Affected code: new datatypes, registry/detection, optional extras, docs/tests
- New dependencies: optional domain libraries (e.g. `segyio`/`obspy`/`cfgrib`/`pygrib` families), kept out of core
