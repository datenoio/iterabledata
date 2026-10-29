## ADDED Requirements

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
