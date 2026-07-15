# IterableData Repository Review Report

Date: 2026-07-14
Scope: format coverage (supported vs missing), code quality, and performance. Combines static analysis, tool runs (ruff, radon, bandit, vulture, pytest, fixture-gap script), and a module-by-module read of `iterable/`. Supersedes the 2026-07-01 review; a "What changed since the last review" section tracks progress against it.

---

## Executive Summary

IterableData is in strong shape architecturally: a single declarative format registry (108 canonical formats, 162 lookup keys), a well-designed `BaseIterable` contract with typed core modules and a custom exception hierarchy, 164 test files with 2,145 test functions, and mature CI/security tooling. Several P0 items from the previous review have been fixed: the registry, `datatypes/__init__.py`, and `dev/formats.json` are now fully in sync; the README correctly disambiguates vCard VCF from genomic VCF; `py7zr` is in the `compression` extra; and import errors for missing optional dependencies now carry actionable install hints.

The three biggest issues today, in order:

1. **Test-suite health is worse than it looks.** Running the suite in a base environment produces 68 failures and 19 collection errors instead of clean skips, plus one genuine product bug (TOML write round-trip crashes) and stale benchmark tests that no longer match the current `read_bulk` contract. The committed `tests/testdata` symlink was also broken locally (a plain file instead of a symlink), which alone caused ~150 spurious failures.
2. **Error handling is centralized in design but not in practice.** The `_handle_error()` / `on_error` policy exists in `base.py` but only 3 of ~110 format modules use it; there are 296 `except Exception` blocks, several of which silently convert parse failures into empty datasets (SMILE, Hudi, stream-fallback in `open_iterable`).
3. **A meaningful set of formats advertised as iterable actually load the whole file/table into memory** — Arrow/Feather, Lance, Delta, Iceberg, Hudi, Shapefile, CBOR, YAML, TOML, and the Snappy/LZO codecs — which undermines the library's core streaming value proposition on large data.

Format breadth remains a strength (108 formats, 11 codecs). The most valuable genuinely-missing formats are Zarr, genomic VCF/BCF/CRAM/BED/GFF, FlatGeobuf/GeoParquet, MATLAB `.mat`, FITS/GRIB, HAR/syslog/EVTX, safetensors/GGUF, and TAR-as-container.

---

## What Changed Since the 2026-07-01 Review

| Previous finding | Status now |
| --- | --- |
| `datatypes/__init__.py` stale vs registry (12 missing imports, 6 missing from `__all__`) | **Fixed** — all 108 descriptor classes exported; `dev/formats.json` matches 108/108 |
| README claimed `.vcf` = Variant Call Format | **Fixed** — README explicitly says vCard, "not genomic Variant Call Format" |
| `py7zr` missing from `compression`/`all`; bogus `[szip]` hint | **Fixed** — `py7zr` in `[compression]`; install hints resolved via `install_extra_hint()` |
| `.sz` / Snappy / SZip confusion | **Fixed** in code: `.sz` → `SnappyCodec`, `.7z` → `SZipCodec` (naming caveat remains: "SZip" is 7z, not HDF5 SZIP) |
| Missing extras for many formats | **Partially fixed** — 48 extras now exist, but lakehouse and a long tail still uncovered (see §2.3) |
| `add-ai-block-documentation` OpenSpec change active though complete | **In progress** — being moved to `openspec/changes/archive/2026-07-01-add-ai-block-documentation/` in the working tree |
| 142 fixture gaps | **Unchanged** — script still reports 142 (58 text+codec, 84 golden read) |
| Silent parse failures / broad excepts | **Unchanged** — 296 `except Exception` (was ~290) |

---

## 1. Current Snapshot (measured)

| Metric | Value |
| --- | --- |
| Canonical formats / registry keys | 108 / 162 (54 aliases) |
| Writable / read-only formats | 69 / 39 |
| Codecs | 11 (gzip, bz2, lzma/xz, zip, raw, lz4, lzo, brotli, snappy, zstd, 7z) |
| Optional extras in `pyproject.toml` | 48 (`all` = 60 packages) |
| Test files / test functions | 164 / 2,145 |
| Coverage gate | `fail_under = 75`, branch coverage on |
| Ruff | 2 errors (E501), 1 file unformatted (`tests/test_parquet.py`) |
| Radon average complexity | A (4.37) over 1,911 blocks |
| Functions rated E/F | 9 (worst: `open_iterable` F=91) |
| Bandit | 0 high, 34 medium, 71 low over 32,052 LOC |
| `except Exception` occurrences | 296 across 96 files; 0 bare `except:` |
| Fixture gaps (`dev/scripts/find_missing_fixtures.py`) | 142 (58 text+codec, 84 golden read) |
| Test run (base env, no heavy extras, stress/slow excluded) | **1,962 passed, 68 failed, 361 skipped, 19 collection errors** |

