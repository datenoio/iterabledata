# IterableData Repository Review

**Review date:** 2026-07-16

**Repository version:** 1.0.16

**Scope:** implementation architecture, code quality, tests, CI/security, packaging, documentation, repository hygiene, file-format coverage, and file-format read/write performance.

**Supersedes:** the 2026-07-14 review in this file. Findings already addressed by the twelve completed OpenSpec changes were re-tested rather than copied forward.

## Executive summary

IterableData has an unusually broad and useful core: 111 canonical formats behind a consistent iterator API, transparent codecs, a machine-readable catalog, conversion and validation layers, database integrations, agent tooling, and a substantial test suite. The work completed since the previous review materially improved the project: the default suite is green, the performance gate is active, high-risk parsers are hardened, several formerly eager readers now stream in batches, dependency hints are much better, and GeoJSONSeq, TAR, and genomic VCF/BCF are now supported.

The repository is nevertheless not release-clean yet. The most urgent issues span both release engineering and several hot I/O paths:

1. **The wheel contains files outside the library.** A local build produced a 266-file wheel containing top-level `dev/`, `examples/`, `docs/`, and `iterable/` trees. `check-wheel-contents` failed with W004/W005/W009. Restrict setuptools discovery to `iterable` and add a wheel-content gate before the next release.
2. **The nominally blocking Mypy gate is red.** The exact CI core command reports three errors in `helpers/open_iterable.py` and `async_base.py`. Full-package Mypy reports 1,224 errors in 167 files, so the shipped `py.typed` marker currently promises more typing completeness than the implementation delivers.
3. **Tests are passing but not hermetic.** The suite passed (`2,218 passed`, `329 skipped`) but rewrote seven tracked binary fixtures, leaving a clean checkout dirty. CI also installs only `[dev]` in every ordinary matrix leg, so many advertised optional formats are skipped on all operating systems.
4. **The “single source of truth” for formats is still fragmented.** Only 1 of 111 descriptors populates `extra`, none populates `magic`, compression capability is guessed as readable = compressed, and read-only/text/flat/install metadata is duplicated in hand-maintained tables.
5. **Format breadth is high, but the next additions should be selective.** The best gaps are Zarr; metadata-aware GeoParquet and FlatGeobuf; CRAM/BED/GFF3; and OTLP JSON/protobuf. FITS, GRIB, MATLAB, DICOM, safetensors, and GGUF are useful second-wave candidates but require an explicit array/tensor-to-row contract.
6. **The performance API has important path-dependent behavior.** Only 19 of 111 datatype classes override `read_bulk()`, 42 of 84 `write_bulk()` implementations call `write()` in a loop, JSONL bulk reading was slower than ordinary iteration in the local benchmark, and Parquet row writes created almost one row group per row after the first flush. Arrow and Parquet also use independent row and bulk cursors, so mixing `read()` with `read_bulk()` repeats data.

Overall assessment: **strong functionality and improving runtime quality, with immediate release-engineering and focused I/O-path cleanup required**.

## 1. Measured repository snapshot

| Measure | Result |
| --- | --- |
| Canonical formats / registry keys / aliases | 111 / 169 / 58 |
| Writable / read-only descriptors | 70 / 41 |
| Text / flat descriptors | 53 / 42 |
| Compression codecs | 11 |
| Python source files under `iterable/` | 216 |
| Python LOC (`wc -l`) | 31,808 |
| Test files / test functions | 170 / 2,265 |
| Optional-dependency groups | 65 (`all` has 81 entries) |
| Default test result | 2,218 passed, 329 skipped, 38 deselected, 20 warnings |
| Branch coverage | 61.64%; configured floor 55% |
| Performance regression gate | 5 passed |
| Advisory benchmark suite | 19 passed |
| Custom `read_bulk()` implementations | 19 / 111 datatype classes |
| `write_bulk()` implementations that call `write()` per row | 42 / 84 implementations |
| Targeted streaming-memory tests | 6 passed, 9 skipped (memory-profiler absent) |
| Ruff lint / format | Pass / pass (392 files formatted) |
| CI core Mypy command | **Fail: 3 errors in 2 files** |
| Full-package Mypy | **Fail: 1,224 errors in 167 files** |
| Radon | Average A (4.18), 2,055 blocks; 7 E/F-rated functions |
| Bandit `-ll` | 0 high, 30 medium; all medium findings are B608 SQL construction |
| Pydocstyle | 22 findings |
| Broad `except Exception` blocks | 292 |
| Format modules using `_handle_error()` | 4 |
| Fixture-gap audit | 142 gaps: 58 text/codec, 84 golden-read |
| Placeholder format-doc pages | 23 |
| OpenSpec strict validation | 53 passed, 0 failed |
| Completed but unarchived OpenSpec changes | 12 |
| Documentation production build | Pass, with stale Browserslist warning |
| Distribution checks | Twine pass; **check-wheel-contents fail** |

### Audit commands

The review used the configured project commands and additional audit checks:

```text
.venv/bin/pytest --verbose
ruff check iterable tests
ruff format --check iterable tests
mypy iterable
mypy --follow-imports=skip <the 12 CI-gated core files>
bandit -r iterable -ll
radon cc iterable -s -a
vulture iterable --min-confidence 80
pydocstyle iterable
.venv/bin/pytest tests/test_performance_regression.py -m performance --no-cov --verbose
.venv/bin/pytest tests/test_benchmarks.py -m benchmark --benchmark-only --no-cov
.venv/bin/pytest tests/test_memory_profiling.py tests/test_arrow.py::TestArrowStreaming \
  tests/test_shapefile.py::TestShapefileStreaming tests/test_snappy.py::TestSnappyStreaming --no-cov
openspec validate --all --strict --no-interactive
npm --prefix docs run build
python -m build; twine check; check-wheel-contents
python dev/scripts/find_missing_fixtures.py
```

## 2. What improved since the previous review

The twelve completed OpenSpec changes addressed most of the prior P0 findings:

