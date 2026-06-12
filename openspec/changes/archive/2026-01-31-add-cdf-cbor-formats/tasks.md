# Tasks

- [x] Add dependencies to `pyproject.toml`
    - [x] `spacepy` (extra: `cdf`); document CDF C library requirement if applicable
    - [x] `cbor2` (extra: `cbor`)
- [x] Implement `CDFIterable`
    - [x] Create `iterable/datatypes/cdf.py`
    - [x] Register in `iterable/helpers/detect.py` (extension `.cdf`)
    - [x] Add tests in `tests/test_cdf.py`
- [x] Implement `CBORIterable`
    - [x] Create `iterable/datatypes/cbor.py` (already existed; added optional dep and error message)
    - [x] Register in `iterable/helpers/detect.py` (extensions `.cbor`, `.cbors`)
    - [x] Add tests in `tests/test_cbor.py` (already existed)
