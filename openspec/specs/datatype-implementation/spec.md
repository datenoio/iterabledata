# datatype-implementation Specification

## Purpose
TBD - created by archiving change fix-datatypes-implementation-issues. Update Purpose after archive.
## Requirements
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

### Requirement: Truthful Streaming Declaration

Every datatype implementation SHALL declare its memory behavior explicitly via `is_streaming()`: implementations whose read path is genuinely incremental (peak memory bounded by record/batch size, not file size) SHALL return `True`, and implementations that materialize the whole file or table during `reset()` or iteration SHALL return `False` and document this in the class docstring. The capability API SHALL report this declaration instead of `None` for built-in formats whose behavior is known.

#### Scenario: Streaming reader declares True

- **WHEN** `get_format_capabilities()` is queried for a format whose reader is incremental (e.g. ORC, Avro, BSON, MessagePack, PCAP, SQLite)
- **THEN** the `streaming` capability SHALL be `True`
- **AND** `is_streaming()` on an instance SHALL return `True`

#### Scenario: Full-load reader declares False

- **WHEN** `get_format_capabilities()` is queried for a format that materializes the entire input (e.g. Arrow/Feather, Lance, Delta, Iceberg, Hudi, Shapefile, CBOR, YAML, TOML)
- **THEN** the `streaming` capability SHALL be `False`
- **AND** the class docstring SHALL state that the whole file or table is loaded into memory

#### Scenario: New formats must declare deliberately

- **WHEN** the streaming-declaration conformance test runs against a registered built-in format missing from the reviewed allowlist
- **THEN** the test SHALL fail
- **AND** the failure message SHALL instruct the author to classify the format's memory behavior

### Requirement: Batch-Iterating Readers for Columnar and Record Sources

Datatype implementations whose underlying libraries expose batch or record iterators (Arrow/Feather, Lance, Delta, Iceberg, Shapefile, XLSX) SHALL read through those incremental APIs rather than materializing the whole file or table during `reset()`. Where an underlying library offers no incremental API, the implementation SHALL document the full-load behavior in its class docstring and declare `is_streaming()` as `False`.

#### Scenario: Shapefile iterates lazily

- **WHEN** a large shapefile is opened and the first record is read
- **THEN** only the shapes required so far SHALL have been parsed
- **AND** peak memory SHALL be bounded by record size, not feature count

#### Scenario: Columnar formats read by batch

- **WHEN** an Arrow, Lance, Delta, or Iceberg source is iterated
- **THEN** data SHALL be fetched via the library's batch iterator
- **AND** `read_bulk()` SHALL map to the underlying batch API where available

#### Scenario: Records are unchanged by the conversion

- **WHEN** an existing fixture is read with the batch-iterating implementation
- **THEN** the yielded records SHALL be identical (content and, where the format guarantees it, order) to the previous full-load implementation

### Requirement: Unified Row and Bulk Cursor Semantics

Every datatype that implements both `read()` and `read_bulk()` SHALL advance one logical cursor. Any interleaving of the two methods SHALL yield each source record exactly once and in source order, unless the user explicitly calls `reset()`.

#### Scenario: Row read followed by bulk read

- **WHEN** a user reads one record with `read()` and then calls `read_bulk(2)`
- **THEN** the bulk result SHALL contain the next two records
- **AND** it SHALL NOT repeat the record returned by `read()`

#### Scenario: Bulk read followed by row read

- **WHEN** a user calls `read_bulk(n)` and then calls `read()`
- **THEN** `read()` SHALL return the record immediately following the bulk result
- **AND** no record SHALL be skipped

#### Scenario: Reset restores the initial cursor

- **WHEN** row and bulk reads have advanced the iterable and the user calls `reset()`
- **THEN** the next read SHALL return the first record again
- **AND** all backend and remainder cursor state SHALL be cleared

### Requirement: Bounded Incremental Writers

Writable formats that declare bounded write memory SHALL flush records at a configurable batch or row-group boundary and SHALL NOT retain the complete output dataset until close. Formats whose backend cannot append incrementally SHALL declare whole-output memory behavior explicitly.

#### Scenario: Parquet row writes form bounded row groups

- **WHEN** records are supplied one at a time to a Parquet writer
- **THEN** records SHALL be accumulated into bounded row groups
- **AND** writer creation SHALL NOT cause each later record to become its own row group

#### Scenario: Arrow or Lance writes exceed one batch

- **WHEN** more records than the configured write batch size are written to Arrow or Lance
- **THEN** completed batches SHALL be flushed incrementally
- **AND** peak retained records SHALL remain proportional to the configured batch size

#### Scenario: Backend requires whole-output buffering

- **WHEN** a format backend cannot safely append or stream its output
- **THEN** the implementation SHALL declare whole-output write memory behavior
- **AND** the format documentation SHALL state the limitation

### Requirement: Low-Overhead Success Paths

Streaming text readers SHALL preserve actionable parse-error context without performing avoidable seek/tell or equivalent decoder-position work for every valid record.

#### Scenario: JSONL bulk read of valid input

- **WHEN** a valid JSONL file is read with `read_bulk()`
- **THEN** the reader SHALL parse lines incrementally without a successful `tell()` call per line
- **AND** line numbers SHALL remain available for any later parse error

#### Scenario: Malformed text record

- **WHEN** a text record cannot be parsed
- **THEN** the raised error SHALL include the format, filename when available, and record or line number
- **AND** byte offset MAY be omitted when the active stream cannot provide it cheaply or correctly

### Requirement: CSV Dialect Options From Iterable Arguments

`CSVIterable` SHALL apply `delimiter`, `quotechar`, `escapechar`, `doublequote`, `keys` and `autodetect` supplied through `options` (and therefore through `open_iterable(iterableargs=...)`) to both reading and writing. An explicit constructor argument SHALL take precedence over `options`, and `options` SHALL take precedence over extension defaults and autodetection.

#### Scenario: Semicolon delimiter through open_iterable

- **WHEN** a user opens `a.csv` containing `a;b\n1;2\n` with `iterableargs={"delimiter": ";"}`
- **THEN** the reader SHALL return `{"a": "1", "b": "2"}`

#### Scenario: Tab delimiter on write

- **WHEN** a user writes `{"a": 1, "b": 2}` to `o.csv` with `iterableargs={"delimiter": "\t"}`
- **THEN** the file SHALL contain `a\tb` and `1\t2`

### Requirement: Tab-Separated Defaults

Files detected as `tsv` SHALL use a tab delimiter by default for reading and writing.

#### Scenario: Reading a TSV file without options

- **WHEN** a user opens `t.tsv` containing `a,b\tc\n1,2\t3\n` without options
- **THEN** the reader SHALL return `{"a,b": "1,2", "c": "3"}`

#### Scenario: Writing a compressed TSV file

- **WHEN** a user writes records to `out.tsv.gz`
- **THEN** the decompressed output SHALL be tab-separated

### Requirement: CSV Totals Exclude the Header

`CSVIterable.totals()` SHALL NOT count the header line as a record.

#### Scenario: Two data rows

- **WHEN** a CSV file has one header line and two single-line data rows
- **THEN** `totals()` SHALL return `2`