---

## 2. Format Coverage

### 2.1 What is supported

- 108 canonical formats across tabular, binary serialization, geospatial, RDF/graph, scientific/statistical, biosequence, log/web, lakehouse, and stream domains; 51 text formats, 42 flat/tabular.
- 11 codecs; gzip/bz2/lzma/zip/raw are stdlib, lz4/lzo/brotli/snappy/zstd/7z via `[compression]`.
- Registry ↔ `datatypes/__init__.py` ↔ `dev/formats.json` are fully aligned (verified programmatically). One intentional orphan: `iterable/datatypes/zipped.py` (`ZIPSourceWrapper`) is in `READ_ONLY_FORMATS` but not a `FormatDescriptor`.

### 2.2 Dependency/extras drift (the main coverage risk)

Users can still see a format advertised and be unable to install its dependency through any extra:

- **Lakehouse formats have no declared dependencies at all**: `delta` (`deltalake`), `iceberg` (`pyiceberg`), `hudi` (`pyhudi`), `lance` (`pylance`). `_MODULE_INSTALL_EXTRAS` points delta/iceberg/lance at `[parquet]`, which only installs `pyarrow` — the hint is misleading.
- **`[all]` omits existing extras**: `cbor2` (`[cbor]`) and `spacepy` (`[cdf]`) are not in the `all` group.
- **Formats with runtime ImportError but no dedicated extra**: `avro`, `npy/npz` (numpy), `ubj`, `vcf` (vobject), `ods`, `rda`/`rds` (pyreadr), `capnp`, `thrift`, `fbs`, `flexbuf`, `smile`, `edn`, `hocon`, `der`, `bencode`, `gpx`, `ics`, `ldif`.
- **Metadata contradictions**: `_LLM_METADATA["avro"]` says "Read-only" while the descriptor and implementation are writable (Avro write shipped in 1.0.14); `docs/docs/formats/vcf.md` says writing is not supported while `vcf.py` implements `write()`/`write_bulk()`.
- README format categories omit some registered formats (LIBSVM, NumPy NPY/NPZ, others under "Other Formats").

### 2.3 VCF ambiguity

`iterable/datatypes/vcf.py` is vCard-only (`BEGIN:VCARD`, `vobject`), with the `vcard` alias, and README/docs/registry now consistently say so. Genomic Variant Call Format remains unsupported; `.vcf` files from bioinformatics pipelines will be mis-detected as vCard. A separate `genomic_vcf` handler keyed on `##fileformat=VCF` content magic (via `pysam`/`cyvcf2`) is the right fix.

### 2.4 Genuinely missing formats worth adding (grouped, with suggested libraries)

**Scientific / array / climate**

| Format | Library |
| --- | --- |
| Zarr (v2/v3) | `zarr`, `numcodecs` |
| FITS | `astropy` |
| GRIB/GRIB2 | `cfgrib` / `pygrib` |
| MATLAB `.mat` | `scipy.io`, `mat73` |
| ROOT | `uproot` |

**Geospatial**

| Format | Library |
| --- | --- |
| FlatGeobuf | `flatgeobuf` |
| GeoParquet (dedicated, metadata-aware) | `pyarrow` + GeoParquet spec (`geopandas` optional) |
| MBTiles | stdlib `sqlite3` |
| GeoJSONSeq / `.geojsonl` (RFC 8142) | per-line GeoJSON handler |
| WKT/WKB row formats | `shapely` |
| LAS/LAZ point clouds | `laspy` |

**Bioinformatics** (BAM/SAM/FASTA/FASTQ already exist)

| Format | Library |
| --- | --- |
| Genomic VCF / BCF | `pysam`, `cyvcf2` |
| CRAM | `pysam` |
| BED, GFF3/GTF | `gffutils`, `pysam` |

**Logs / observability / security** (CEF/GELF/Apache log/WARC/CDX already exist)

