# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).


## [Unreleased]

## [1.0.15] - 2026-07-04

### Fixed
- **Bare install importability**: `import iterable` no longer requires optional `bson` or `pydantic` dependencies. BSON schema type handling is now optional, and AI block Pydantic models are loaded only when structured AI block output is used. Fixes [#13](https://github.com/datenoio/iterabledata/issues/13).

## [1.0.14] - 2026-06-26

### Added
- **Avro write support**: `AVROIterable` is now writable (previously read-only). Adds `write()`, `write_bulk()`, and `read_bulk()`, with lazy schema inference from the first record when no explicit `schema`/`keys` are supplied (mirroring the ORC writer). Values are coerced to an all-nullable-string schema (`["null", "string"]`) so heterogeneous and missing values round-trip, field names are validated against Avro naming rules with an actionable error, and the Avro codec is configurable via `compression`/`codec` (defaulting to the dependency-free `deflate`). New `fields_to_avro_schema()` helper. The `avro` format descriptor is now marked writable in `format_registry.py`. See `tests/test_avro.py`.

### Changed
- **ORC robust schema inference**: The ORC writer now defers writer creation until the first record and infers field names from it when no `schema`/`keys` are given. Inferred schemas are built via `pyorc.Struct(**fields)` instead of a `struct<...>` string, so columns whose names contain spaces, commas, colons, or non-ASCII characters are written correctly. `write_bulk([])` is a no-op. See `tests/test_orc.py`.
- **DuckDB/SQLite default table naming**: When writing to a `.ddb`/`.duckdb` or `.sqlite`/`.db` file without an explicit `table`, the target table name is now derived (and SQL-sanitized) from the output filename. Generic conversions such as `convert(src, "data.ddb")` / `convert(src, "data.sqlite")` work without extra configuration. See `tests/test_duckdb.py` and `tests/test_sqlite.py`.
- **Lance import diagnostics**: Lance read/write now fails fast with an actionable error (`_require_lance()`) when the genuine `pylance` library is missing or when the unrelated PyPI package named `lance` shadows it on import, instead of surfacing a cryptic `AttributeError` later.

## [1.0.13] - 2026-06-25

### Added
- **Block-based AI documentation**: New `ai.doc.generate_blocks()` produces structured, machine-readable documentation as independent blocks (`general`, `schema`, `quality`, `examples`, `statistics`, `codebook`) returning `{source, blocks{name:{markdown,data}}, full_document_markdown}`. Backed by a block registry (`iterable/ai/blocks.py`); `lineage` and `geo_coverage` are registered but deferred. `ai.doc.generate()` remains fully backward compatible and delegates to the block engine. See OpenSpec change `add-ai-block-documentation` and `tests/test_ai_blocks.py`.
- **Structured LLM output**: `generate_structured()` on the provider abstraction (JSON Schema where supported, `json_object` + Pydantic validation fallback) with per-block Pydantic models in `iterable/ai/models.py`. Schema-block LLM calls are batched when columns > 100.
- **AI context, progress, and sampling**: `context` parameter (title, description, tags, territory, source_url, card metadata) threaded into prompts; in-process progress hooks with a `Stage` enum and `progress` callback plus per-stage structured JSON logging (`iterable/ai/progress.py`); size-based sampling tiers driven by `MAX_ROWS_SAMPLING` (`iterable/ai/sampling.py`).
- **File metadata and multi-table docs**: File metadata helpers (size, sha256, encoding, record_count, table_count) in `iterable/ai/fileinfo.py`; XLS/XLSX multi-table documentation with `tables=` selection and per-table schema blocks.
- **Generic OpenAI-compatible provider**: Honors `LLM_PROVIDER` / `LLM_BASE_URL` / `LLM_API_KEY` / `LLM_DEFAULT_MODEL` environment variables.
- **Extended column statistics**: `ops.stats.compute()` gains optional `null_fraction`, `top_values`, and `is_dictionary` (via `DICT_THRESHOLD`).
- **Format metadata registry**: New `iterable/helpers/format_registry.py` with declarative `FormatDescriptor` entries as the single source of truth for built-in format metadata. `detect.py` now derives `DATATYPE_REGISTRY`, `READ_ONLY_FORMATS`, `TEXT_DATA_TYPES`, and `FLAT_TYPES` from the descriptor table; content-based magic-byte detection uses `match_magic_prefix()`. Lookup API: `get_descriptor()`, `iter_descriptors()`. `capabilities.py` uses descriptor-based read-only checks. See OpenSpec change `add-format-metadata-registry` and `tests/test_format_registry.py`.
- **Ingest and codec deduplication**: Shared SQL ingest helpers (`create_text_table`, `run_batched_ingest`) in `iterable/ingest/_sql_base.py` for PostgreSQL/MySQL/SQLite backends. Shared codec stream helper `get_underlying_fileobj()` in `iterable/codecs/_stream.py` for gzip/bz2/zstd.
- **Uncovered format tests**: New `tests/test_uncovered_formats.py` with registry, round-trip, and contract tests for the ten formats that previously had no dedicated coverage (plan item 4.1).
- **Conformance fixture auto-discovery**: `tests/conformance_fixtures.py` discovers golden fixtures; `dev/scripts/find_missing_fixtures.py` reports text/codec and binary golden gaps (CI advisory).
- **Format doc stubs**: `dev/scripts/generate_format_doc_stubs.py` and 23 stub pages under `docs/docs/formats/`.
- **Per-package coverage tracking**: `dev/scripts/coverage_by_package.py` reports package-level coverage with advisory floors (`--check`).

### Changed
- **Fixture consolidation**: All test data merged into `tests/fixtures/`; `tests/testdata` is a symlink for legacy paths; repo-root `testdata/` removed (plan item 4.3).
- **Detect module split**: Content-based detection in `iterable/helpers/content_detection.py`; `open_iterable()` in `iterable/helpers/open_iterable.py` (plan item 3.4).
- **Guidance and DataFrame splits**: Actionable error guidance moved to `iterable/guidance.py`; shared `to_pandas`/`to_polars`/`to_dask` logic in `iterable/dataframe_adapters.py` (plan item 3.4).
- **Codec base split**: `BaseCodec` moved to `iterable/codec_base.py` (re-exported from `iterable.base`) (plan item 3.4).
- **Strict mypy core (partial)**: `disallow_untyped_defs` enabled for twelve core modules in `pyproject.toml` (plan item 3.5); blocking in CI.
- **Placeholder formats documented**: Module docstrings for `flatbuffers` and `hudi` clarify partial/schema-dependent support; removed stale `7zcodec.py_` duplicate (plan item 3.3).
- **ZIP wrappers on `BaseFileIterable`**: `ZIPSourceWrapper` and `ZIPXMLSource` now extend `BaseFileIterable` with proper close/reset lifecycle and `_closed` handling (plan item 3.3).
- **Docs site build**: Docusaurus build fixed (MDX placeholders, format link cleanup, `FORMAT_PAGE_TEMPLATE.md` moved out of `docs/docs/`). CI `docs` job runs blocking `npm run build`.
- **Pre-commit hooks**: Ruff bumped to v0.14.9; hook versions aligned with CI tooling.
- **Install hints**: `install_extra_hint()` in `format_registry.py` drives per-format `pip install iterabledata[<extra>]` messages in `_load_symbol`.

### Fixed
- **XML `tagname`**: `iterableargs['tagname']` is no longer overwritten with `None` after `super().__init__()` in `xml.py`.
- **Pickle `read_bulk`**: Returns `[]` at EOF instead of raising `StopIteration` in `picklef.py` (conformance contract).

## [1.0.12] - 2026-06-12

### Security
- **SQL identifier quoting in ingest**: PostgreSQL, MySQL, SQLite, and DuckDB ingest backends now validate and quote table and column names before interpolating them into SQL statements (new `iterable/ingest/identifiers.py`), preventing SQL injection through crafted identifiers. Control characters in identifiers are rejected.

### Added
- **Default `read_bulk()` in `BaseIterable`**: The base class now provides a concrete `read_bulk()` implementation (read() loop with StopIteration handling). 86 identical per-format implementations were removed; formats keep optimized overrides where they exist (Parquet, CSV, SQLite, etc.).
- **Format conformance test suite**: New `tests/test_format_conformance.py` validates every format in `DATATYPE_REGISTRY` (class loads, static `id()`, iterator contract methods) and verifies runtime behavior (StopIteration at EOF, `read_bulk` semantics, reset round-trip) for fixture-backed formats.
- **Shared datatype helpers**: New `iterable/datatypes/_shared.py` with `graph_to_records()` (GEXF/GraphML/DOT) and `rdf_term_to_str()` (TriG/N3/TriX), replacing per-module duplicates.
- **`zipxml` registry entry**: `ZIPXMLSource` is now registered in `DATATYPE_REGISTRY` and usable via `open_iterable(..., iterableargs={"format": "zipxml", "tagname": ...})`; it also gained proper `reset()` and static `id()` implementations (same for `ZIPSourceWrapper`).
- **`feed` registry alias**: canonical "feed" format id now resolves alongside "atom"/"rss".
- **Project URLs**: `Documentation` and `Changelog` URLs added to packaging metadata.
- **Validation hooks on write**: JSON, Parquet, SQLite, TopoJSON, JSONL, Arrow, and YAML now apply `validation_hook` in `write()` and `write_bulk()` (previously only CSV did). Invalid rows are skipped when `on_validation_error="skip"`.
- **Specs**: New capabilities `validation-consistency` and `sqlite-optimization`; `topojson-format` extended with write-structure requirement.
- **Confidence Scores for Format Detection**: Detection results now include confidence scores (0.0-1.0) and detection method
  - `detect_file_type()` returns `confidence` and `detection_method` fields
  - Filename detection: confidence 1.0, method "filename"
  - Magic number detection: confidence 0.95-0.99, method "magic_number"
  - Heuristic detection: confidence 0.70-0.90, method "heuristic" (varies by match quality)
  - See `docs/docs/api/open-iterable.md` for detailed confidence score documentation
- **Memory Usage Benchmarks**: New benchmark script `dev/benchmarks/bench_memory_usage.py` for comparing memory usage
  - Measures memory usage for streaming vs non-streaming formats
  - Demonstrates memory efficiency improvements from streaming implementations
  - Reports memory per record and streaming status

### Changed
- **CI consolidation**: `ci.yml`, `test.yml`, and `lint.yml` merged into a single `ci.yml` with three jobs (lint, test matrix across 3 OS x Python 3.10-3.12, security). Ruff lint/format, mypy on core modules (`types.py`, `exceptions.py`, `async_base.py`), and Bandit high-severity scans are now blocking; full mypy, pydocstyle, vulture, radon, and pip-audit remain advisory.
- **Single PyPI publish path**: `release.yml` no longer uploads to PyPI directly; publishing happens exclusively in `python-publish.yml` (triggered by GitHub Release publication) using PyPI Trusted Publishing instead of token secrets. Release tests now install via `pip install -e ".[dev]"` instead of legacy `requirements.txt`.
- **Docs deployment target**: Docusaurus config now points at the real repository (`datenoio/iterabledata`) and publishes to `https://datenoio.github.io/iterabledata/` (previously configured for a non-existent `iterabledata.github.io` site).
- **`iterable.ingest` is the submodule again**: `from iterable import ingest; ingest.to_db(...)` works as documented (previously `iterable.ingest` was accidentally bound to the `to_db` function itself).
- **`iterable.validate` is the submodule again**: `from iterable import validate; validate.iterable(...)` works as documented (previously bound to the `iterable()` function itself). `validate.iterable(..., mode="stats")` now actually returns the statistics dictionary instead of an exhausted generator.
- **READ_ONLY_FORMATS updated**: added missing read-only formats fasta/fastq (and aliases), bam, sam, trig, n3, trix, graphml, gexf, dot/gv, xlsb, and the `nc` netcdf alias.
- **Data types consistency**: SQLite `read_bulk()` now uses `cursor.fetchmany(size)` for efficient bulk reads. TopoJSON `write_bulk()`/`write()` buffer records and emit a single valid TopoJSON document (`{"type": "Topology", ...}`) on `close()`.
- **Exception Hierarchy**: Comprehensive exception hierarchy replaces generic exceptions
  - **New Base Exception**: `IterableDataError` - Base exception for all library errors
  - **Format Exceptions**: `FormatError`, `FormatNotSupportedError`, `FormatDetectionError`, `FormatParseError`
  - **Codec Exceptions**: `CodecError`, `CodecNotSupportedError`, `CodecDecompressionError`, `CodecCompressionError`
  - **Read/Write Exceptions**: `ReadError`, `WriteError`, `WriteNotSupportedError`, `StreamingNotSupportedError`
  - **Resource Exceptions**: `ResourceError`, `StreamNotSeekableError`, `ResourceLeakError`
  - All format implementations updated to use specific exceptions instead of `NotImplementedError`, `ValueError`, or generic `Exception`
  - Exception messages include error codes for programmatic handling
  - See `docs/docs/getting-started/migration-guide.md` for migration guide
- **Format Detection**: Enhanced content-based format detection with confidence scores
  - `detect_file_type_from_content()` now returns `(format_id, confidence, method)` tuple
  - `detect_file_type()` includes `confidence` and `detection_method` in results
  - Improved detection accuracy with confidence scoring
  - See `docs/docs/api/open-iterable.md` for detection behavior documentation
- **Streaming Status Reporting**: Improved accuracy of streaming capability detection
  - Capability system updated to use known non-streaming formats list
  - Detects conditional streaming (e.g., JSON uses streaming for files >10MB)
  - `is_streaming()` method now accurately reflects actual streaming behavior
- **Documentation**: Enhanced documentation with memory warnings and error handling guides
  - Added memory warnings for non-streaming formats in `capabilities.md`, `best-practices.md`, and format-specific docs
  - Added comprehensive error handling guide with exception hierarchy examples
  - Added format detection details with magic numbers table and confidence scores
  - Updated migration guide with exception handling changes
- **Documentation Improvements**: Standardized examples and expanded coverage
  - Standardized all examples to use context managers consistently
  - Added error handling sections to all format documentation (JSON, YAML, XLSX, ODS, TOML, FWF, etc.)
  - Converted parameter documentation to structured tables with Type, Default, Required, Description columns
  - Created comprehensive performance guide (`docs/docs/getting-started/performance.md`) covering bulk operations, memory management, format selection, compression, streaming vs batch, DuckDB engine, benchmarking
  - Expanded troubleshooting guide with factory method issues, reset operation issues, context manager issues, exception handling, common error messages reference, debugging tips
  - Updated migration guide with factory methods, type hints, and improved initialization validation
  - Added resource management documentation with context manager patterns, cleanup on exceptions, reset operations

### Fixed
- **PCAP iterator contract**: `PCAPIterable.read()` now raises `StopIteration` at end of file instead of returning `None`; added missing static `id()` and a `reset()` that clears reader state.
- **Async error propagation**: `AsyncBaseIterable.__anext__` no longer converts arbitrary exceptions (parse errors, I/O errors) into `StopAsyncIteration`; only source exhaustion ends iteration. `AsyncBaseFileIterable.aread()` now correctly handles `StopIteration` raised inside executor threads (previously surfaced as `RuntimeError`).
- **`read_bulk` at EOF**: AVRO, XLS, and XLSX `read_bulk()` no longer raise `StopIteration` when the source is exhausted mid-chunk; they return the partial chunk (and `[]` thereafter) per the documented contract.
- **Double-counting in SQL ingest**: PostgreSQL, MySQL, SQLite, and DuckDB ingest no longer duplicate the first row when given a list (the schema-probe row was re-read because a fresh iterator was created for the main loop).
- **NumPy invalid-shape error**: `NumPyIterable` no longer crashes with `TypeError` when raising `FormatNotSupportedError` for unsupported array shapes (constructor arguments were passed incorrectly).
- **Typed core modules**: `iterable/types.py`, `iterable/exceptions.py`, and `iterable/async_base.py` are now mypy-clean; exception `__str__` guidance guards against `None` format/codec ids.
- **Memory Anti-Patterns**: Fixed memory loading patterns in format implementations
  - JSON format: Uses `ijson` for streaming when files >10MB (was loading entire file)
  - GeoJSON format: Uses `ijson` for streaming large files (was loading entire file)
  - TopoJSON format: Uses `ijson` for streaming when files >10MB (was loading entire file)
  - Audited all formats using `fobj.read()` - documented legitimate cases in `MEMORY_AUDIT.md`
  - Memory usage remains constant for streaming formats regardless of file size
- **Exception Handling**: Replaced generic exceptions with specific exception types
  - Format parsing errors now raise `FormatParseError` with context (row_number, byte_offset, original_line)
  - Resource requirement errors now raise `ReadError` or `WriteError` with error codes
  - Format detection errors now raise `FormatDetectionError` instead of `ValueError`
  - Write operations on unsupported formats now raise `WriteNotSupportedError` instead of `NotImplementedError`
  - All format implementations updated (15+ files modified, 30+ exception instances replaced)
- **DuckDB Engine**: Refactored for better performance and security
  - Replaced string formatting with parameterized queries to prevent SQL injection
  - Optimized DataFrame conversions using DuckDB's native `.df()` method when pandas available
  - Improved error handling with specific exceptions (`ReadError`, `FormatNotSupportedError`, `FormatParseError`)
  - Simplified batch loading logic with helper methods for better maintainability
- **Base Class Design**: Converted to Abstract Base Class (ABC) with proper method signatures
  - `BaseIterable` now enforces `read()` and `read_bulk()` as abstract methods
  - Default implementations for `write()`, `write_bulk()`, `is_flat()`, `has_totals()`, etc.
  - Updated all 87+ format implementations to match consistent method signatures
  - Fixed `skip_empty` parameter defaults and `DEFAULT_BULK_NUMBER` usage across all formats
- **Resource Management**: Improved resource cleanup and error handling
  - Added seekable stream validation in `reset()` with clear error messages
  - Improved exception handling in `reset()` and `close()` methods
  - Simplified codec cleanup logic with proper error handling
  - Added comprehensive resource leak detection tests
  - Enhanced context manager support with proper cleanup on exceptions
- **Bulk Operations**: Optimized bulk read operations for better performance
  - Parquet/Arrow formats: Direct batch consumption with batch caching (10-100x faster)
  - ARFF/TOML formats: List slicing optimizations (2-5x faster)
  - ORC format: Direct iterator access optimization
  - All optimizations maintain backward compatibility and transparent performance improvements
- **Type Hints**: Comprehensive type annotation coverage
  - Added type hints to all public methods in base classes (`BaseIterable`, `BaseFileIterable`, `BaseCodec`)
  - Added type hints to all 95+ format implementation files
  - Created `Protocol` classes for duck typing (`Readable`, `Writable`, `Seekable`, `FileLike`)
  - Added `TypeVar` definitions for generic types (`T`, `T_co`, `T_contra`, `BufferType`, `DataFrameType`)
  - Enabled strict mypy checking with per-module overrides for optional dependencies
  - Added type stub packages for optional dependencies (`types-pyyaml`, `types-requests`, etc.)

### Added
- **Factory Methods for Initialization**: New class methods for clearer, type-safe initialization
  - `BaseFileIterable.from_file()` - File-based initialization with validation
  - `BaseFileIterable.from_stream()` - Stream-based initialization
  - `BaseFileIterable.from_codec()` - Codec-based initialization
  - Factory methods provide better error messages and prevent invalid configurations
  - All format implementations automatically inherit factory methods
  - Backward compatible - existing `__init__()` calls continue to work
  - See `docs/docs/getting-started/migration-guide.md` for usage examples
- **Type System**: Comprehensive type hints and type-safe helpers
  - Type aliases: `Row`, `IterableArgs`, `CodecArgs` for common dictionary types
  - Result dataclasses: `ConversionResult`, `FileConversionResult`, `BulkConversionResult`, `PipelineResult`
  - Typed helpers: `as_dataclasses()` and `as_pydantic()` for converting dict rows to typed objects
  - `py.typed` marker file for type checker support
  - See `docs/docs/api/type-system.md` for comprehensive documentation
- **Read-Ahead Caching**: Optional prefetching for improved I/O performance
  - Configurable via `iterableargs={'read_ahead': True, 'read_ahead_size': 10}`
  - Automatically refills buffer when it drops below threshold (30% by default)
  - Provides `peek()` method for non-consuming access to next row
  - Particularly beneficial for network sources and slow I/O
  - Disabled by default, opt-in feature
- **Parallel Bulk Conversion**: Concurrent file conversion support
  - `bulk_convert()` now supports `parallel=True` parameter
  - Uses `ThreadPoolExecutor` with configurable worker count (defaults to min(4, CPU count))
  - Processes multiple file conversions concurrently while maintaining error handling
  - Progress callbacks supported in parallel mode
  - Atomic writes supported in parallel mode
  - Sequential mode remains default for backward compatibility
- **Debug Mode**: Comprehensive debug logging for troubleshooting
  - Enable via `open_iterable(..., debug=True)` or `ITERABLEDATA_DEBUG` environment variable
  - Format detection logging: shows detection steps, extension checks, content-based detection attempts
  - File I/O logging: logs file operations, modes, encoding, errors
  - Performance logging: pipeline execution metrics with throughput
  - Integrates with Python's standard logging framework
  - See `docs/docs/getting-started/troubleshooting.md` for usage
- **Enhanced Error Messages**: Actionable guidance in exception messages
  - Exception messages now include troubleshooting steps and installation instructions
  - Context-aware guidance for `FormatNotSupportedError`, `FormatDetectionError`, `FormatParseError`
  - Smart dependency suggestions and format alternatives
  - Documentation links included in error messages
- **Structured Logging**: JSON and human-readable structured logging support
  - `configure_structured_logging()` function for JSON or human-readable output
  - Operation context tracking with operation IDs and correlation IDs
  - Standard event types: format_detection, file_io, parsing, conversion, pipeline, error, performance
  - Environment variable support: `ITERABLEDATA_STRUCTURED_LOGGING`, `ITERABLEDATA_LOG_FORMAT`
  - Context propagation using `contextvars` for operation tracking
  - Opt-in feature, disabled by default
- **Progress Callback Enhancements**: Improved progress tracking with configurable intervals and enhanced stats
  - Configurable `progress_interval` parameter for `convert()`, `pipeline()`, and `bulk_convert()`
  - Enhanced progress stats: `bytes_read`, `bytes_written`, `percent_complete`, `estimated_time_remaining`
  - `with_progress()` helper function for progress tracking during direct iteration
  - Backward compatible - default interval (1000 rows) unchanged
  - See `docs/docs/api/observability.md` for usage examples
- **Validation Hooks**: Automatic data validation during read/write operations
  - `ValidationHook` protocol for custom validation functions
  - Error handling policies: `raise` (default), `skip`, `log`, `warn`
  - Factory functions: `schema_validator()` and `rules_validator()` for easy integration
  - Support for single hook or multiple hooks (chaining)
  - Integrated into read operations (`__iter__`) and write operations (`write()`, `write_bulk()`)
  - Configuration via `iterableargs`: `validation_hook` and `on_validation_error` parameters
  - See `docs/docs/api/validate.md` for comprehensive documentation
- **Connection Pooling**: Thread-safe connection pooling for database drivers
  - `ConnectionPool` abstract base class and `SimpleConnectionPool` implementation
  - Global pool registry for managing pools per connection string
  - Automatic connection reuse across multiple queries to the same database
  - Configurable pool size (`min_size`, `max_size`), timeout, and max idle time
  - Connection validation and automatic stale connection cleanup
  - Enabled by default, can be disabled per connection via `pool.enabled=False`
  - Integrated into PostgreSQL driver (pattern can be applied to other drivers)
  - Pool statistics and cleanup functions for monitoring and management
  - See `docs/docs/api/database-engines.md` for usage examples
- **Plugin System**: Comprehensive plugin architecture for extending IterableData
  - Support for format, codec, database driver, validation rule, and engine plugins
  - Automatic plugin discovery via Python entry points (`iterabledata.formats`, `iterabledata.codecs`, etc.)
  - Programmatic registration API for dynamic plugin loading
  - Built-in formats/codecs take precedence over plugins (priority system)
  - Error isolation - plugin errors don't crash the core library
  - Plugin metadata support (version, author, custom metadata)
  - Lazy plugin discovery for optimal performance
  - Integrated with existing format detection and capabilities systems
  - See `docs/docs/api/plugins.md` for comprehensive documentation and examples
- **Async/Await Support (Phase 1)**: Foundation for asynchronous I/O operations
  - `AsyncBaseIterable` and `AsyncBaseFileIterable` base classes with async iterator protocol
  - `aopen_iterable()` function for async file opening
  - Async methods: `aread()`, `aread_bulk()`, `awrite()`, `awrite_bulk()`, `areset()`, `aclose()`
  - Async context manager and async iterator support
  - Thread pool executor wrapper for synchronous operations (Phase 1)
  - Supports concurrent file processing and async iteration
  - Backward compatible - synchronous API unchanged
  - Phase 2 (native async I/O) and Phase 3 (advanced features) planned for future releases
- **Write Support Documentation**: Comprehensive write capability tracking
  - `supports_write()` convenience function to check write support
  - `READ_ONLY_FORMATS` registry with 27 read-only format IDs
  - Capability system distinguishes between actual write implementations and base class defaults
  - Write support roadmap document with prioritized implementation plan
  - See `docs/docs/api/capabilities.md` for read-only formats documentation
- **Comprehensive Test Suites**: Expanded testing coverage
  - Edge case tests: empty files, invalid data, boundary conditions, file permissions, encoding issues
  - Performance benchmarks: CSV/JSONL read/write, bulk operations, format detection, streaming
  - Memory profiling tests: streaming vs non-streaming formats, memory leak detection
  - Stress tests: 10GB+ file handling, concurrent access, error recovery
  - Performance regression tests: baseline tracking with configurable thresholds
  - Concurrent access tests: thread safety, state isolation, error handling
- **Database Engine Support**: Read-only access to SQL and NoSQL databases as iterable data sources
  - **PostgreSQL Support**: Full support for PostgreSQL databases via `psycopg2-binary`
    - Connection via connection strings or existing connection objects
    - Streaming queries using server-side cursors for memory efficiency
    - Table name auto-query: automatically builds `SELECT * FROM table` queries
    - Query parameters: `query`, `schema`, `columns`, `filter`, `batch_size`
    - Read-only transactions by default for safety
    - `list_tables()` helper function for database introspection
  - **ClickHouse Support**: Full support for ClickHouse databases via `clickhouse-connect`
    - Connection via connection strings or existing client objects
    - Streaming queries using batch processing with `max_block_size` for memory efficiency
    - Table name auto-query: automatically builds `SELECT * FROM table` queries
    - Query parameters: `query`, `table`, `database`, `columns`, `filter`, `batch_size`, `settings`, `format`
    - Read-only query validation by default for safety (validates queries are SELECT statements)
    - ClickHouse-specific query settings support for performance tuning
    - Native format (default) and JSONEachRow format support
    - `list_tables()` helper function for database introspection
  - **Database Driver Architecture**: Extensible driver registry system
    - `DBDriver` abstract base class for database-specific implementations
    - Driver registry with `register_driver()`, `get_driver()`, `list_drivers()`
    - `DatabaseIterable` wrapper providing `BaseIterable` interface for database sources
  - **Integration with Existing Features**:
    - Database sources work with `open_iterable()` via `engine` parameter
    - Database → file conversion via `convert()` function
    - Database sources in data pipelines via `pipeline()` function
    - DataFrame bridges (`.to_pandas()`, `.to_polars()`, `.to_dask()`) work with database sources
  - **Optional Dependencies**: New dependency groups for database support
    - `db`: All database engines (`psycopg2-binary`, `pymongo`, `elasticsearch`, `pymysql`, `pyodbc`, `clickhouse-connect`)
    - `db-sql`: SQL databases only (`psycopg2-binary`, `pymysql`, `pyodbc`, `clickhouse-connect`)
    - `db-nosql`: NoSQL databases only (`pymongo`, `elasticsearch`)
  - **Usage Examples**:
    ```python
    from iterable.helpers.detect import open_iterable
    
    # Read from PostgreSQL database
    with open_iterable(
        'postgresql://user:password@localhost:5432/mydb',
        engine='postgres',
        iterableargs={'query': 'users'}
    ) as source:
        for row in source:
            print(row)
    
    # Read from ClickHouse database
    with open_iterable(
        'clickhouse://user:password@localhost:9000/analytics',
        engine='clickhouse',
        iterableargs={'query': 'events', 'settings': {'max_threads': 4}}
    ) as source:
        for row in source:
            print(row)
    
    # Convert database to file
    from iterable.convert import convert
    convert(
        fromfile='postgresql://localhost/mydb',
        tofile='users.parquet',
        iterableargs={'engine': 'postgres', 'query': 'users'}
    )
    ```
  - **Planned Database Support**: MySQL/MariaDB, Microsoft SQL Server, SQLite, MongoDB, Elasticsearch/OpenSearch
  - **Documentation**: Comprehensive database engine documentation in `docs/docs/api/database-engines.md`
- **Extended Table Listing Support**: Extended `list_tables()` and `has_tables()` support to additional formats
  - **HTML Format**: List all `<table>` elements by ID, caption, or index
    - Prefers table IDs (`<table id="...">`) when available
    - Falls back to caption text (`<caption>...</caption>`) if no ID
    - Uses numeric indices as final fallback
  - **XML Format**: List all unique tag names found in the document
    - Returns sorted list of tag names that can be iterated
    - Supports namespace prefix stripping
  - **ZIPXML Format**: List all XML files within ZIP archives
    - Returns sorted list of XML filenames (`.xml` extension)
    - Filters out non-XML files in the archive
  - **Iceberg Format**: List all tables in Iceberg catalogs
    - Supports catalog-based table discovery
    - Handles namespace-based catalogs
  - **Hudi Format**: List all tables in Hudi catalogs or directories
    - Returns `None` for single table paths (expected behavior)
    - Supports catalog-based listing when available
  - **Delta Format**: Table listing support (returns `None` for single table directories, which is the common case)
    - `has_tables()` returns `False` to indicate single-table directory usage
    - Catalog-based listing would require additional configuration
  - **Documentation**: Added format-specific documentation with `list_tables()` examples
    - Created `docs/docs/formats/html.md` with table listing examples
    - Created `docs/docs/formats/zipxml.md` with XML file listing examples
    - Updated `docs/docs/formats/iceberg.md`, `docs/docs/formats/hudi.md`, `docs/docs/formats/delta.md` with table listing examples
  - **Tests**: Comprehensive test coverage for all new table listing implementations
- **Error Handling Controls**: Configurable error policies for handling malformed records in production ETL pipelines
  - **Error Policy Configuration**: New `on_error` parameter in `iterableargs` with three options:
    - `'raise'` (default) - Raise exception immediately when parse error occurs (maintains backward compatibility)
    - `'skip'` - Silently skip malformed records and continue iteration
    - `'warn'` - Log warning using Python's `warnings` module and continue iteration
  - **Error Logging**: New `error_log` parameter in `iterableargs` for logging errors to file or file-like object
    - Logs include contextual information: timestamp, filename, row number, byte offset, error message, original line
    - Supports both file path strings and file-like objects
    - Works with all error policies (`raise`, `skip`, `warn`)
  - **Enhanced Error Context**: Parse errors now include detailed contextual information:
    - Filename (if available)
    - Row number (1-indexed, header excluded for text formats)
    - Byte offset in file (when available)
    - Original line content (for text formats, when available)
  - **Format Support**: Error handling implemented for CSV, JSONL, and XML formats
  - **Usage Examples**:
    ```python
    from iterable.helpers.detect import open_iterable
    
    # Skip bad records and continue processing
    with open_iterable('data.csv', iterableargs={'on_error': 'skip'}) as source:
        for row in source:
            process(row)
    
    # Warn on errors and log to file
    with open_iterable(
        'data.jsonl',
        iterableargs={'on_error': 'warn', 'error_log': 'errors.log'}
    ) as source:
        for row in source:
            process(row)
    
    # Log errors while raising exceptions (for analysis)
    with open_iterable(
        'data.xml',
        iterableargs={'on_error': 'raise', 'error_log': 'errors.log'}
    ) as source:
        for row in source:
            process(row)
    ```

### Changed
- `open_iterable()` now accepts database engines via `engine` parameter (e.g., `'postgres'`, `'clickhouse'`, `'mysql'`, `'mongo'`)
- `convert()` now supports database sources (database → file conversion)
- `pipeline()` now supports database sources as input

## [1.0.11] - 2026-01-25

### Added
- **Atomic Writes for Safer File Operations**: Production-safe file writing with temporary files and atomic renames
  - **New `atomic` Parameter**: Added to `convert()`, `bulk_convert()`, and `pipeline()` functions
    - When `atomic=True`, writes to temporary file (`.tmp` suffix) and atomically renames to final destination
    - Ensures output files are never left in partially written state
    - Original files preserved on failure or interruption
    - Temporary files automatically cleaned up on both success and failure
  - **Production Safety**: Prevents data corruption from crashes, interruptions, or mid-process failures
  - **Backward Compatible**: Defaults to `atomic=False` for existing code compatibility
  - **Usage Examples**:
    ```python
    from iterable.convert.core import convert
    
    # Convert with atomic writes for production safety
    convert('input.csv', 'output.parquet', atomic=True)
    
    # Atomic writes in pipelines
    from iterable.pipeline import pipeline
    pipeline(source=source, destination=dest, process_func=func, atomic=True)
    ```
  - **Limitations**: Atomic writes only work on same filesystem (uses `os.replace()`)
- **Bulk File Conversion**: Convert multiple files at once using glob patterns, directories, or file lists
  - **New `bulk_convert()` Function**: Batch conversion of multiple files with aggregated results
    - Supports glob patterns (e.g., `'data/raw/*.csv.gz'`)
    - Supports directory paths (converts all files in directory)
    - Supports single file paths
    - Reuses existing `convert()` function internally for each file
  - **Flexible Output Naming**: 
    - Filename patterns with placeholders: `{name}`, `{stem}`, `{ext}`
    - Extension replacement via `to_ext` parameter
    - Example: `pattern='{name}.parquet'` or `to_ext='parquet'`
  - **Aggregated Results**: `BulkConversionResult` object with:
    - Total files processed, successful, and failed
    - Total rows converted across all files
    - Per-file conversion results
    - Aggregated errors and throughput metrics
  - **Error Resilience**: Continues processing remaining files if one fails
  - **All `convert()` Parameters Supported**: All parameters (batch_size, iterableargs, is_flatten, etc.) are passed through
  - **Usage Examples**:
    ```python
    from iterable.convert.core import bulk_convert
    
    # Convert all CSV files matching glob pattern
    result = bulk_convert('data/raw/*.csv.gz', 'data/processed/', to_ext='parquet')
    
    # Convert with custom filename pattern
    result = bulk_convert('data/*.csv', 'output/', pattern='{name}.parquet')
    
    # Convert entire directory
    result = bulk_convert('data/raw/', 'data/processed/', to_ext='parquet')
    
    # Access results
    print(f"Converted {result.successful_files}/{result.total_files} files")
    print(f"Total rows: {result.total_rows_out}")
    for file_result in result.file_results:
        if file_result.success:
            print(f"✓ {file_result.source_file}")
        else:
            print(f"✗ {file_result.source_file}: {file_result.error}")
    ```
- **Observability Features**: Progress tracking, metrics, and logging for conversions and pipelines
  - **Progress Callbacks**: Custom callbacks for real-time progress tracking
    - `convert()` now accepts `progress` parameter for periodic progress updates
    - `pipeline()` now accepts `progress` parameter for periodic progress updates
    - Callbacks receive stats dictionary with rows processed, elapsed time, and throughput
  - **Built-in Progress Bars**: Visual progress indicators using `tqdm`
    - `convert()` now supports `show_progress` parameter for automatic progress bars
    - Progress bars respect `silent` parameter and gracefully handle missing `tqdm`
  - **Standardized Metrics Objects**: Structured metrics for programmatic access
    - `convert()` now returns `ConversionResult` object with:
      - `rows_in`, `rows_out`, `elapsed_seconds`, `bytes_read`, `bytes_written`, `errors`
    - `pipeline()` now returns `PipelineResult` object with:
      - `rows_processed`, `elapsed_seconds`, `throughput`, `exceptions`, `nulls`
      - Supports both attribute access and dictionary-style access for backward compatibility
  - **Usage Examples**:
    ```python
    # Progress callback
    def cb(stats):
        print(f"Progress: {stats['rows_read']} rows read")
    
    result = convert('input.csv', 'output.parquet', progress=cb)
    print(f"Converted {result.rows_out} rows in {result.elapsed_seconds:.2f}s")
    
    # Progress bar
    result = convert('input.jsonl', 'output.parquet', show_progress=True)
    
    # Pipeline metrics
    result = pipeline(source, destination, process_func=transform, progress=cb)
    print(f"Throughput: {result.throughput:.0f} rows/second")
    ```
  - **Backward Compatibility**: All changes are additive and backward compatible
    - Existing code using `convert()` without return value handling continues to work
    - Existing code using `pipeline()` with dictionary-style stats access continues to work
- **Cloud Storage Support**: Direct access to cloud object storage (S3, GCS, Azure) via URI schemes
  - **Supported Providers**:
    - Amazon S3: `s3://` and `s3a://` schemes
    - Google Cloud Storage: `gs://` and `gcs://` schemes
    - Azure Blob Storage: `az://`, `abfs://`, and `abfss://` schemes
  - **Features**:
    - Transparent integration with existing format detection and codec logic
    - Works with all compression codecs (gzip, zstd, bz2, etc.)
    - Streaming support for memory-efficient processing
    - Authentication via environment variables or `storage_options` parameter
  - **Optional Dependencies**: New `cloud` extra group in `pyproject.toml`
    - Install with: `pip install iterabledata[cloud]`
    - Includes: `fsspec`, `s3fs`, `gcsfs`, `adlfs`
  - **Usage Examples**:
    ```python
    # Read from S3
    with open_iterable('s3://bucket/data.csv') as source:
        for row in source:
            print(row)
    
    # Read compressed file from GCS
    with open_iterable('gs://bucket/data.jsonl.gz') as source:
        for row in source:
            print(row)
    
    # Write to Azure with authentication
    with open_iterable(
        'az://container/output.jsonl',
        mode='w',
        iterableargs={'storage_options': {'connection_string': '...'}}
    ) as dest:
        dest.write({'name': 'Alice', 'age': 30})
    ```
  - **Note**: DuckDB engine does not support cloud storage URIs; use `engine='internal'` (default)
  - All existing functionality works identically for cloud storage as for local files
- **DataFrame Bridges**: Convenient methods to convert iterable data to Pandas, Polars, and Dask DataFrames
  - **Pandas Bridge** (`to_pandas()` method):
    - Convert iterable to pandas DataFrame: `df = source.to_pandas()`
    - Chunked processing: `for df in source.to_pandas(chunksize=100_000): ...`
    - Preserves nested data structures as dict/list columns
  - **Polars Bridge** (`to_polars()` method):
    - Convert iterable to Polars DataFrame: `df = source.to_polars()`
    - Chunked processing: `for df in source.to_polars(chunksize=100_000): ...`
    - Efficient memory usage and modern API
  - **Dask Bridge** (`to_dask()` method and helper function):
    - Single file: `ddf = source.to_dask()`
    - Multi-file support: `ddf = to_dask(['file1.csv', 'file2.jsonl'])` - automatically detects formats
    - Builds Dask computation graph from multiple files
    - Supports out-of-core and distributed processing
  - **Optional Dependencies**: New `dataframes` extra group in `pyproject.toml`
    - Install with: `pip install iterabledata[dataframes]`
    - Includes: `pandas`, `polars`, `dask[dataframe]`
  - All methods raise helpful `ImportError` messages if dependencies are missing
  - Works with all supported formats (CSV, JSONL, Parquet, etc.)
  - Example usage:
    ```python
    # Pandas
    with open_iterable('data.csv.gz') as src:
        df = src.to_pandas()
    
    # Polars with chunking
    with open_iterable('large.csv') as src:
        for df in src.to_polars(chunksize=100_000):
            process(df)
    
    # Dask multi-file
    from iterable.helpers.bridges import to_dask
    ddf = to_dask(['file1.csv', 'file2.jsonl', 'file3.parquet'])
    result = ddf.groupby('category').sum().compute()
    ```
- **DuckDB Engine Pushdown Optimizations**: Advanced query optimizations for DuckDB engine
  - **Column Projection Pushdown** (`columns` parameter in `iterableargs`):
    - Only read specified columns from disk, reducing I/O and memory usage
    - Example: `iterableargs={'columns': ['name', 'age']}`
    - Works with CSV, JSONL, JSON, and Parquet formats
  - **Filter Pushdown** (`filter` parameter in `iterableargs`):
    - Filter rows at the database level before reading into Python
    - Supports SQL string filters: `iterableargs={'filter': "age > 18 AND status = 'active'"}`
    - Supports Python callable filters: `iterableargs={'filter': lambda row: row['age'] > 18}`
    - Python callables fall back to Python-side filtering if not translatable to SQL
  - **Direct SQL Query Support** (`query` parameter in `iterableargs`):
    - Execute full SQL queries while maintaining iterator interface
    - Example: `iterableargs={'query': 'SELECT name, age FROM read_csv_auto(\'file.csv\') WHERE age > 18 ORDER BY age DESC LIMIT 100'}`
    - Validates queries are read-only (rejects DDL/DML operations)
    - When `query` is provided, `columns` and `filter` parameters are ignored
  - **Format Detection Improvements**:
    - DuckDB engine now correctly detects file format and uses appropriate DuckDB function
    - CSV files use `read_csv_auto()`
    - JSONL/NDJSON files use `read_json_auto()`
    - JSON files use `read_json_auto()`
    - Parquet files use `read_parquet()`
  - **Combined Pushdown**: Support combining `columns` and `filter` for maximum efficiency
  - **Backward Compatible**: All changes are additive; existing code continues to work
  - Example usage:
    ```python
    # Column projection + filter pushdown
    with open_iterable(
        'data.csv',
        engine='duckdb',
        iterableargs={
            'columns': ['name', 'age'],
            'filter': 'age > 18'
        }
    ) as src:
        for row in src:
            process(row)
    
    # Direct SQL query
    with open_iterable(
        'data.parquet',
        engine='duckdb',
        iterableargs={
            'query': 'SELECT name FROM read_parquet(\'data.parquet\') WHERE age > 18'
        }
    ) as src:
        for row in src:
            process(row)
    ```
- **Error Handling Controls**: Configurable error policies and enhanced error context for robust data processing
  - **Configurable Error Policy** (`on_error` parameter in `iterableargs`):
    - `'raise'` (default) - Raise exceptions immediately (current behavior)
    - `'skip'` - Silently skip malformed records and continue processing
    - `'warn'` - Log warnings and continue processing (uses Python's `warnings` module)
  - **Error Logging** (`error_log` parameter in `iterableargs`):
    - Supports file path (string) or file-like object
    - Structured JSON log format with timestamp, filename, row number, byte offset, error message, and original line
    - Errors are logged regardless of error policy (useful for later analysis)
  - **Enhanced Error Context**:
    - `FormatParseError` and `ReadError` now include contextual attributes:
      - `filename` - File where error occurred
      - `row_number` - Row number (1-indexed, header excluded)
      - `byte_offset` - Byte offset in file where error occurred
      - `original_line` - Original line content that failed to parse (for text formats)
    - Error messages automatically include all available context
  - **Format Support**: Error handling implemented for CSV and JSONL formats
    - Other formats will benefit from base error handling infrastructure
  - **Backward Compatible**: Default behavior (`on_error='raise'`) maintains existing functionality
  - Example usage:
    ```python
    with open_iterable(
        'data.csv',
        iterableargs={'on_error': 'skip', 'error_log': 'errors.log'}
    ) as src:
        for row in src:
            process(row)
    ```
- **Type Hints and Typed Helpers**: Comprehensive type annotations and type-safe helper functions for modern Python projects
  - **Type Aliases** (`iterable/types.py`): Common type aliases for better code readability
    - `Row = dict[str, Any]` - Type alias for data rows
    - `IterableArgs = dict[str, Any]` - Type alias for iterable configuration arguments
    - `CodecArgs = dict[str, Any]` - Type alias for codec configuration arguments
  - **Complete Type Hints**: Full type annotations across the public API
    - `open_iterable()` - All parameters and return type annotated
    - `BaseIterable` methods - `read()`, `write()`, `read_bulk()`, `write_bulk()`, and all other methods
    - `convert()` - All parameters annotated with proper types
    - `pipeline()` - Complete type annotations for all parameters and return values
  - **Type Marker File**: Added `py.typed` marker file to indicate package supports type checking
    - Enables mypy, pyright, and other type checkers to use the provided type hints
  - **Typed Helper Functions** (`iterable/helpers/typed.py`):
    - `as_dataclasses(iterable, dataclass_type)` - Converts dict-based rows to dataclass instances
      - Provides type safety and IDE autocomplete for dataclass fields
      - Automatically filters extra fields not in the dataclass definition
    - `as_pydantic(iterable, model_type, validate=True)` - Converts rows to Pydantic model instances
      - Optional validation against Pydantic schemas
      - Catches schema issues early with helpful error messages
      - Requires `pydantic>=2.0.0` (install with `pip install iterabledata[pydantic]`)
  - **Improved IDE Support**: Type hints enable better autocomplete, type checking, and documentation in modern IDEs
  - All type hints are backward compatible and don't affect runtime behavior
- **Vortex Format Support**: Added support for reading and writing Vortex columnar data files
  - **Vortex Format** (`iterable/datatypes/vortex.py`) - Modern columnar format with fast random access
    - Supports reading and writing Vortex files (`.vortex`, `.vtx` extensions)
    - Automatic format detection by extension and magic number (`VTXF`)
    - Uses `vortex-data` library for core operations
    - Integrates with PyArrow for data conversion (dict ↔ Vortex arrays)
    - Supports bulk operations and totals counting
    - Requires `vortex-data>=0.56.0` package (install with `pip install iterabledata[vortex]`)
    - **Note**: `vortex-data` requires Python ≥3.11, but the library gracefully handles this version constraint

## [1.0.10] - 2026-01-13

### Added
- **Enhanced Format Detection**: Added content-based format detection using magic numbers and heuristics
  - **Magic Number Detection**: Detects binary formats by reading file headers (magic numbers)
    - `PAR1` → Parquet format
    - `ORC` → ORC format
    - `PK\x03\x04` → ZIP-based formats (XLSX, DOCX, etc.)
    - `ARROW1` → Arrow/Feather format
  - **Content Heuristic Detection**: Detects text formats using content analysis
    - JSON detection: Files starting with `{` or `[`
    - CSV detection: Files with consistent delimiter patterns (commas, tabs, pipes)
    - JSONL detection: Files where each line is valid JSON
  - **Combined Detection Strategy**: Uses filename extension as primary method, content detection as fallback
    - Works for files without extensions
    - Works for streams without filenames
    - Handles files with incorrect extensions
  - **Stream Support**: Content-based detection works with non-seekable streams
  - See `iterable.helpers.detect.detect_file_type_from_content()` for details
- **Exception Hierarchy**: Added comprehensive exception hierarchy for better error handling
  - **Base Exceptions**: `IterableDataError` - Base exception for all library errors
  - **Format Exceptions**: `FormatError`, `FormatNotSupportedError`, `FormatDetectionError`, `FormatParseError`
  - **Codec Exceptions**: `CodecError`, `CodecNotSupportedError`, `CodecDecompressionError`, `CodecCompressionError`
  - **Read/Write Exceptions**: `ReadError`, `WriteError`, `StreamingNotSupportedError`
  - **Resource Exceptions**: `ResourceError`, `StreamNotSeekableError`, `ResourceLeakError`
  - All exceptions include error codes for programmatic handling
  - See `iterable.exceptions` module for details
- **Format Capability Reporting**: Added programmatic API to query format capabilities
  - `get_format_capabilities(format_id)` - Get all capabilities for a specific format
  - `list_all_capabilities()` - Get capabilities for all registered formats
  - `get_capability(format_id, capability)` - Query a specific capability for a format
  - Capabilities include: readable, writable, bulk_read, bulk_write, totals, streaming, flat_only, tables, compression, nested
  - Returns boolean values (True/False) or None for unknown/unsupported capabilities
  - Handles optional dependencies gracefully
  - See `iterable.helpers.capabilities` module for details
- **Table Listing Support**: Added `list_tables()` and `has_tables()` methods to discover available tables, sheets, datasets, and other named collections in multi-table formats
  - **Excel formats** (XLSX, XLS, ODS): List sheet names
  - **Database formats** (SQLite, DuckDB): List table names
  - **Scientific formats** (HDF5, NetCDF): List dataset/variable names
  - **Geospatial formats** (GeoPackage): List layer names
  - **Statistical formats** (RData): List R object names
  - **Markup formats** (HTML, XML): List table identifiers (HTML) or tag names (XML)
  - **Archive formats** (ZIPXML): List XML filenames within ZIP archives
  - **Data lake formats** (Iceberg, Hudi): List table names from catalogs
  - Methods can be called on instances (reuses open connections) or with filename parameter
  - Returns `list[str]` of names, empty list `[]` for empty files, or `None` for unsupported formats
  - See [BaseIterable Methods](/api/base-iterable#list_tables) documentation for details

### Improved
- **Format Detection**: Enhanced `detect_file_type()` and `open_iterable()` to use content-based detection when filename detection fails
  - Automatically falls back to magic number detection for binary formats
  - Automatically falls back to heuristic detection for text formats
  - Better error messages with `FormatDetectionError` exception
  - Improved support for files without extensions or with incorrect extensions

## [1.0.9] - 2026-01-12

### Added
- **New Data Format Support**: Added support for 6 new data formats across scientific, geospatial, web feed, CAD, and network analysis domains
  - **NetCDF** (`iterable/datatypes/netcdf.py`) - Network Common Data Form for scientific array data
    - Supports reading multi-dimensional scientific data
    - Automatic dimension detection with configurable iteration
    - Requires `netCDF4` package (install with `pip install iterabledata[netcdf]`)
  - **Mapbox Vector Tiles** (`iterable/datatypes/mvt.py`) - MVT/PBF format for geospatial vector tiles
    - Decodes Mapbox Vector Tiles with layer support
    - Extracts features with geometry and properties
    - Requires `mapbox-vector-tile` package (install with `pip install iterabledata[geospatial]`)
  - **TopoJSON** (`iterable/datatypes/topojson.py`) - Topology-preserving GeoJSON extension
    - Converts TopoJSON topology to GeoJSON features
    - Supports multiple objects within a topology
    - Requires `topojson` package (install with `pip install iterabledata[geospatial]`)
  - **Atom/RSS Feeds** (`iterable/datatypes/feed.py`) - Web feed formats
    - Unified support for both Atom and RSS feeds
    - Extracts entries with metadata, content, and tags
    - Requires `feedparser` package (install with `pip install iterabledata[feed]`)
  - **DXF** (`iterable/datatypes/dxf.py`) - AutoCAD Drawing Exchange Format
    - Reads CAD entities (lines, circles, polylines, text, etc.)
    - Extracts geometry and layer information
    - Requires `ezdxf` package (install with `pip install iterabledata[dxf]`)
  - **PCAP/PCAPNG** (`iterable/datatypes/pcap.py`) - Packet capture format for network analysis
    - Supports both PCAP and PCAPNG formats
    - Extracts packet timestamps and data
    - Requires `dpkt` package (install with `pip install iterabledata[pcap]`)
- **Format Detection**: Updated `iterable/helpers/detect.py` with new file extensions:
  - `.nc`, `.netcdf` for NetCDF files
  - `.mvt`, `.pbf` for Mapbox Vector Tiles
  - `.topojson` for TopoJSON files
  - `.atom`, `.rss` for web feeds
  - `.dxf` for AutoCAD files
  - `.pcap`, `.pcapng` for packet capture files

### Improved
- All new formats support the `totals()` method for counting records
- Enhanced format detection with better extension mapping
- Consistent error handling with helpful installation messages

## [1.0.8] - 2026-01-05

### Added
- **AI Agent Integration Guides**: 
  - `AGENTS.md` - Comprehensive guide for integrating IterableData with LangChain, CrewAI, and AutoGen agents
  - `GEMINI.md` - Complete guide for using IterableData with Google Gemini AI for data processing and analysis
- **Documentation Enhancements**:
  - Added `docs/docs/api/capabilities.md` - Capability matrix showing read/write/bulk/totals/streaming support by format
  - Updated Docusaurus configuration and sidebars
- **Development Tools**:
  - `dev/benchmarks/bench_import_open.py` - Benchmarking tool for import performance
  - `dev/scripts/inspect_zip.py` - Utility for inspecting ZIP file contents
  - `dev/scripts/verify_output.py` - Output verification script
  - Moved `find_missing_fixtures.py` to `dev/scripts/` directory
- **Examples**:
  - `examples/zipxml/` - New example demonstrating ZIP XML processing with README
  - Updated existing examples with improvements
- **Test Data**:
  - Added `testdata/test_zipxml.zip` - Test fixture for ZIP XML processing
  - Added `tests/test_property_roundtrip.py` - New test for property roundtrip functionality

### Improved
- **Format Detection**: Enhanced `iterable/helpers/detect.py` with improved detection logic and better error handling
- **Compression Codecs**: Updated all codec implementations (brotli, bz2, gzip, lz4, lzma, lzo, raw, snappy, szip, zip, zstd) with consistent patterns and improved error handling
- **Data Type Handlers**: Refactored all datatype modules for better consistency, error handling, and code organization
- **Conversion Core**: Improved `iterable/convert/core.py` with better format handling
- **Pipeline Processing**: Enhanced `iterable/pipeline/core.py` with improved state management and error handling
- **Helper Utilities**: Updated `iterable/helpers/utils.py` and `iterable/helpers/schema.py` with new functionality
- **Base Classes**: Improved `iterable/base.py` with better abstraction and error handling
- **Test Suite**: Comprehensive updates to all test files with improved fixtures and test coverage
- **Test Data**: Updated compression test fixtures (br, bz2, gz, lz4, xz, zst) with corrected data
- **Documentation**: Updated installation instructions and GitHub Pages setup documentation

### Fixed
- Removed obsolete test data files (`test_convert_csv_json.json`, `test_mysqldump_*.sql`, `test_warc_roundtrip.warc`)
- Fixed compression codec implementations for better consistency
- Improved error messages and handling across all modules

## [1.0.7] - 2024-12-15

### Added
- **Comprehensive Documentation**: Enhanced README.md with detailed usage examples, API reference, and comprehensive guides
- **GitHub Actions Release Workflow**: Automatic release generation with version verification, testing, and PyPI publishing support
- **Improved Examples**: Added examples for all major use cases including format conversion, pipeline processing, and DuckDB integration

### Improved
- **Documentation Structure**: Better organized README with clear sections for quick start, usage examples, and API reference
- **Release Process**: Automated CI/CD pipeline for building and publishing releases

### Fixed
- Documentation examples and code snippets updated for accuracy

## [1.0.5] - Previous Release

### Added
- DuckDB engine support
- Enhanced format detection
- Improved compression codec handling
- Pipeline processing framework
- Bulk operations support

