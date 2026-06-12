## ADDED Requirements

### Requirement: CBOR File Reading
The system SHALL support reading Concise Binary Object Representation (CBOR, RFC 8949) data and yielding decoded items as Python objects (e.g. dicts or lists), supporting single top-level items and CBOR sequences where applicable.

#### Scenario: Read CBOR file with automatic detection
- **WHEN** using `open_iterable` on a `.cbor` (or configured CBOR) file
- **THEN** it automatically selects `CBORIterable` for processing

#### Scenario: Read CBOR array or sequence as records
- **WHEN** reading a CBOR file whose top-level value is an array or a CBOR sequence of items
- **THEN** it yields one record per array element or sequence item (e.g. dicts for map items)

#### Scenario: Read single CBOR map as one record
- **WHEN** reading a CBOR file whose top-level value is a single map
- **THEN** it yields one record representing that map (e.g. a single dict)

#### Scenario: Handle missing CBOR dependency
- **WHEN** the CBOR library (e.g. `cbor2`) is not installed
- **THEN** it raises an `ImportError` with a clear message instructing installation of `iterabledata[cbor]`