| Format | Library |
| --- | --- |
| HAR | stdlib JSON + schema |
| syslog (RFC 3164/5424) | `syslog-rfc5424-parser` |
| Windows EVTX | `python-evtx` |
| OTLP JSON/protobuf exports | `opentelemetry-proto` |

**ML / model artifacts**

| Format | Library |
| --- | --- |
| safetensors | `safetensors` |
| GGUF | `gguf` |
| ONNX (metadata/tensor iteration) | `onnx` |

**Containers / other**

| Format | Library |
| --- | --- |
| TAR (as multi-file container, incl. `.tar.gz`/`.tar.zst`) | stdlib `tarfile` |
| RAR (read-only) | `rarfile` |
| DICOM | `pydicom` |
| Apache Paimon | `pypaimon` |
| XLSM | `openpyxl` (partial) |

### 2.5 Fixture coverage

`dev/scripts/find_missing_fixtures.py` reports 142 gaps: 58 missing text+codec combinations (script only covers csv/json/jsonl/ndjson/xml × codecs) and 84 missing golden-read fixtures (28 of 112 formats have `2cols6rows.*`). Some of the 84 are impractical as generic fixtures (bam, pcap, delta, iceberg), so the realistic target is smaller — but high-value gaps (toml conformance, ubj, vcf, xlsb, zipxml, snappy/7z/lzo codec combos) remain.

---

## 3. Code Quality

### 3.1 Architecture — strong spine, uneven long tail

- `BaseIterable` → `BaseFileIterable` → format modules is a clean, typed contract with factory methods, validation hooks, read-ahead buffering, and a centralized `_handle_error()` with `on_error="raise"|"skip"|"warn"` policies.
- `format_registry.py` (832 lines, 108 descriptors) is a genuine single source of truth; lazy class loading avoids importing optional deps at import time.
- Mature formats (CSV, JSONL, XML, Parquet) are high quality; the tail (Hudi, SMILE, VCF, lakehouse) diverges sharply in error handling and streaming semantics. `hudi.py`'s docstring admits it is partial and its fallback path is `self.iterator = iter([])`.
- Naming confusion: `iterable/engines/duckdb.py` (`DuckDBEngineIterable`, file query engine) vs `iterable/datatypes/duckdb.py` (`DuckDBDatabaseIterable`, native DB files).

### 3.2 Error handling — the biggest systemic gap

- **296 `except Exception` blocks** (96 files); zero bare excepts. Distribution: ~90 in `datatypes/`, ~60 in `db/`, ~46 in `ai/`, 14 in `convert/core.py`, 10 in `pipeline/core.py`.
- **`_handle_error()` is used by only 3 of ~110 formats** (`csv.py`, `jsonl.py`, `xml.py`). Everything else bypasses the centralized error policy.
- **Silent data loss patterns** (malformed file reads as empty dataset):
  - `smile.py:53–66` — parse failure → `self.items = []`, no error.
  - `hudi.py:90` — unsupported API path → empty iterator.
  - `delta.py:118–119`, `hudi.py:161–162` — `list_tables()` returns `None` for dependency, path, and parse errors alike.
  - `open_iterable.py:107–108` — stream detection failure silently falls back to CSV.
- **Generic exceptions at the API boundary**: `open_iterable.py:119–120, 365–372` catch `Exception` and raise `RuntimeError` instead of an `IterableDataError` subclass.
- The custom hierarchy in `iterable/exceptions.py` (15 classes, error codes, actionable guidance) is well designed — the problem is adoption, not design.

### 3.3 Verified test-suite health (measured in this review)

Run in a base environment (no pyarrow/duckdb/dbfread/warcio/lxml/python-snappy), excluding stress/slow/benchmark/integration markers:

