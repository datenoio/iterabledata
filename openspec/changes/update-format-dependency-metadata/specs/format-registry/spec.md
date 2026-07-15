## ADDED Requirements

### Requirement: Resolvable Dependency Extras

Every format descriptor whose implementation requires an optional third-party package SHALL map to an optional-dependency extra declared in `pyproject.toml` that installs the required package(s), and the install hint reported on `ImportError` SHALL name that extra. The `all` extra SHALL include every pip-installable optional dependency referenced by any format extra.

#### Scenario: Install hint resolves to a real extra

- **WHEN** opening a format whose optional dependency is not installed raises `ImportError`
- **THEN** the error message SHALL name an extra that exists in `pyproject.toml`
- **AND** installing that extra SHALL provide the package(s) the format module imports

#### Scenario: Lakehouse formats are installable

- **WHEN** a user installs the extra named in the install hint for `delta`, `iceberg`, or `lance`
- **THEN** the corresponding format module SHALL import successfully
- **AND** the hint SHALL NOT point at an extra (such as `parquet`) that does not include the format's required package

#### Scenario: The all extra is complete

- **WHEN** a user installs `iterabledata[all]`
- **THEN** every pip-installable package referenced by any format or codec extra SHALL be installed
- **AND** no registered format SHALL raise `ImportError` for a package that is available on PyPI

### Requirement: Descriptor Metadata Consistency

LLM-oriented descriptor metadata (descriptions, limitations) and format documentation pages SHALL be consistent with the descriptor's capability flags and the implementation. A descriptor with `writable=True` SHALL NOT carry metadata or documentation stating the format is read-only.

#### Scenario: Writable format metadata does not claim read-only

- **WHEN** a descriptor declares `writable=True`
- **THEN** its `limitations` metadata SHALL NOT contain a read-only claim
- **AND** the corresponding page under `docs/docs/formats/` SHALL NOT state that writing is unsupported
