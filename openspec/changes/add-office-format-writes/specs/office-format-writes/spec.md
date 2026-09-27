# Spec Delta: office-format-writes

## ADDED Requirements

### Requirement: XLSX write support

The XLSX format SHALL support `write()` and `write_bulk()` through openpyxl,
buffering rows and materializing the workbook on `close()`.

#### Scenario: Write and read back records

- **WHEN** records are written with `mode="w"` and the iterable is closed
- **THEN** the produced `.xlsx` file opens with openpyxl and the format's own
  reader yields the same records (with typed values preserved where the format
  supports them)

#### Scenario: Missing dependency

- **WHEN** openpyxl is not installed and a write is attempted
- **THEN** an `ImportError` with an install hint is raised

### Requirement: XML write support

The XML format SHALL support `write()` and `write_bulk()`, emitting one
`<tagname>` element per record under a root element, honoring the configured
`tagname`.

#### Scenario: Round-trip honors tagname

- **WHEN** records are written with `iterableargs={"tagname": "item"}` and read
  back with the same tagname
- **THEN** the reader yields the same records

#### Scenario: Nested structures follow reader conventions

- **WHEN** a record contains nested dicts or lists
- **THEN** the written XML uses the same flattening conventions the reader
  applies, so round-trip equality holds

### Requirement: ODS write support

The ODS format SHALL support `write()` and `write_bulk()` through odfpy,
replacing the current `WriteNotSupportedError` stubs.

#### Scenario: Write and read back records

- **WHEN** records are written with `mode="w"` and the iterable is closed
- **THEN** the produced `.ods` file loads with odfpy and the format's own
  reader yields the same records with typed cells preserved

### Requirement: Registry and capability consistency

The format registry SHALL mark xlsx, xml, and ods as writable, and their
memory-profile descriptors SHALL record that writing buffers the full document.

#### Scenario: Descriptor truthfulness

- **WHEN** capability metadata is computed for xlsx, xml, or ods
- **THEN** `writable` is true, the write memory profile is full-buffer, and the
  descriptor-driven capability conformance tests pass