- The default suite now completes without failures or collection errors.
- TOML round-trip behavior and stale benchmark assumptions were repaired.
- Missing optional dependencies skip cleanly in the tested environment.
- The performance regression baseline is committed and the five-workload gate passes.
- TAR container, GeoJSON Text Sequence, and genomic VCF/BCF support were added with tests and docs.
- VCF content detection now distinguishes genomic VCF from vCard despite the shared `.vcf` extension.
- Shapefile, Arrow, Lance, Delta, Iceberg, Hudi, XLSX, Snappy, and LZO paths received streaming/lazy improvements.
- Pickle trust gating, XML hardening, bounded parsing, safe identifier handling, and filter-expression validation improved untrusted-input behavior.
- The high-risk silent-error cases in SMILE, Hudi, vCard VCF, Parquet, and `open_iterable()` now surface typed failures.
- Dependency extras now cover the lakehouse and long-tail packages much more completely; `[all]` includes CBOR and CDF.
- The catalog, `dev/formats.json`, and docs targets currently agree for all 111 canonical formats.
- `open_iterable()` was split into smaller detection, validation, resolution, and construction stages; it is no longer one of the F-complexity functions.

These are meaningful improvements. The completed changes should now be archived so the OpenSpec `specs/` tree becomes the actual source of truth rather than leaving implemented deltas under `changes/`.

## 3. Priority findings and recommendations

### P0 — fix before the next release

#### 3.1 Restrict the wheel to the importable package

`[tool.setuptools.packages.find]` excludes only `tests`, so namespace-package discovery includes unrelated top-level directories. The reviewed wheel contained:

| Top-level path | Files in wheel |
| --- | ---: |
| `iterable/` | 217 |
| `examples/` | 33 |
| `dev/` | 9 |
| `docs/` | 1 |
| dist-info | 6 |

The `docs/` entry came from locally present `docs/node_modules/shell-quote/print.py`, demonstrating that ignored working-tree content can leak into a build. Even in a clean CI checkout, `dev/` and Python files under `examples/` are included.

Recommended fix:

- Set package discovery to `include = ["iterable", "iterable.*"]` (and/or disable implicit namespace discovery where appropriate).
- Build from a clean checkout in CI.
- Run `python -m build`, `twine check`, `check-wheel-contents`, install the wheel into a fresh environment, and smoke-test `import iterable` plus `open_iterable()`.
- Add an assertion that the wheel has only `iterable/` and dist-info top-level entries.

The build also reports setuptools deprecations for `license = {text = "MIT"}` and the license classifier. Move to an SPDX string (`license = "MIT"`) and `license-files` before setuptools' stated 2027 cutoff.

#### 3.2 Restore the blocking Mypy gate

The exact command in `.github/workflows/ci.yml` fails with:

- `iterable/helpers/open_iterable.py:389`: `Any` returned as `BaseIterable`.
- `iterable/helpers/open_iterable.py:477`: redundant cast.
- `iterable/async_base.py:214`: redundant cast.

Fix these three immediately or the lint job cannot be relied upon as a green required check. Then make the command a reusable script or configuration target so local and CI invocations cannot drift.

Do not attempt all 1,224 full-package errors in one change. Establish a checked baseline by package and expand strictness in this order: public helpers and catalog → ops/convert/validate → AI/tools → database integrations → datatypes/codecs. Keep new or edited files error-free while the historical baseline declines.

#### 3.3 Repair obsolete CI runtime/action references

