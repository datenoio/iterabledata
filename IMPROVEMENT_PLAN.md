# IterableData Improvement Plan

Date: 2026-06-12
Baseline: v1.0.11 (PyPI) + large uncommitted working tree (~262 changed paths)

This plan is based on a full repository audit covering architecture and features,
code quality, testing, CI/CD, documentation, and release/product quality.
Items are grouped by theme and ordered by priority within each theme.
Suggested phasing is at the end.

---

## 1. Current State Summary

**Strengths**

- 107 format classes behind a unified `open_iterable()` / `BaseIterable` API; 10 compression codecs; 7 DB read engines; mature convert, pipeline, and ops layers.
- 147 test files with a 75% coverage gate; multi-Python (3.10–3.12) and cross-OS CI; weekly security scans; Dependabot.
- Minimal core dependencies (`chardet`, `tqdm`) with 30+ optional extras; `py.typed` shipped; published on PyPI as `iterabledata`.
- Mature OpenSpec process (38 specs, 0 active proposals), Cursor skills, AGENTS.md, large Docusaurus docs site, 1,300-line README.
- Well-designed plugin system (entry points for formats, codecs, drivers, rules, engines).

**Key weaknesses**

- Format knowledge is scattered across 5 places (`DATATYPE_REGISTRY`, `TEXT_DATA_TYPES`, `FLAT_TYPES`, `READ_ONLY_FORMATS`, `datatypes/__init__.py`) and `READ_ONLY_FORMATS` is stale (missing fasta, bam, sam, trig, graphml, gexf, ...).
- Heavy copy-paste: identical `read_bulk` loops in ~90 files, `_graph_to_records` duplicated in 3 graph formats, RDF helpers duplicated in 3 modules, codec stream-wrapping duplicated, 6 near-identical ingest modules.
- Quality gates not enforced: mypy, pydocstyle, vulture, radon, security scans, and even some ruff format checks run with `|| true` in CI.
- 10 formats with no test coverage (kafka, pulsar, flink, beam, lance, recordio, sequencefile, tfrecord, flexbuffers, zipped); 26 formats without docs pages.
- Broken contracts: `pcap.py` returns `None` instead of raising `StopIteration`, lacks `id()`/`read_bulk()`; `zipped.py`/`zipxml.py` bypass `BaseFileIterable`; `async_base.py` swallows all exceptions as `StopAsyncIteration`.
- Docs site deployment is broken (configured URL returns 404; org/repo mismatch between `iterabledata.github.io` config and `datenoio/iterabledata` repo).
- Release hygiene: two overlapping CI workflows, two PyPI publish paths with different secrets, release tests use legacy `requirements.txt`, and a large feature batch (RDF/bio/graph/geo formats, examples) is uncommitted and unreleased.
- SQL injection surface in ingest modules (table/column names interpolated into SQL strings).

---

## 2. Immediate Housekeeping (P0)

These unblock everything else and carry release/security risk.

### 2.1 Commit and release the in-flight work
- Review, commit, and push the ~262-path working tree (new formats: fasta, fastq, bam, sam, cdf, dot, gexf, graphml, gpx, kmz, n3, trig, trix, xlsb; new examples; OpenSpec archives).
- Cut release `1.0.12` (or `1.1.0` given the feature volume): move the large `[Unreleased]` CHANGELOG section into a release entry, bump `iterable/__init__.py`, tag, and publish.

### 2.2 Fix SQL injection surface in ingest
- `iterable/ingest/postgresql.py`, `mysql.py`, `sqlite.py`, etc. interpolate table/column names directly into SQL.
- Add identifier validation/quoting (e.g. `psycopg.sql.Identifier`, backtick/bracket quoting per driver, plus an allowlist regex for identifiers).
- **Status: Done.** `iterable/ingest/identifiers.py` validates and quotes table/column names; used by postgresql/mysql/sqlite/duckdb ingest and `_sql_base.py`. Covered by `tests/test_ingest_identifiers.py`.

### 2.3 Fix broken iterator contracts
- `iterable/datatypes/pcap.py`: raise `StopIteration` instead of returning `None`; add `id()`, `read_bulk()`, proper `reset()`; switch to relative imports.
- `iterable/async_base.py` `__anext__`: only convert `StopIteration` to `StopAsyncIteration`; let parse/I/O errors propagate. Align async default bulk size (1000) with sync `DEFAULT_BULK_NUMBER` (100) or document the difference.
- **Status: Done.** `pcap.py` refactored: `read()`/`__iter__` yield row dicts and raise `StopIteration` at EOF; `reset()` clears reader state; contract tests in `test_pcap.py`. `async_base.py` uses `DEFAULT_BULK_NUMBER` (100); error propagation tests in `test_async_support.py`.

