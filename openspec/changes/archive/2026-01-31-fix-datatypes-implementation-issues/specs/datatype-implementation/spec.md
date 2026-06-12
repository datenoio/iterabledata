# datatype-implementation (delta)

## ADDED Requirements

### Requirement: Row Type Import in Datatype Modules
Every datatype module that uses the `Row` type alias in method signatures (e.g. `write(record: Row)` or `write_bulk(records: list[Row])`) SHALL import `Row` from `iterable.types` so that type checkers (mypy, pyright) can resolve the type and do not report undefined-name errors.

#### Scenario: Type checker resolves Row in write signature
- **WHEN** a type checker processes a datatype module that defines `def write(self, record: Row) -> None` or `def write_bulk(self, records: list[Row]) -> None`
- **THEN** the module SHALL contain `from ..types import Row` (or equivalent)
- **AND** the type checker SHALL not report `Row` as undefined

#### Scenario: Mypy passes on datatypes directory
- **WHEN** `mypy iterable/datatypes` is run
- **THEN** no errors SHALL be reported for undefined name `Row` in any datatype module

### Requirement: Filename-Only Format Source Validation
Formats that require a file path and do not support stream or codec as a source (e.g. DBF, shapefile, sqlite, mbox, xlsb) SHALL validate in `__init__` or at the start of `reset()` that a filename is available. If the user provides only a stream or codec (so that `filename` is None), the implementation SHALL raise a clear error (e.g. `ValueError` or `ReadError`) with a message indicating that the format requires a file path and that stream/codec is not supported, instead of failing later with a library-specific or confusing error.

#### Scenario: DBF with stream raises clear error
- **WHEN** user instantiates DBFIterable with only a stream (no filename)
- **THEN** the implementation SHALL raise an error (e.g. ValueError or ReadError) with a message that DBF requires a file path
- **AND** the error SHALL occur at construction or at first use (e.g. reset()), not as an opaque failure inside the underlying library

#### Scenario: Filename-only format with filename succeeds
- **WHEN** user instantiates a filename-only format (e.g. DBF) with a valid filename
- **THEN** the iterable SHALL open and read as usual
- **AND** no spurious validation error SHALL be raised

### Requirement: read_bulk Exhaustion Returns Empty List
Implementations of `read_bulk()` SHALL return an empty list `[]` when no more records are available, and SHALL NOT raise `StopIteration` to signal exhaustion. This allows callers to use patterns such as `while chunk := it.read_bulk(100): ...` and ensures consistent behavior across all datatype implementations.

#### Scenario: read_bulk at end of data returns empty list
- **WHEN** the iterable has no more records and the user calls `read_bulk(n)`
- **THEN** the method SHALL return `[]`
- **AND** the method SHALL NOT raise StopIteration

#### Scenario: read_bulk returns partial chunk then empty list
- **WHEN** the iterable has fewer than n records remaining and the user calls `read_bulk(n)`
- **THEN** the first call SHALL return the remaining records (e.g. a list of length less than n)
- **AND** the next call to `read_bulk(n)` SHALL return `[]`

### Requirement: Correct Docstrings for Read/Write Methods
Datatype implementations SHALL use correct docstrings for `read()` and `write()` methods. A method named `read()` SHALL have a docstring that describes reading (e.g. "Read single X record"); a method named `write()` SHALL have a docstring that describes writing (e.g. "Write single X record"). Incorrect labels (e.g. "Write" on a read method) SHALL be fixed.

#### Scenario: read method docstring describes reading
- **WHEN** a datatype implements `read(self, ...)`
- **THEN** its docstring SHALL describe reading a record (e.g. "Read single ... record")
- **AND** the docstring SHALL NOT describe writing

#### Scenario: write method docstring describes writing
- **WHEN** a datatype implements `write(self, record, ...)`
- **THEN** its docstring SHALL describe writing a record (e.g. "Write single ... record")
- **AND** the docstring SHALL NOT describe reading