- **19 collection errors**: `tests/test_parquet.py`, `test_orc.py`, `test_dbf.py`, `test_duckdb*.py`, `test_totals.py` import optional classes at module top level (`from iterable.datatypes import ParquetIterable`) without `importorskip`, so missing extras break collection instead of skipping. Since `datatypes/__init__.py` swallows ImportError per class, the symbol is simply absent.
- **~60 of 68 failures are ImportError-as-failure** (WARC, HTML, Arrow, Snappy, detect tests) — same root cause: assertions/opens that should be skips when the extra is absent.
- **1 genuine product bug**: TOML write round-trip fails — `tomli_w` receives a list where it expects a dict (`AttributeError: 'list' object has no attribute 'items'` from `tests/test_format_conformance.py::TestWriteRoundTrip::test_write_read_round_trip[toml]`).
- **Stale tests after the `read_bulk` consolidation**: `tests/test_benchmarks.py` still iterates `read_bulk()` as a generator of chunks; it now returns a single `list[Row]`, so 6 benchmark tests fail on any environment.
- **Stale test after Avro write support**: `tests/test_ai_plan.py::test_plan_readonly_target_warning` expects a "read-only" warning for `.avro` targets that no longer applies.
- **Broken committed symlink**: `tests/testdata` existed locally as an 8-byte regular file containing "fixtures" rather than a symlink, causing ~150 spurious `FileExistsError`/`NotADirectoryError` failures. Restored to a proper symlink during this review. Consider a conftest guard that fails fast with a clear message if `tests/testdata` is not a symlink (this happens when the repo is checked out with `core.symlinks=false` or copied without symlink preservation).
- **Stress-test timeout**: `test_csv_10gb_streaming_read` exceeds the global 300 s `pytest-timeout` when stress tests are not deselected — the full default run (`pytest --verbose` per AGENTS.md) aborts mid-suite. Stress tests should carry their own `@pytest.mark.timeout` or be excluded by default addopts.

### 3.4 Typing, lint, complexity

- `py.typed` shipped; strict mypy on core modules (`base`, `detect`, `open_iterable`, `format_registry`, `utils`, `exceptions`, `types`); relaxed on `datatypes.*`/`codecs.*`/`db.*` — a pragmatic and reasonable split.
- Ruff: nearly clean (2 E501, 1 unformatted file — both in currently-modified working-tree files).
- Complexity: average A (4.37), but 9 E/F-rated functions concentrate risk:

| Function | Rating | Location |
| --- | --- | --- |
| `open_iterable` | F (91) | `iterable/helpers/open_iterable.py:123` (255 lines) |
| `doc.generate` | F (68) | `iterable/ai/doc.py:34` |
| `AnnotatedCSVIterable.read` | F (67) | `iterable/datatypes/annotatedcsv.py:254` |
| `convert` | F (65) | `iterable/convert/core.py:53` (333 lines) |
| `Pipeline.run` | F (54) | `iterable/pipeline/core.py:112` |
| `parse_line_protocol` | F (42) | `iterable/datatypes/ilp.py:11` |
| `_detect_capabilities` | F (41) | `iterable/helpers/capabilities.py:33` |
| `schema.infer` | E (34) | `iterable/ops/schema.py:20` |
| `detect_file_type` | E (32) | `iterable/helpers/detect.py:210` |

- Vulture (≥90% confidence): mostly `__exit__` signature false positives; real hits: unused `detect_dates` parameters in `iterable/ops/schema.py:22` and `iterable/ops/stats.py:39`.

### 3.5 Security posture

Bandit: 0 high-severity issues. Items worth attention:

| Pattern | Location | Assessment |
| --- | --- | --- |
| `eval()` on filter expressions | `iterable/ops/filter.py:117` | Restricted builtins, but still an expression-injection surface; consider `ast`-based evaluation |
| `eval(python_type)` | `iterable/helpers/validation.py:138` | Replace with an explicit type-name map |
| `pickle.load` | `iterable/datatypes/picklef.py` | Inherent to the format; docstring should warn about untrusted input |
| lxml parsing without XXE hardening | `xml.py:66`, `kml.py`, `gml.py`, `kmz.py:105` | No `defusedxml`; pass `resolve_entities=False, no_network=True` or document trust assumptions |
| ZIP member access | `zipped.py`, `kmz.py:94` | No `extractall()` anywhere (good); member names not canonicalized (low risk since nothing extracts to disk) |

### 3.6 Repo hygiene

- Tracked junk in git index: `.DS_Store`, `data.parquet`, `inddata.parquet`, `test_output.jsonl` (the latter three deleted in the working tree but still in the index/history).
- OpenSpec: `add-ai-block-documentation` archive move is in flight in the working tree; `LLM_READINESS_ROADMAP.md` is marked archived in content but lives outside `archive/`.
- No TODO/FIXME/HACK markers in production code.

---

## 4. Performance

### 4.1 Streaming vs full-load (the core finding)

Truly streaming and healthy: CSV, JSONL, XML (iterparse + `elem.clear()`), Parquet (`iter_batches`), ORC, Avro, BSON, MessagePack, PCAP, SQLite (cursor). JSON/GeoJSON/TopoJSON are hybrid: `ijson` streaming above a 10 MB threshold, `json.load` below or when `ijson` is missing.