- `.github/workflows/security.yml` uses `actions/upload-artifact@v3`. GitHub states v3 stopped working for GitHub.com customers on 2025-01-30; use v4. See the [GitHub artifact v3 deprecation notice](https://github.blog/changelog/2024-04-16-deprecation-notice-v3-of-the-artifact-actions/).
- CI and docs deployment pin Node 18. Node 18 reached end of life on 2025-03-27. Use a supported LTS line (currently 22 or 24) and update `docs/package.json` engines. See the [official Node release table](https://nodejs.org/en/about/previous-releases).
- Add Python 3.13 and 3.14 to CI after optional-dependency compatibility is verified. Python 3.14 is in bugfix support, while Python 3.10 reaches end of life in 2026-10; plan the 3.10 removal rather than continuing a 3.10–3.12-only matrix. See the [Python version status table](https://devguide.python.org/versions/).

### P1 — address in the next one or two development cycles

#### 3.4 Make tests hermetic and improve optional-format coverage

The suite passed but rewrote these tracked files:

- `tests/fixtures/2cols6rows_flat_converted.csv.gz`
- `tests/fixtures/2cols6rows_infer.avro`
- `tests/fixtures/2cols6rows_test.avro`
- `tests/fixtures/2cols6rows_test.csv.gz`
- `tests/fixtures/2cols6rows_test.dbf`
- `tests/fixtures/coerce.avro`
- `tests/fixtures/ru_cp1251_comma_converted.csv.gz`

The direct causes include write tests in `test_gzip.py`, `test_avro.py`, and `test_convert.py` targeting `tests/testdata`/`tests/fixtures` instead of `tmp_path`. Binary formats also embed timestamps or sync markers, so same-size rewrites are still byte-different.

Recommended actions:

- Copy read fixtures into `tmp_path` before any write/round-trip test.
- Reserve committed fixtures as immutable inputs.
- Add `git diff --exit-code -- tests/fixtures` after tests in CI.
- Add `.hypothesis` to `norecursedirs` (or extend rather than replace pytest's defaults) to remove the recurring collection warning.

CI currently installs `.[dev]` in the 3×3 OS/Python matrix and again in `test-base-env`. This makes the extra base-environment job largely duplicate an existing Linux leg, while 329 tests skip locally and many optional integrations may skip everywhere in CI.

Use a layered matrix instead:

1. Minimal/bare install job: importability and core CSV/JSONL behavior.
2. Cross-platform core job: `[dev]` on supported Python/OS combinations.
3. Linux representative-extras jobs grouped by family (columnar, scientific, geospatial, bio, database, lakehouse).
4. Live service/provider jobs only on schedules or explicit dispatch with secrets.

Avoid installing the 81-package `[all]` group as the sole full test: it includes packages with native/system requirements and will be fragile across platforms. Smaller family groups give clearer failures.

#### 3.5 Raise coverage by risk, not only globally

61.64% branch coverage passes the 55% floor, but coverage is uneven:

- `iterable/engines/duckdb.py`: 1.06% in this run.
- Most database ingestion backends: roughly 15–25%.
- `helpers/bridges.py`: 21%.
- `tools/langchain.py`: 42%.
- Several database drivers: roughly 57–78%.

The low figures partly reflect absent optional dependencies. Add per-package reports for the representative-extras jobs and introduce staged floors for stable core packages. A reasonable sequence is 60% immediately, 65% after optional jobs are active, then 70% once the high-risk engine/ingest paths are covered. Do not inflate coverage with assertion-light tests; prioritize failure cleanup, transaction handling, resource closure, and round trips.

The new performance gate is a strong addition and all five workloads pass. Its current 2.0–2.5× tolerances and five 10,000-row workloads are intentionally coarse, however, and do not detect the JSONL bulk slowdown, Parquet row-write fragmentation, mixed row/bulk cursor bug, or unbounded Arrow/Lance/Vortex write buffering found in this review. Retain the normalized single-runner gate, keep noisy absolute benchmarks advisory, and add ratio/structural assertions and memory ceilings as described in Section 5.

#### 3.6 Finish the format registry as a real source of truth

`FormatDescriptor` is a good architectural center, but important metadata still lives elsewhere:

- 1/111 descriptors sets `extra`; 110 exported catalog entries therefore report `"extra": null` even when an installation extra exists.
- 0/111 descriptors sets `magic`; nine signatures live in a separate `MAGIC_SIGNATURES` tuple.
- `_READONLY_MEMBERS`, `_TEXT_TYPE_ORDER`, `_FLAT_TYPE_ORDER`, `_MODULE_INSTALL_EXTRAS`, `_LLM_METADATA`, `FORMAT_DESCRIPTIONS`, and `DOC_FILENAMES` duplicate facts already associated with a format.
- Capability detection uses source inspection and heuristics. In particular, `compression` is set equal to `readable`, which is false for filename-only or backend-constrained formats.
- Only 31 datatype classes explicitly declare `is_streaming()`; the rest still depend on an allowlist/default heuristic.

Create an OpenSpec proposal such as `unify-format-capability-metadata` to:

- Put install extra, magic signatures, read/write/bulk/totals/streaming/tables/compression, maturity, and path/stream constraints in declarative metadata.
- Generate alias lookup, read-only/text/flat lists, install hints, catalog output, and docs matrices from that metadata.
- Require every built-in format to declare capabilities explicitly; use `unknown` rather than optimistic guesses.
- Add a conformance test that imports every installable descriptor and compares declared capabilities with method behavior.
- Add a catalog schema/version so agent consumers can detect incompatible metadata changes.

This will reduce drift and simplify `_detect_capabilities`, currently F-rated at complexity 44.

#### 3.7 Continue focused code-quality reduction

Average complexity is good, but seven functions concentrate risk:

| Function | Complexity |
| --- | ---: |
| `ai.doc.generate` | F (68) |
| `AnnotatedCSVIterable.read` | F (67) |
| `_detect_capabilities` | F (44) |
| `parse_line_protocol` | F (42) |
| `detect_file_type` | E (38) |
| `ops.schema.infer` | E (34) |
| `detect_file_type_from_content` | E (31) |

Refactor by parsing stages and decision tables, not by adding more helper indirection without tests. The successful `open_iterable()` split is a useful pattern.

There are 292 `except Exception` blocks and only four datatype modules route records through `_handle_error()`. The recent error-policy change fixed the known silent-data-loss cases, so this is no longer a blanket P0. Continue the audited migration when touching a format: narrow exceptions, add filename/format/record context, preserve the cause, and apply `on_error` consistently. Track accepted broad exceptions explicitly rather than chasing the raw count.

Vulture's actionable findings are small: `detect_dates` appears unused in both `ops/schema.py` and `ops/stats.py`; most other hits are conventional unused `__exit__` parameters. Pydocstyle's 22 errors are also small enough to clear and then make blocking.

#### 3.8 Clarify remaining security trust boundaries

Bandit found no high-severity issues. All 30 medium findings are B608 string-built SQL. Many are expected because identifiers are now validated/quoted and values use parameters, but database driver `filter_clause` inputs remain intentionally raw SQL.

Recommended actions:

- Document raw query/filter arguments as trusted-code APIs.
- Offer a structured predicate API for untrusted input rather than attempting to sanitize arbitrary SQL.
- Add backend-specific tests for identifier quoting and malicious names.
- Keep Pickle's explicit `trust=True` gate and hardened XML parser covered by regression tests.
- Review each `# nosec` annually and record the threat-model rationale beside it.

A local `pip-audit` reported 48 advisories across 15 installed packages. This is **not a reproducible project vulnerability result**: the local virtual environment is stale and includes many undeclared/transitive development packages. It does show that developer environments drift. Use a periodically refreshed development constraints/lock file, while continuing to publish the library with appropriately ranged dependencies. Make the scheduled audit produce an SBOM/artifact and distinguish runtime from dev-only advisories.

### P2 — repository and documentation maintenance

#### 3.9 Consolidate release automation

`release.yml` and `python-publish.yml` both contain build/version/publish logic and both use the long-lived `PYPI_API_TOKEN`. Consolidate them into one least-privilege release workflow, build once, test the exact artifacts, and publish through PyPI Trusted Publishing/OIDC. PyPI describes the security benefit as short-lived credentials rather than stored long-lived tokens; see [PyPI Trusted Publishers](https://docs.pypi.org/trusted-publishers/).

Add explicit workflow permissions, a protected release environment, artifact attestations/provenance, and a single manual recovery path. Do not maintain two subtly different publish implementations.

#### 3.10 Bring governance and repository status files up to date

- Archive all twelve completed OpenSpec changes; strict validation currently passes 53/53.
- Update or retire `IMPROVEMENT_PLAN.md`: it still says 107 formats, 147 tests, a 75% coverage gate, and several now-fixed CI/format gaps.
- Clarify whether `UNFINISHED_PROPOSALS.md` is historical or active; completed/archived entries dominate it.
- Remove the tracked `.DS_Store` and keep it ignored.
- Add a `SECURITY.md` with supported versions and private disclosure instructions.
- Consider `CODE_OF_CONDUCT.md`, `CODEOWNERS`, and a maintainer/release policy as the contributor base grows.
- Expand `CONTRIBUTING.md` with OpenSpec triggers, minimal vs family-extra test commands, fixture immutability, and the package-build check.

#### 3.11 Finish format documentation rather than generating more stubs

All catalog `doc_url` targets exist and the Docusaurus production build passes. However, 23 format pages still contain template placeholders such as `[Specific Use Case]` or `[Description of what this example does]`. Replace these with verified examples, install extras, capability/maturity badges, memory behavior, and limitations.

The committed `dev/formats.json` exactly matches the live export today, but its test checks exact fields only for three formats. Compare the complete generated object (with deterministic capability generation) or implement a `--check` mode that fails on any diff.

## 4. File-format support review

### 4.1 Current breadth

The current 111-format registry covers:

- Core text/tabular: CSV variants, JSON/JSONL, XML, YAML, TOML, FWF, logs, SQL dumps, COPY, PX, CSVW.
- Columnar/lakehouse: Parquet, ORC, Arrow/Feather, Lance, Vortex, Delta, Iceberg, Hudi.
- Serialization: Avro, BSON, MessagePack, CBOR, Ion, Protobuf, Thrift, FlatBuffers, FlexBuffers, UBJSON, Pickle, ASN.1, Bencode, Smile.
- Geospatial: GeoJSON, GeoJSONSeq, KML/KMZ, GPX, GML, Shapefile, GeoPackage, MVT, TopoJSON, DXF.
- Scientific/statistical: HDF5, NetCDF, NASA CDF, NumPy, SAS, SPSS, Stata, RData/RDS, ARFF, LIBSVM.
- RDF/graphs: RDF/XML, Turtle, N-Triples, N-Quads, TriG, N3, TriX, GraphML, GEXF, DOT.
- Bioinformatics: FASTA, FASTQ, SAM, BAM, genomic VCF/BCF, plus vCard VCF as a separate format.
- Web/log/container/stream formats: WARC/ARC/CDX, PCAP, feeds, email formats, TAR, Kafka, Pulsar, Flink, Beam, SequenceFile, RecordIO, TFRecord.

Breadth is no longer the primary weakness. Consistent maturity, installability, test fixtures, and truthful capabilities matter more than maximizing the raw count.

### 4.2 Gaps inside existing support

1. **Maturity is implicit.** Tests identify `fbs`, `hudi`, `lance`, `capnp`, `thrift`, `iceberg`, and `delta` as partial through free-text limitations. Add a structured `maturity = stable|experimental|partial` field.
2. **Golden conformance coverage is sparse.** Only 31 formats have the script's standard golden fixture; 84 are missing. Some cannot use a generic two-column table, so define format-specific canonical fixtures/overrides rather than treating every absence equally.
3. **Compression claims are optimistic.** Filename-only database/lakehouse formats and libraries that open paths directly cannot necessarily compose with every codec.
4. **Read-only support is broad.** Forty-one descriptors are read-only. Prioritize write support only where users need conversion targets and the backend safely supports it; do not implement writes merely for matrix symmetry.
5. **Cloud behavior is uneven.** Stream-compatible formats can use `fsspec`, while path-only formats and DuckDB reject cloud URIs. Expose this as a declared capability.

### 4.3 Recommended format roadmap

#### Tier 1 — highest value and best fit

| Candidate | Why it fits IterableData | Suggested implementation boundary |
| --- | --- | --- |
| **Zarr v2/v3** | Fills the largest scientific-array gap beside HDF5/NetCDF; official Python supports local, cloud, and in-memory stores | Iterate arrays by configurable first dimension or chunks; expose groups/arrays through `list_tables()`; require an OpenSpec data-model decision. [Zarr v3 specification](https://zarr-specs.readthedocs.io/en/latest/v3/core/) and [Zarr-Python](https://zarr.readthedocs.io/en/stable/) |
| **GeoParquet profile** | Reuses Parquet/Arrow while preserving CRS, geometry encoding, and bounding-box metadata | Extend Parquet with a metadata-aware profile rather than duplicate the reader; preserve GeoParquet metadata on write. [GeoParquet specification](https://geoparquet.org/) |
| **FlatGeobuf** | Streaming-friendly, indexed geospatial format; complements Shapefile/GeoPackage/GeoJSONSeq | Read features sequentially, use the documented magic bytes, optionally exploit the spatial index. [FlatGeobuf specification](https://flatgeobuf.org/) |
| **CRAM + BED + GFF3/GTF** | Natural extension of existing SAM/BAM/VCF and reuses the `pysam` extra for CRAM/BED-adjacent work | Extend the alignment family for CRAM; implement BED/GFF as streaming tabular profiles with coordinate semantics and header preservation. [GA4GH HTS specifications](https://github.com/samtools/hts-specs) and [GFF3 specification](https://github.com/The-Sequence-Ontology/Specifications/blob/master/gff3.md) |
| **OTLP JSON/protobuf exports** | Fits the existing CEF/GELF/log/Protobuf and observability layers; trace/log exports are naturally iterable | Yield one span, metric point, or log record with resource/scope context; preserve 64-bit JSON string rules. [OTLP specification](https://opentelemetry.io/docs/specs/otlp/) |

#### Tier 2 — valuable, but define row semantics first

| Candidate | Integration path and caution |
| --- | --- |
| **FITS** | Use `astropy.io.fits`; iterate table HDUs or configurable image slices and expose HDUs as tables. Memory mapping makes large data feasible. [Astropy FITS I/O](https://docs.astropy.org/en/stable/io/overview.html) |
| **GRIB/GRIB2** | Use ECMWF ecCodes; iterate messages and optionally expose decoded value arrays separately. [ecCodes Python GRIB tutorial](https://confluence.ecmwf.int/display/ECC/Introduction%2BTutorial%2Bon%2BGRIB%2Bdecoding%2Bwith%2BecCodes%3A%2Bdecoding%2Bwith%2Bthe%2BecCodes%2BPython%2BAPI) |
| **MATLAB `.mat`** | Use `scipy.io.loadmat`/`savemat` for v4–7.2 and the existing HDF5 path for 7.3. Decide whether variables, records, or array slices are rows. [SciPy `loadmat`](https://docs.scipy.org/doc/scipy/reference/generated/scipy.io.matlab.loadmat.html) |
| **DICOM** | Start with metadata-only records and deferred/optional pixel data using `pydicom`; avoid eagerly materializing images. [pydicom `dcmread`](https://pydicom.github.io/pydicom/stable/reference/generated/pydicom.filereader.dcmread.html) |
| **Safetensors** | Strong fit with the AI surface and a safer alternative to model Pickle; expose tensor metadata and configurable slices rather than pretending a whole model is tabular. [Safetensors documentation](https://huggingface.co/docs/safetensors/main/index) |
| **GGUF** | Useful for model inventory/catalog workflows; begin with key-value metadata and tensor directory entries, not inference. [GGUF specification](https://github.com/ggml-org/ggml/blob/master/docs/gguf.md) |

#### Tier 3 — add only with demonstrated demand

- HAR as a JSON profile, syslog RFC 3164/5424, and Windows EVTX for operational data.
- MBTiles as a specialized SQLite profile and PMTiles for cloud-native tiled maps.
- LAS/LAZ/COPC for point clouds.
- FIT/TCX for fitness/activity tracks.
- RAR as a read-only container.

These are reasonable formats, but each adds maintenance and fixture/dependency cost. Require an issue with a concrete use case, representative fixture, maintained backend, streaming story, and intended conversion targets before opening an implementation proposal.

### 4.4 Format-admission checklist

Every new format should include:

1. An approved OpenSpec proposal when it adds a capability or new dependency.
2. Declarative descriptor metadata: aliases, magic, extra, maturity, read/write, streaming, tables, compression, path/stream/cloud constraints.
3. A golden read fixture and, where writable, a round-trip fixture using `tmp_path`.
4. Malformed/empty/truncated input behavior and missing-dependency tests.
5. A memory-bound or batch-behavior test for formats advertised as streaming.
6. A completed docs page with install command, examples, limitations, security notes, and data-model mapping.
7. Verification in at least one representative-extras CI job.

## 5. File-format read/write performance review

### 5.1 Performance verdict

The project has a sound streaming foundation, but its performance is inconsistent across otherwise equivalent API paths. CSV, JSONL, XML, ORC, Parquet, Arrow IPC, Shapefile, Avro, MessagePack, BSON, PCAP, SQLite, and several lakehouse readers process data incrementally. Recent changes also made Arrow, Shapefile, Delta, Iceberg, Lance, XLSX, Snappy, and LZO materially safer for large inputs.

The main weakness is that `read_bulk()` and `write_bulk()` do not consistently mean native batching:

- Only 19 of 111 datatype classes implement `read_bulk()`; 90 reader classes inherit the base loop over `read()`.
- Two of the 19 custom readers (`GeoJSONIterable` and `PXIterable`) still call `read()` internally.
- Eighty-four classes implement `write_bulk()`, but 42 call `write()` once per record.
- The conversion layer batches destination writes but always consumes the source row by row, even when the source has an optimized bulk or native record-batch reader.
- Columnar/lakehouse readers usually decode a native batch and immediately materialize it as `list[dict]`, giving bounded memory but losing much of the columnar advantage.

This is not an argument to force every document format into a batch API. For TOML, email, configuration documents, graph documents, and similar formats, a whole-document parser or per-record writer may be the correct backend boundary. The capability model should distinguish **API bulk** from **native bulk**, and performance work should focus on high-volume tabular, event, columnar, database, and compressed paths.

### 5.2 Measured evidence

The committed normalized regression gate passed all five workloads. The separate `pytest-benchmark` suite also passed all 19 benchmarks. On the review machine, its 10,000-row CSV tests reported a mean of 12.73 ms for ordinary reading and 11.40 ms for bulk reading, so the current CSV bulk path was about 10% faster.

Additional local microbenchmarks used macOS, Python 3.13.7, warm filesystem cache, fixture creation outside the timed region, and the best of four runs unless noted. The absolute numbers are not portable baselines; the relative behavior identifies paths that need regression tests.

| Workload | Ordinary path | Bulk/alternate path | Result |
| --- | ---: | ---: | --- |
| CSV read, 50,000 rows | 62.2 ms | 56.5 ms (`read_bulk(1000)`) | Bulk about 9% faster |
| JSONL read, 50,000 rows | 79.2 ms | 166.6 ms (`read_bulk(1000)`) | **Bulk 2.1× slower** |
| CSV write, 50,000 rows | 58.4 ms | 49.0 ms (1,000-row batches) | Bulk about 16% faster |
| JSONL write, 50,000 rows | 95.2 ms | 86.1 ms (1,000-row batches) | Bulk about 10% faster |
| Parquet read, 100,000 rows | 67.2 ms | 61.9 ms (`read_bulk(1000)`) | Bulk about 8% faster |
| Parquet read, 100,000 rows | 67.2 ms | 80.4 ms (`read_bulk(1)`) | Tiny bulk calls about 20% slower |
| CSV→JSONL conversion, 50,000 rows, empty callback | 154.6 ms (`use_totals=False`) | 206.3 ms (`use_totals=True`) | Repeated totals scans made it 33% slower |

Parquet row writing was the clearest defect. This was a single 5,000-row local comparison using identical records:

| Parquet write path | Time | Output size | Row groups |
| --- | ---: | ---: | ---: |
| 5,000 calls to `write()` | 399.8 ms | 1,194,225 bytes | 3,977 |
| Five calls to `write_bulk()` | 4.4 ms | 23,583 bytes | 4 |

After the first buffer flush creates the writer, `ParquetIterable.write_bulk()` sends every subsequent call directly to `_write_records()`. Because `write()` delegates as a one-record bulk call, the remainder of a row-at-a-time workload becomes one PyArrow table and effectively one row group per record. In this sample, batching was about 91× faster and produced a file about 51× smaller.

Targeted memory/streaming tests produced six passes for Arrow, Shapefile, and Snappy. Nine generic memory-profiling tests skipped because `memory-profiler` was absent. The passing tests validate several recent improvements, but the skipped group means CSV, JSONL, compressed CSV, and cross-operation memory assertions are not currently enforced in this environment.

### 5.3 Critical performance and correctness findings

#### 5.3.1 Keep Parquet writes buffered after schema creation

`iterable/datatypes/parquet.py` uses a 1,024-row buffer only until the first writer is created. Subsequent calls bypass the buffer. This is catastrophic for the documented row API and also makes output structure depend on caller chunk boundaries.

Recommended fix:

- Keep appending to the buffer after schema creation and flush only when a configurable target row-group size is reached.
- Separate `batch_size` for read/decode batches from `row_group_size` for writes.
- Align records to the established schema at flush time, not on every row.
- Let PyArrow dictionary encoding default intelligently or expose `use_dictionary`; the current unconditional `use_dictionary=False` can hurt repeated-string compression and scan performance.
- Add tests for row-group count, file size sanity, bounded memory, mixed-size bulk calls, and row-versus-bulk throughput.

#### 5.3.2 Use one logical cursor for `read()` and `read_bulk()`

Parquet and Arrow initialize two independent batch iterators: one feeds `read()`, the other feeds `read_bulk()`. The review reproduced the following sequence for both formats:

```text
read()         -> row 0
read_bulk(2)   -> rows 0, 1
```

This repeats data and violates the expectation that both methods advance the same source. It can also invalidate performance measurements that mix sampling and bulk consumption.

Use one batch cursor plus an index/deque of unconsumed rows. Replace `list.pop(0)` in Arrow, Parquet, JSON/GeoJSON buffers, and `ReadAheadBuffer` with a deque or an index into an immutable batch. Add conformance tests that interleave row and bulk calls for every custom `read_bulk()` implementation.

#### 5.3.3 Remove successful per-line `tell()` calls from JSONL bulk reads

Both JSONL paths probe `tell()` before parsing each line for error context. Normal iteration uses `next(fileobj)`; after buffered text iteration starts, `tell()` quickly raises and the exception is ignored. The bulk path uses `readline()`, so `tell()` continues to succeed and performs decoder-position bookkeeping on every record. In the local test, this made bulk reading more than twice as slow as ordinary iteration.

Track offsets without probing the stream on every valid record, or make exact byte-offset capture conditional on an error/debug policy. A regression gate should require medium and large JSONL bulk reads to be no slower than row iteration outside a small noise allowance.

#### 5.3.4 Compute conversion totals once

`convert()` calls `totals()` in `_wrap_progress_iter()` and calls it again from `_report_progress()` at every progress interval when a callback is present. For CSV this is a complete file scan each time; at the default interval, a 50,000-row input is rescanned about 50 times. Compressed line totals are also broken: a local gzip CSV check passed a decoded text wrapper to `rowincount()`, which counts byte newlines and raised `TypeError`.

Compute `estimated_total` once before conversion, cache it in the metrics/context, and never let progress reporting consume or rescan the source. Metadata-backed totals (Parquet/ORC/Arrow/database counts) can remain cheap, but they should follow the same single-evaluation contract. Add compressed and non-seekable-source tests.

### 5.4 Performance by format family

| Family | Current strengths | Main performance gaps | Recommended direction |
| --- | --- | --- | --- |
| CSV and row-text formats | Incremental parsing; CSV uses `writerows()`; line formats have low memory use | CSV probes `tell()` in the hot path; most log/text `write_bulk()` methods loop; encoding detection reads up to 1 MB on open | Make offset tracking cheap/conditional; add native line-batch writes where they reduce syscalls; allow explicit encoding/format hints to skip probing |
| JSONL / GeoJSONSeq | Naturally streaming and writable; bulk output coalesces writes | JSONL bulk `tell()` regression; standard `json` creates a dict and strings per row | Fix offset tracking first; then benchmark an optional faster compatible JSON backend behind strict semantic tests |
| JSON / GeoJSON / TopoJSON | JSON and GeoJSON use `ijson` for larger files; JSON/GeoJSON writes stream array/feature delimiters | Fixed 10 MB mode threshold; small inputs fully materialize; no projection; list-backed item caches | Make parse mode/threshold explicit; use deque/index buffers; document top-level shape limitations and memory behavior |
| XML and annotated CSV | XML uses `iterparse()` and clears/prunes processed elements | Annotated CSV calls `readlines()` during reset and has an F-complexity row parser | Scan only the annotation/header prefix, then continue streaming; split conversion/type parsing into cached stages |
| Parquet / ORC / Arrow | Native batch readers; metadata totals; ORC uses `writerows()` | Python `dict` materialization; Parquet row-write fragmentation; Arrow buffers all writes; no general projection/filter API | Fix buffering/cursor defects; expose projection and native record batches; tune row groups/dictionaries/compression |
| XLSX / XLS / ODS | XLSX uses openpyxl `read_only=True` and iterates rows | XLS/ODS backends materialize workbook data; Python cell-to-dict conversion dominates | Declare eager formats; add sheet/range/column selection; benchmark wide and sparse workbooks |
| SQLite / DuckDB files | SQLite `fetchmany()` and `executemany()` are real batch paths | SQLite `write()` commits every record; DuckDB file engine issues repeated `LIMIT/OFFSET` queries and converts batches through pandas/dicts | Use explicit transaction scopes; keep one result/record-batch cursor; push projection/filter before Python conversion |
| Delta / Iceberg / Lance / Hudi / Vortex | Delta, Iceberg, and Lance read native batches; metadata totals exist in several backends | All batches become dicts; Hudi converts the whole table to pandas and repeats that in `totals()`; Arrow/Lance/Vortex writes are unbounded buffers | Add native batch bridge; cache Hudi materialization/count or use backend scans; enforce writer flush thresholds and declare unavoidable eager paths |
| HDF5 / NetCDF / NumPy / statistical formats | Backends often support slicing or row iteration | Generic row conversion can copy arrays/scalars; selection/chunk semantics are inconsistent | Add variable/dataset, slice, column, and chunk selection before conversion; benchmark wide arrays and large first dimensions |
| TAR / ZIP / 7z and codecs | Archive and codec wrappers compose with existing readers; common codecs stream | TAR buffers each member fully (`raw.read()`), so memory is O(largest member); archives default to the first member; resets may decompress again | Stream members through readers that do not require reset, spool only when necessary, expose member selection, and benchmark nested compression |
| Config/document/graph formats | Correct whole-document libraries are reused | Many formats necessarily load the full object graph; `read_bulk()` cannot reduce parser memory | Declare eager behavior and recommended size limits; avoid claiming native bulk/streaming; prioritize safety and predictable failure |

DuckDB engine observations in this table are from static inspection because the optional `duckdb` package was not installed in the review environment. Its query construction supports useful projection and filter pushdown, but a persistent DuckDB result/Arrow batch reader should replace repeated offset queries before treating it as the high-throughput default.

### 5.5 Cross-cutting improvement opportunities

1. **Add an optional native-batch protocol.** Keep the public row iterator, but allow compatible sources to yield PyArrow `RecordBatch`, tuples, or backend-native batches. Converters targeting Parquet, Arrow, ORC, Lance, Delta, or databases could then avoid `RecordBatch → list[dict] → RecordBatch` round trips.
2. **Make conversion pull batches.** `_run_write_loop()` currently iterates one row at a time and only batches the output. When flattening, validation hooks, and row callbacks are not required, consume `read_bulk(batch_size)` or the native-batch protocol directly. Preserve a row-transform fallback for semantic compatibility.
3. **Standardize bounded writer buffering.** Arrow and Lance define `batch_size` but do not flush writes at that threshold; Vortex explicitly holds the whole output until close. Every descriptor should declare `write_memory = bounded|whole_output|backend_defined`, and bounded writers should expose a tested limit.
4. **Push selection down.** Add consistent `columns`, `filter`, `table/sheet`, and row-range options where the backend supports them. Parquet can project columns during `iter_batches`; lakehouse and scientific backends can select columns/datasets before Python objects are created.
5. **Avoid work on the success path solely for rare errors.** CSV/JSONL offset capture, repeated normalization, dynamic key rebuilding, and validation-list copies should be profiled. Preserve rich errors, but gather expensive context lazily where possible.
6. **Treat batch size as a policy, not one constant.** The base default is 100, Parquet/Arrow default to 1,024, DuckDB caches 1,000, and conversion writes 50,000. Expose separate read, transform, and write/row-group sizes and document their memory/throughput trade-offs.
7. **Fix or remove synchronous “read ahead.”** `ReadAheadBuffer` fills from the same thread and removes from a list with `pop(0)`; it does not overlap I/O with consumer work and can add overhead for large configured buffers. Use a deque for buffering and only add background prefetch where ownership, cancellation, exceptions, and close behavior are defined and benchmarked.
8. **Reduce multi-pass open/scan costs.** CSV encoding detection samples up to 1 MB through a separate open, schema inference scans and resets flat sources, and totals can add another pass. Respect explicit format/encoding/schema hints and report which automatic scans are being performed in debug metrics.

The native-batch protocol, new capability fields, changed batching semantics, or new tuning profiles are capability/architecture changes and should begin with an OpenSpec proposal such as `optimize-format-io-performance` before implementation.

### 5.6 Codec performance

The codec layer is mostly streaming: gzip, bzip2, XZ/LZMA, Zstandard, LZ4, and Brotli use file/stream wrappers, while the recent Snappy and LZO implementations process framed blocks. Important remaining points are:

- Zstandard defaults to compression level 19, Brotli to quality 11, and LZ4 to a high-compression mode. These defaults favor size over write throughput and are surprising for a general conversion library. Define documented `fast`, `balanced`, and `max` profiles or choose balanced defaults while retaining explicit levels.
- Snappy and LZO legacy raw blobs still require full-buffer fallback. Surface this in capabilities/runtime diagnostics and add memory tests for both framed and legacy inputs.
- LZO writing uses the project-specific `ILZO1` block framing rather than the `lzop` container despite accepting `.lzop`; benchmark and document interoperability separately from streaming performance.
- Codec reset closes and reopens the stream. Schema scans, totals, retries, and user resets therefore restart decompression. Avoid implicit multiple passes for compressed inputs and prefer spooling/cached metadata only when explicitly justified.
- The performance gate covers gzip only as JSONL.gz→Parquet conversion. Add direct read/write throughput and compression-ratio baselines for gzip, Zstandard, LZ4, Snappy, and Brotli using at least one compressible and one low-compressibility fixture.

### 5.7 Benchmark and regression-gate gaps

The existing gate is useful but too coarse to protect the optimized paths. A 2× tolerance can accept a major regression, and its workloads cover only CSV row/bulk read, CSV bulk write, JSONL row read, and one compressed conversion. The advisory benchmark named “bulk vs individual” benchmarks only the bulk function and runs the individual function once outside the timer, so it verifies equivalence but does not measure the ratio.

Extend performance testing with:

- Paired row/bulk measurements for CSV, JSONL, Parquet, Arrow, ORC, SQLite, and MessagePack at 10,000 and 100,000+ rows.
- Parquet structural assertions: bounded row-group count, no one-row groups from normal row writes, output-size sanity, and dictionary-encoding coverage.
- Mixed `read()`/`read_bulk()` cursor conformance for every custom bulk reader.
- Peak-memory ceilings for JSON/GeoJSON streaming mode, Arrow, Parquet, Lance, Delta, Iceberg, XLSX, TAR member handling, and every streaming codec.
- Cold-open and warm-throughput measurements separately; detection/import cost dominates small-file workloads while parsing dominates large files.
- Narrow ratio gates for deterministic comparisons on the same runner, with normalized absolute gates retained for broad regressions.
- Benchmark metadata including dependency versions, CPU, Python, batch sizes, input bytes, output bytes, and rows/row groups—not only elapsed time.

### 5.8 Prioritized performance action plan

| Priority | Change | Acceptance criteria |
| --- | --- | --- |
| P0 | Fix Parquet buffering after writer creation | Row writes stay within a configured row-group bound; 5,000 row writes no longer create thousands of groups; row and bulk output remain equivalent |
| P0 | Unify Arrow/Parquet row and bulk cursors | Arbitrary interleaving never repeats or skips a row; one cursor implementation feeds both APIs |
| P0 | Cache conversion totals once | Exactly one `totals()` call per conversion; compressed totals are accurate; progress cannot consume the source |
| P0 | Remove JSONL per-line bulk `tell()` overhead | `read_bulk(1000)` is within 5% of or faster than row iteration on representative 10k/100k fixtures |
| P1 | Consume native/source batches in conversion | Columnar→columnar conversion avoids intermediate `list[dict]` where semantics permit; row fallback remains tested |
| P1 | Bound Arrow/Lance/Vortex and other writer buffers | Peak memory is proportional to configured batch size, or the format is explicitly declared whole-output |
| P1 | Add projection/filter/slice pushdown | Unselected columns/variables are not materialized; performance tests cover narrow reads from wide inputs |
| P1 | Optimize database transactions/cursors | SQLite row writes do not commit per record by default; DuckDB uses a persistent result/batch stream rather than repeated offsets |
| P1 | Add codec performance profiles and coverage | Defaults are documented; throughput/ratio/memory baselines cover the five primary codecs |
| P2 | Classify eager and native-bulk capabilities | Catalog/docs state native bulk, read/write memory behavior, selection support, and size limitations truthfully |

## 6. Suggested implementation sequence

The recommendations above are represented by dependency-ordered OpenSpec change proposals. Each change contains `proposal.md`, `tasks.md`, a design where the scope is cross-cutting, and strict-format spec deltas. The proposals were approved for implementation in this work; each task checklist below reflects verified implementation status rather than planned work.

### Workflow prerequisite

Archive the twelve completed changes currently left under `openspec/changes/` before implementing a new proposal that overlaps their capabilities. In particular, archive the performance-regression, streaming-reader, codec-streaming, capability-truth, dependency-metadata, and test-suite-resilience changes so future deltas are based on current specs. Archiving is an OpenSpec workflow action, not a new change proposal.

### Immediate foundation

| Order | OpenSpec change | Scope | Main prerequisite |
| ---: | --- | --- | --- |
| 1 | [`optimize-format-io-hot-paths`](openspec/changes/optimize-format-io-hot-paths/proposal.md) | Parquet buffering, unified row/bulk cursors, JSONL hot path, cached totals, bounded Arrow/Lance writes, structural/performance gates | Archive completed performance/streaming changes |
| 2 | [`harden-release-artifacts`](openspec/changes/harden-release-artifacts/proposal.md) | Minimal wheel, artifact smoke tests, supported CI runtimes/actions, SPDX metadata, consolidated OIDC publishing | Independent |
| 3 | [`strengthen-repository-quality-gates`](openspec/changes/strengthen-repository-quality-gates/proposal.md) | Hermetic fixtures, minimal/family CI, coverage, Mypy ratchet, static quality, complexity, docs/status cleanup | Archive `update-test-suite-resilience` |

### Near-term metadata foundation

| Order | OpenSpec change | Scope | Main prerequisite |
| ---: | --- | --- | --- |
| 4 | [`unify-format-capability-metadata`](openspec/changes/unify-format-capability-metadata/proposal.md) | Complete declarative descriptors, generated registries/catalog/docs, native-bulk and memory/source capabilities, catalog schema version | Archive dependency/streaming metadata changes; coordinate with change 1 |

### Medium-term performance architecture

| Order | OpenSpec change | Scope | Main prerequisite |
| ---: | --- | --- | --- |
| 5 | [`add-native-batch-conversion`](openspec/changes/add-native-batch-conversion/proposal.md) | Optional native batch protocols, columnar-to-columnar transfer, projection/filter/table/slice pushdown, row fallback | Changes 1 and 4 |
| 6 | [`add-codec-performance-profiles`](openspec/changes/add-codec-performance-profiles/proposal.md) | Fast/balanced/max profiles, effective-setting diagnostics, throughput/ratio/memory baselines, legacy-path truth | Archive `update-codec-streaming`; coordinate benchmark jobs with change 1 |

### Format expansion

| Order | OpenSpec change | Scope | Main prerequisite |
| ---: | --- | --- | --- |
| 7 | [`add-zarr-format`](openspec/changes/add-zarr-format/proposal.md) | Zarr v2/v3 groups/arrays, explicit row mapping, slices/chunks, bounded writes, local/cloud stores | Change 4; reuse change 5 when available |
| 8 | [`add-geoparquet-flatgeobuf-formats`](openspec/changes/add-geoparquet-flatgeobuf-formats/proposal.md) | GeoParquet metadata profile and FlatGeobuf streaming/indexed features | Change 4; reuse change 5 when available |
| 9 | [`extend-bioinformatics-formats`](openspec/changes/extend-bioinformatics-formats/proposal.md) | CRAM, BED3–12+, GFF3/GTF, reference and coordinate semantics | Archive genomic VCF change; coordinate with change 4 |
| 10 | [`add-otlp-format-profiles`](openspec/changes/add-otlp-format-profiles/proposal.md) | OTLP JSON/Protobuf traces, logs, metrics, type fidelity, bounded JSON and guarded binary parsing | Change 4 |

Tier-2 candidates such as FITS, GRIB, MATLAB, DICOM, safetensors, and GGUF remain admission-gated backlog items rather than premature active proposals. Create their OpenSpecs only after a concrete use case, representative fixture, maintained backend, row-model decision, and intended conversion targets are available.

### 6.1 Implementation status

The approved foundation is now implemented in the repository:

- Parquet and Arrow share one row/bulk cursor; Parquet has bounded, configurable row groups; Arrow/Lance flush bounded batches; JSONL offset work and conversion totals are cached on the success path. Regression tests cover mixed row/bulk calls, text/columnar equivalence, physical row groups, and peak memory.
- Native batch conversion is opt-in through `BatchSelection` and `use_native_batch=True`, with Parquet/Arrow adapters, projection/range selection, strict unsupported-selection errors, and row-transform fallback.
- Codec profiles (`fast`, `balanced`, `max`) are available across the tunable codecs with explicit-level precedence and framed/legacy diagnostics for Snappy/LZO.
- The format catalog now carries versioned extended capability metadata, and generated catalog/audit checks are available. Zarr, GeoParquet/FlatGeobuf, CRAM/BED/GFF3/GTF, and OTLP profiles are registered with optional-dependency errors and focused tests/docs.
- Release artifacts are restricted to the `iterable` package, source distributions are pruned, wheels/sdists are checked and smoke-installed, and the duplicate token-based publishing workflow is replaced by a single OIDC/attestation release flow. CI now includes fixture-diff protection, a minimal install smoke test, and representative optional-family jobs.

Verification on the review machine: 81 focused implementation tests passed; Ruff check and format checks passed; fixture-diff protection passed; `openspec validate --all --strict --no-interactive` passed (63/63); and `python -m build`, `twine check`, and the distribution-content audit passed. The final full suite reported 2,349 passed, 339 skipped, 19 deselected, and 7 failures because the committed DBF fixture/test pair assumes uppercase numeric fields while the fixture stores lowercase character fields. That compatibility gap is recorded rather than hidden and should be resolved before making the full suite a blocking release gate.

The remaining unchecked OpenSpec tasks are intentionally explicit: deeper native adapters (ORC/lakehouse/scientific), complete Zarr v2/v3 and FlatGeobuf golden fixtures, OTLP incremental JSON streaming and full official protobuf matrices, benchmark-baseline regeneration, and the outstanding typing/static-analysis/doc-page backlog.

## 7. Review limitations

- The full test run used the repository's existing macOS Python 3.13 virtual environment; optional packages present there differ from clean CI, so skip counts are environment-specific.
- The full run exposed a legacy/environment-sensitive DBF fixture/type expectation; it is not represented as a passing quality gate.
- Live databases, cloud providers, Kafka/Pulsar, and LLM-provider integration tests were not run because they require external services or credentials.
- The local `pip-audit` result reflects a stale developer environment, not a resolved clean installation or an SBOM for the built wheel.
- Performance was checked against the committed normalized regression gate, the local advisory benchmark suite, and focused microbenchmarks on one warm-cache macOS/Python 3.13.7 environment. Absolute timings were not re-baselined across machines and should not be treated as portable targets.
- The optional DuckDB engine tests were available in this environment, but its performance findings remain from code-path inspection rather than a dedicated benchmark. Nine generic memory tests skipped because `memory-profiler` was absent.
- Format recommendations are based on adjacency to current capabilities, maintained official specifications/reference libraries, streaming feasibility, and implementation reuse. Actual user demand should still determine final ordering.

## Conclusion

IterableData now has the core performance, artifact, capability-metadata, native-batch, codec-profile, and format-profile foundations described by this review. The next quality step is to finish the explicitly tracked optional-backend adapters and representative benchmarks/fixtures, then ratchet typing, static analysis, and coverage gates without weakening the iterator-first design.