### 2.4 Fix docs deployment
- Resolve the org/repo mismatch: `docs/docusaurus.config.js` targets `iterabledata.github.io` while the repo is `datenoio/iterabledata`; both URLs currently 404.
- Point config at the real Pages target, verify `deploy-docs.yml` publishes successfully, and update README/pyproject URLs to the working docs site.

---

## 3. Code Quality and Architecture (P1)

### 3.1 Single source of truth for format metadata
- Replace the parallel lists in `iterable/helpers/detect.py` (`DATATYPE_REGISTRY` ~160 keys, `TEXT_DATA_TYPES`, `FLAT_TYPES`, `READ_ONLY_FORMATS`) and the 521-line conditional-import `iterable/datatypes/__init__.py` with declarative per-format descriptors: id, aliases, module/class, text vs binary, flat, streaming, read/write capability, optional extra name, magic bytes.
- Drive `detect_file_type_from_content()` (currently a long if/elif chain), `capabilities.py`, and docs generation from the same descriptors.
- This also fixes the stale `READ_ONLY_FORMATS` list automatically.
- **Status: Implemented (core)** via OpenSpec change `add-format-metadata-registry`. New `iterable/helpers/format_registry.py` holds 108 `FormatDescriptor` entries; `detect.py` derives `DATATYPE_REGISTRY`, `READ_ONLY_FORMATS`, `TEXT_DATA_TYPES`, and `FLAT_TYPES` from them. Magic-byte detection uses `match_magic_prefix()`. `capabilities.py` uses `get_descriptor()` for read-only checks. Covered by `tests/test_format_registry.py`. Full suite verified (`pytest -m "not stress"`: 1959 passed). Follow-up: optional `datatypes/__init__.py` generation from descriptors.

### 3.2 Eliminate boilerplate duplication
- Add a default `read_bulk()` loop to `BaseIterable` (the exact loop copy-pasted in ~90 files); keep optimized overrides (parquet `iter_batches`, csv inline error handling).
- Create shared helpers: `_graph_to_records` (gexf/graphml/dot), RDF `_term_to_str` and load-then-iterate pattern (trig/n3/trix/turtle), optional-dependency import guard.
- Extract a generic SQL ingest base (batch loop, table creation, upsert, `IngestionResult`) so `postgresql.py`/`mysql.py`/`sqlite.py` shrink to driver-specific deltas. Same idea for the `_original_fileobj` stream-wrapping pattern shared by gzip/bz2/lzma/zstd codecs.
- **Status: Partially done.** Default `read_bulk()` in `BaseIterable` (17 optimized overrides remain). Shared helpers in `iterable/datatypes/_shared.py` (`graph_to_records`, `rdf_term_to_str`). SQL ingest batch loop + table creation extracted to `iterable/ingest/_sql_base.py` (used by postgresql/mysql/sqlite). Codec stream-wrapping deduped in `iterable/codecs/_stream.py` (gzip, bz2, zstd).

### 3.3 Fix architectural outliers
- Migrate `zipped.py` / `zipxml.py` from raw `BaseIterable` to `BaseFileIterable` (or implement the abstract contract properly); register `zipxml` in `DATATYPE_REGISTRY` so it works through `open_iterable()`.
- Decide the fate of placeholders: `flatbuffers.py` ("This is a placeholder"), `hudi.py` ("Placeholder"), the disabled `7zcodec.py_` (wire it in or delete it; README currently advertises 7z).
- Remove the no-op DuckDB path in `iterable/ops/stats.py::compute()` or implement it.
- **Status: Done.** ZIP wrappers on `BaseFileIterable`; stats no-op removed. Placeholders kept registered with module docstrings documenting partial/schema-dependent behavior. Stale `7zcodec.py_` removed (`szipcodec.py` is canonical); `7z` added to `CODEC_REGISTRY`.

### 3.4 Split oversized modules
- `iterable/helpers/detect.py` (1,196 lines) → registry, content detection, and `open_iterable` orchestration modules.
- `iterable/base.py` (955 lines) → split codec base and DataFrame adapters (`to_pandas`/`to_polars`/`to_dask` share near-identical chunking) out of the iterable hierarchy.
- `iterable/exceptions.py` (716 lines) → move the ~230 lines of guidance strings into a separate `guidance` module.
- **Status: Done.** Splits: `content_detection.py`, `open_iterable.py`, `format_registry.py`, `guidance.py`, `dataframe_adapters.py`, `codec_base.py`. `exceptions.py` ~451 lines; `base.py` ~866 lines; `detect.py` ~440 lines (lazy re-exports).

