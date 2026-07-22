## ADDED Requirements

### Requirement: SEG-Y Format Support

The system SHALL support reading SEG-Y seismic files as an iterable of trace records with documented headers and sample payloads.

#### Scenario: Read SEG-Y traces

- **WHEN** a valid SEG-Y file is opened via `open_iterable`
- **THEN** the system SHALL yield one record per trace
- **AND** each record SHALL include documented header fields and sample data according to the chosen mode

#### Scenario: Missing SEG-Y dependency

- **WHEN** SEG-Y support is requested without its optional dependency
- **THEN** the system SHALL raise an `ImportError` with installation instructions for the correct extra

### Requirement: GRIB2 Format Support

The system SHALL support reading GRIB2 files as an iterable of message records without requiring all messages to be decoded before iteration starts.

#### Scenario: Read GRIB2 messages

- **WHEN** a valid GRIB2 file is opened via `open_iterable`
- **THEN** the system SHALL yield one record per message with documented identifying keys and values

#### Scenario: Missing GRIB dependency

- **WHEN** GRIB2 support is requested without its optional dependency
- **THEN** the system SHALL raise an `ImportError` with installation instructions for the correct extra

### Requirement: miniSEED Format Support

The system SHALL support reading miniSEED waveform files as iterable window/trace records.

#### Scenario: Read miniSEED windows

- **WHEN** a valid `.mseed` file is opened via `open_iterable`
- **THEN** the system SHALL yield records including station/channel timing metadata and sample data as documented

#### Scenario: Compressed miniSEED

- **WHEN** a miniSEED file is compressed with a supported codec extension
- **THEN** detection SHALL compose codec + miniSEED datatype consistently with other formats