Full-load formats that contradict the iterator promise on large inputs:

| Format | Problem | Evidence |
| --- | --- | --- |
| Arrow/Feather | Entire table read at `reset()` | `arrow.py:50` `feather.read_table()` |
| Lance | Full scan materialized before yielding | `lance.py:137–139` `scanner.to_table()` |
| Delta | Full `to_pyarrow_table()` at reset | `delta.py:48` |
| Iceberg | `scan.to_arrow().to_pylist()` | `iceberg.py:84` |
| Hudi | `to_pandas()` on whole table | `hudi.py:85–86` |
| Shapefile | All shapes/records built into `self.features` at reset | `shapefile.py:95–101` |
| XLSX | `load_workbook()` without `read_only=True` in main path (list_tables already uses it) | `xlsx.py:51` |
| CBOR / TOML / YAML | Hard full-file parse | `cbor.py:57–62`, `toml.py:49`, `yaml.py:42` |
| Annotated CSV | `readlines()` on entire file | `annotatedcsv.py:150` |
| Long tail | Whole-file parse in ~25 more modules (html, ini, hocon, feed, ical, jsonld, mhtml, eml, vcf, RDF text formats, ion, smile, ubjson, flexbuffers, capnp, thrift, bencode, mvt, stats formats) | grep `fobj.read()` |

Only 7 formats advertise `is_streaming() == True`; most streaming formats return the default `False`, and no full-load format signals its behavior — so users cannot programmatically distinguish them.

### 4.2 Bulk operations

Default `read_bulk` is a loop over `read()`. Real batch paths exist only for Parquet (both directions, `iter_batches` + `write_table`), Arrow reads, SQLite (`fetchmany`), and bulk writes for CSV (`writerows`), JSONL (concatenated write), ORC. Most other overrides are micro-optimizations, not vectorized I/O. Note the recent consolidation changed `read_bulk` to return one `list[Row]` — internal callers were updated but `tests/test_benchmarks.py` was not (see §3.3).

### 4.3 Codecs

gzip/bz2/lzma/lz4/brotli/zstd are streaming wrappers. **Snappy (`snappycodec.py:45–63`) and LZO (`lzocodec.py:35–43`) decompress the entire payload into a `BytesIO`** — any `.sz`/`.snappy`/`.lzo` compressed input negates streaming downstream. ZIP/7z open only the first archive member as a stream (partial but acceptable).

### 4.4 DuckDB engine

Good: `LIMIT ?/OFFSET ?` batched fetching (batch size 1000) for csv/jsonl/json/parquet with gz/zstd. Weak spots: callable filters in `totals()` do `SELECT *` and filter in Python (`engines/duckdb.py:528–532`); the dict-conversion fallback path uses `fetchall()` (`:618–621`); every row still becomes a Python dict, limiting the pushdown benefit.

### 4.5 Detection and helpers

Extension-based detection is O(1); content sniffing is bounded at 8 KB; encoding detection samples up to 1 MB. `JSONLinesIterable.totals()` and `AnnotatedCSVIterable.totals()` call `rowincount()`, which reads the entire file on every call — worth caching or documenting.

### 4.6 Benchmarks and regression gating

`tests/test_benchmarks.py` runs in default CI (and is currently broken, §3.3). `tests/test_performance_regression.py` exists but is inert: `tests/performance_baselines.json` is not committed, so every test skips. There is no enforced performance regression gate.

---

## 5. Prioritized Recommendations

### P0 — Correctness and trust

1. **Fix the TOML write round-trip bug** (`tomli_w` receives a list; wrap records into a table/array-of-tables document). This is a shipped-writable format that crashes on write.
2. **Make missing optional dependencies skip, not fail**: replace top-level `from iterable.datatypes import XIterable` in tests with `pytest.importorskip` or module-level `HAS_*` guards; today 19 test modules error at collection in a base env. Add a minimal CI job that runs the suite with *no* extras to keep this honest.
3. **Update stale tests**: `test_benchmarks.py` (new `read_bulk` list contract) and `test_ai_plan.py::test_plan_readonly_target_warning` (Avro is now writable).
4. **Guard the `tests/testdata` symlink**: a conftest check that raises a clear error when it is not a symlink (broken checkouts silently produce ~150 misleading failures).
5. **Declare lakehouse dependencies**: add `delta`/`iceberg`/`lance`(/`hudi`) extras or fold them into a `lakehouse` extra; stop pointing their install hints at `[parquet]`. Add `cbor`/`cdf` to `[all]`.
6. **Reconcile metadata contradictions**: Avro `_LLM_METADATA` "Read-only" vs writable descriptor; `docs/docs/formats/vcf.md` write claim vs implementation.

