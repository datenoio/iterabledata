# Change: Add Support for Common Data Format (CDF) and Concise Binary Object Representation (CBOR)

## Why
Users need to process NASA Common Data Format (CDF) files common in space and solar physics, and CBOR (RFC 8949) binary data used in IoT, COSE, and compact interchange. Adding support for these formats extends IterableData to scientific/space data pipelines and binary-serialization workflows without loading entire datasets into memory.

## What Changes
- **Dependencies**
    - Add `spacepy` (or equivalent) for CDF support, with clear documentation that the NASA CDF C library may be required.
    - Add `cbor2` for CBOR encode/decode.
    - Update `pyproject.toml` with optional extras (e.g. `cdf`, `cbor`).
- **New Iterables**
    - `iterable/datatypes/cdf.py`: Implement `CDFIterable` for reading CDF variables as record streams.
    - `iterable/datatypes/cbor.py`: Implement `CBORIterable` for reading CBOR sequences or arrays of records.
- **Detection**
    - Update `iterable/helpers/detect.py` to recognize `.cdf` for CDF and `.cbor` / `.cbors` (CBOR sequence) for CBOR.

## Impact
- **New capabilities**: `cdf-format`, `cbor-format`
- **Affected files**:
    - `pyproject.toml`
    - `iterable/helpers/detect.py`
    - `iterable/datatypes/cdf.py` (new)
    - `iterable/datatypes/cbor.py` (new)