### 3.5 Typing and consistency cleanup
- Replace legacy `filename: str = None` with `str | None = None` (~90 files); add `from __future__ import annotations` and return types on `reset()` in older modules.
- Make mypy blocking in CI for core modules first (`base.py`, `types.py`, `helpers/detect.py`, `exceptions.py`), then enable `disallow_untyped_defs` package by package.
- Standardize the new-format template: module docstring, typed `__init__`, explicit streaming behavior, `_handle_error`/`on_error` integration (currently only ~15 formats use it), read-only declared in the registry rather than implied by base-class default.
- Stop swallowing plugin discovery errors silently in `detect.py` (`_ensure_plugins_discovered`); log at warning level with the failing entry point.
- **Status: In progress.** Strict mypy on 12 core modules (`helpers/utils.py` added). CI lint job runs blocking mypy on them.

---

## 4. Testing (P1)

### 4.1 Close the format coverage gap
- Add tests for the 10 uncovered formats: `kafka`, `pulsar`, `flink`, `beam` (mock/integration-marker based), `lance`, `recordio`, `sequencefile`, `tfrecord`, `flexbuffers`, `zipped`.
- For broker-backed formats (kafka, pulsar) use unit tests with mocked clients plus optional `@pytest.mark.integration` tests behind docker-compose.
- **Status: Implemented (baseline)** in `tests/test_uncovered_formats.py` — registry/contract tests for all 10, write/read round-trips for tfrecord/recordio/kafka/pulsar/flink/beam, SequenceFile read contract, zipped wrapper tests; flexbuffers/lance round-trips skip when optional deps are missing.

### 4.2 Contract test for all formats
- Add a parametrized conformance suite that iterates the format registry and asserts the base contract for every registered format with an available fixture: `read()` raises `StopIteration` at EOF, `read_bulk(n)` length semantics, `reset()` re-yields identical rows, `id()` is a static string, write round-trip where `supports_write` is true. This would have caught the `pcap.py` bug.
- Extend `dev/scripts/find_missing_fixtures.py` to binary formats and wire it into CI as a report.
- **Status: Done (baseline).** `tests/test_format_conformance.py` uses auto-discovery via `tests/conformance_fixtures.py` (24 golden formats). Write round-trip tests for writable fixture-backed formats. `dev/scripts/find_missing_fixtures.py` reports text+codec gaps and missing binary golden fixtures; CI runs it as an advisory step.

### 4.3 Consolidate fixtures
- Merge the duplicate fixture roots (`tests/fixtures/`, `tests/testdata/`, repo-root `testdata/`) into one documented layout.
- **Status: Done.** All committed fixtures live under `tests/fixtures/`. `tests/testdata` is a symlink to `fixtures/` for legacy paths. Repo-root `testdata/` removed (files merged into `tests/fixtures/`). See `tests/fixtures/README.md` and `fixture_path()` in `tests/conftest.py`.

### 4.4 Raise the bar gradually
- Once gaps are closed, raise `fail_under` from 75 toward 85; track per-package coverage so `datatypes/` weak spots are visible.
- **Status: Started.** `dev/scripts/coverage_by_package.py` prints per-package breakdown from `.coverage`; CI runs it (advisory) on Ubuntu 3.11 after pytest. Global `fail_under` remains 75 until coverage gaps close.

---

## 5. CI/CD and Release Engineering (P1)

### 5.1 Consolidate workflows
- Merge `ci.yml` and `test.yml` (they overlap on pytest + ruff for the same branches) into one matrix workflow; keep `lint.yml` checks inside it.
- Make checks blocking in stages: ruff format check first, then mypy on core modules, then pydocstyle on new code. Keep vulture/radon advisory.
- Make `bandit`/`pip-audit` failures at high severity blocking (currently all `|| true` / `continue-on-error`).
- **Status: Done (baseline).** Single `ci.yml` with lint, matrix test, and security jobs. Blocking: ruff, format, mypy (11 core modules), bandit high-severity, pip-audit. Advisory: pydocstyle, vulture, radon, fixture/coverage reports. Weekly `security.yml` retained for scheduled scans.

### 5.2 Unify release pipeline
- Pick one publish path: `release.yml` (tag-triggered, `PYPI_API_TOKEN`) vs `python-publish.yml` (release-triggered, `PYPI_ITERABLE_API_TOKEN`). Prefer one workflow using PyPI Trusted Publishing (OIDC, no token secret).
- Release workflow should install via `pip install -e ".[dev]"` like CI, not the legacy `requirements.txt`.
- Add `check-wheel-contents` and `twine check` to the release job (deps already present).
- **Status: Partial.** Tag workflow uses `pip install -e ".[dev]"`, `twine check`, and `check-wheel-contents`. PyPI publish is OIDC-only via `python-publish.yml` on release published. Follow-up: remove any legacy token publish path if still referenced elsewhere.

### 5.3 Pre-commit alignment
- Bump pinned ruff (v0.1.6 is old) and align hook versions with CI; consider adding mypy on changed files.

---