### P1 — Systemic quality

7. **Drive `_handle_error()` adoption**: migrate at least the silent-failure offenders (SMILE, Hudi, VCF, Parquet write-alignment) and make "malformed non-empty file must not read as zero rows" a conformance test across formats.
8. **Expose streaming truthfully**: override `is_streaming()` in the ~10 streaming formats that return the default `False`, and return `False` (or add a `memory_bound` capability flag) for the full-load formats so `open_iterable` callers and the AI planner can reason about memory.
9. **Fix the two non-streaming codecs** (Snappy, LZO) using the same file-like wrapper pattern as gzip/zstd; snappy has a framed streaming API.
10. **Convert top full-load readers to lazy iteration**: Shapefile (iterate the reader), Arrow (record-batch reader), Lance (`scanner.to_batches()`), Delta/Iceberg/Hudi (scan batch iterators), XLSX (`read_only=True`).
11. **Decompose the F-rated god functions** (`open_iterable`, `convert`, `bulk_convert`, `Pipeline.run`) into detect → validate → instantiate → configure stages; they are the hardest code to test and the most likely regression sites.
12. **Stress-test timeouts**: per-test `@pytest.mark.timeout` on 10 GB tests, and exclude `stress`/`slow` in default addopts so `pytest --verbose` (as documented in AGENTS.md) passes.
13. **Commit performance baselines** (`tests/performance_baselines.json`) and run the regression suite in one CI leg; exclude `benchmark` marker from the default matrix.

### P2 — Growth

14. **Split genomic VCF from vCard**: new `genomic_vcf` descriptor with `##fileformat=VCF` content magic (`pysam`), then BCF/CRAM/BED/GFF3 as a `bio` extra.
15. **Add the highest-leverage missing formats**: TAR-as-container (stdlib, cheap, unlocks `.tar.gz` datasets), GeoJSONSeq (trivial on top of JSONL), Zarr, MATLAB `.mat`, FlatGeobuf, GeoParquet metadata awareness, HAR, syslog, safetensors/GGUF.
16. **Shrink fixture gaps with a non-regression budget**: fail CI only if the missing-fixture count increases; extend the codec matrix in the script to snappy/7z/lzo.
17. **Security hardening**: XXE-safe lxml defaults (`resolve_entities=False, no_network=True`), replace `eval` in `validation.py:138` with a type map, and add an untrusted-input warning to the pickle format docs.
18. **Hygiene**: purge `.DS_Store`/`data.parquet`/`inddata.parquet`/`test_output.jsonl` from the index, finish the OpenSpec archive move, and relocate `LLM_READINESS_ROADMAP.md` under `archive/`.

### Quick wins (each < 1 hour)

- Fix the 2 E501 lint errors and run `ruff format tests/test_parquet.py`.
- Remove the unused `detect_dates` parameters (`ops/schema.py:22`, `ops/stats.py:39`) or wire them up.
- Add `cbor2` and `spacepy` to `[all]`.
- Conftest symlink guard for `tests/testdata`.
- Correct the Avro "Read-only" limitation string in `_LLM_METADATA`.

---

## Appendix: Evidence and Commands

```bash
ruff check iterable tests --statistics          # 2 × E501
ruff format --check iterable tests              # 1 file would be reformatted
radon cc iterable --min C -s --total-average    # avg A (4.37); 9 E/F functions
bandit -r iterable -ll -q                       # 0 high, 34 medium, 71 low
vulture iterable --min-confidence 90
python dev/scripts/find_missing_fixtures.py     # 142 gaps (58 + 84)
pytest -q --continue-on-collection-errors \
  -m "not stress and not slow and not benchmark and not integration"
# = 1962 passed, 68 failed, 361 skipped, 19 collection errors (base env, no heavy extras)
```

Registry counts measured via `iterable.helpers.format_registry.iter_descriptors()` / `build_datatype_registry()`. The `tests/testdata` symlink was restored to its committed state (`ln -s fixtures tests/testdata`) during this review; before the fix the same pytest invocation produced 221 failures.