## 6. Features and Product (P2)

### 6.1 Write support for high-value read-only formats
- 27 formats are read-only. Prioritize per the existing `write-support-roadmap.md`: avro, xlsx, xml, ods first (common ETL targets); then scientific (hdf5, netcdf) and lakehouse (delta — write via `deltalake` package is feasible; iceberg via `pyiceberg`).

### 6.2 Async Phase 2
- `aopen_iterable()` is a thread-pool wrapper. Implement native async I/O for the highest-traffic line-oriented formats first (csv, jsonl, json) using `aiofiles`, and export `aopen_iterable` from the top-level `iterable` package.

### 6.3 DB parity
- Add ClickHouse and MSSQL ingest backends to match the 7 read drivers (8 vs 6 today).
- Extend connection pooling beyond PostgreSQL (at minimum MySQL).

### 6.4 Validation hook rollout
- Write-side validation hooks exist in only 8 of ~80 writable formats. Once `read_bulk`/write plumbing is centralized in the base class (3.2), hooks come for free — verify with the conformance suite.

### 6.5 Plugin ecosystem
- Publish one reference plugin package (e.g. a niche format) to prove the entry-point path end to end, and document plugin authoring in the docs site.

### 6.6 CLI (out of scope — handled externally)
- A CLI is already provided through the project's distribution metadata, not from this package. **Do not add a CLI module (`iterable/cli.py`) or a `[project.scripts]` entry point to this repo.** See the note in `AGENTS.md`.

---

## 7. Documentation and DX (P2)

- Add docs pages for the 26 undocumented formats (bam, cdf, fasta, fastq, gexf, gpx, graphml, kmz, n3, sam, topojson, trig, trix, xlsb, dot, arff, bsonf, dxf, feed, libsvm, mvt, netcdf, numpy, pcap, picklef, zipped). Consider generating stubs from the format metadata registry (3.1). **Status: Done (stubs).** `dev/scripts/generate_format_doc_stubs.py` generates registry stubs; 23 pages added under `docs/docs/formats/` and linked from `index.md`. Expand stubs with full examples over time.
- Add `CONTRIBUTING.md` (can largely link to AGENTS.md), GitHub issue templates, and a PR template. **Status: Done** — `CONTRIBUTING.md`, `.github/ISSUE_TEMPLATE/`, and `.github/pull_request_template.md`.
- Fix the `[Unreleased]` CHANGELOG discipline after the 1.0.12 release: keep entries small and release more frequently.
- Fix the `iterable/iterabledata.code-workspace` file accidentally placed inside the package directory (untracked; should not ship in the wheel).
- Clean up the misleading `ImportError` hint in `detect.py::_load_symbol` that suggests `pip install iterabledata[dev]` for missing format extras — point to the correct extra per format (also enabled by 3.1). **Status: Done** — `install_extra_hint()` in `format_registry.py` drives per-format `pip install iterabledata[<extra>]` messages.

---

## 8. Suggested Phasing

**Phase 1 — Stabilize (1–2 weeks)**
- 2.1 commit + release 1.0.12, 2.2 SQL injection fix, 2.3 contract bugs (pcap, async), 2.4 docs deployment, 5.2 unify release pipeline.

**Phase 2 — Consolidate (2–4 weeks)**
- 3.1 format metadata registry, 3.2 dedupe (`read_bulk` default, shared helpers, ingest base), 3.3 outliers/placeholders, 4.2 conformance suite, 4.1 missing format tests, 5.1 CI consolidation with staged blocking checks.

**Phase 3 — Harden (2–4 weeks)**
- 3.4 split large modules, 3.5 typing rollout (blocking mypy on core), 4.3 fixture consolidation, 4.4 coverage to 85%, 7 docs/DX items.

**Phase 4 — Grow (ongoing)**
- 6.1 write support roadmap, 6.2 async Phase 2, 6.3 DB parity, 6.4 validation hooks everywhere, 6.5 reference plugin, 6.6 CLI.

Each Phase 2–4 item that changes public behavior should go through the existing OpenSpec proposal workflow (`openspec/AGENTS.md`).

---

## 9. Quick Reference: Top 10 Actions

1. Commit the in-flight feature batch and release 1.0.12.
2. Parameterize/quote identifiers in `iterable/ingest/*` (security).
3. Fix `pcap.py` iterator contract and `async_base.py` exception swallowing.
4. Repair docs site deployment and URL mismatch.
5. Build a declarative format metadata registry; delete the 4 parallel lists.
6. Move the duplicated `read_bulk` loop into `BaseIterable`.
7. Add a registry-driven format conformance test suite.
8. Add tests for the 10 uncovered formats.
9. Merge duplicate CI workflows; make mypy/format/security checks blocking in stages.
10. Unify on a single PyPI publish workflow with Trusted Publishing.
