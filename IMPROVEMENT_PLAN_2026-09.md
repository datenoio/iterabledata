# IterableData — Improvements Plan (September 2026)

**Date:** 2026-09-18 · **Code state:** `main` @ `2764b3b`, version 1.0.23 · **re-verified same day** (all headline claims re-run live; corrections applied, see §8)
**Supersedes:** `IMPROVEMENT_PLAN.md` (2026-06-12, ~85% executed — status folded into §2)
**Method:** Three-track audit — feature inventory, quality measurement (tests/lint/types/security/complexity/deps), and OpenSpec/docs consistency review.

---

## 1. Executive summary

IterableData is in strong shape: **145 registered formats** (88 writable / 57 read-only; 115 stable, 26 experimental, 4 partial), **11 codecs**, DuckDB + internal engines, mature ops/convert/validate/AI/MCP/plugin layers, ~50.6k LOC with 186 test files, **0 lint errors, 0 high-severity security findings, and docs coverage for all 145 formats**.

The real risks are not missing features but **process drift and polish debt**:

1. **1 failing test** (XLSX totals) and a **broken pytest-xdist** combo on pytest 9.
2. **33 unarchived OpenSpec changes** (23 complete, 10 half-finished) — the spec tracker no longer reflects reality.
3. **Stale status artifacts**: `UNFINISHED_PROPOSALS.md`, `IMPROVEMENT_PLAN.md`, `dev/formats.json` (121 vs 145 formats), `AGENTS.md` DuckDB note.
4. **Environment-fragile quality gates**: mypy core gate fails when optional deps (polars/fsspec) are installed; coverage gate measures 63.8% in the full-extras dev venv but ~23.6% in a base env — one number can't honestly serve both; dev venv carries 131 known vulnerabilities (re-audit pending — PyPI unreachable from dev env).
5. **Planned P2 features that stalled**: async Phase 2, ingest parity (ClickHouse/MSSQL), write support for xlsx/xml/ods, validation-hooks rollout, reference plugin package.

**Recommended first week:** fix the failing test, archive the 23 completed changes, refresh the stale artifacts, repair xdist — all low-risk, high-clarity wins — then pick at most two P2 feature tracks per release.

---

## 2. Where the previous plan stands

June 2026 plan (`IMPROVEMENT_PLAN.md`): all P0 housekeeping, P1 testing/CI, and P2 docs/DX items are **done** (SQL-injection hardening, iterator contracts, format registry, module splits, docs deployment, release pipeline unification, uncovered-format tests, conformance suite). The **partial/not-done** remainder forms the feature backlog in §5:

| Item | State | Evidence |
|---|---|---|
| 3.5 Typing/mypy rollout | Partial | Strict gate on 12 core modules; full-package mypy advisory with 1,369 errors |
| 4.4 Coverage bar | Regressed scope | `fail_under` recalibrated to 50 (1.0.22) instead of raised toward 85 |
| 6.1 Write support for read-only formats | **Done (xlsx/xml/ods)** | Avro/Delta/Iceberg writable; xlsx/xml/ods writable since 2026-09-27 (`add-office-format-writes`); hdf5, netcdf still read-only |
| 6.2 Async Phase 2 | **Done** | `aopen_iterable()` offloads open/detection via `asyncio.to_thread`, exported from `iterable/__init__.py`, documented in README + docs (`add-genuine-async-iteration`, archived 2026-09-27) |
| 6.3 DB parity | **Done** | ClickHouse + MSSQL ingest backends added (insert-only); pooling opt-in for mysql/mssql/mongo/clickhouse/elasticsearch (`add-db-ingest-parity`, archived 2026-09-27) |
| 6.4 Validation hooks everywhere | **Done** | Hooks on all 92 writable formats + registry-driven conformance guard (`add-validation-hooks-rollout`, archived 2026-09-27) |
| 6.5 Plugin ecosystem | Partial | Loader/registry/docs exist; no published reference plugin |

July 2026 review (`REPOSITORY_REVIEW_REPORT.md`): release engineering, packaging, fixture hermeticity, and placeholder docs are **fixed**; what remains is governance hygiene, the environment-sensitive mypy gate, and the stale catalog JSON.

---

## 3. Quality snapshot (measured 2026-09-18, `.venv`, Python 3.13.7)

| Area | Result | Verdict |
|---|---|---|
| Tests | 2,553 passed / **1 failed** / 321 skipped (64.3 s serial) | ⚠️ Fix XLSX totals |
| pytest-xdist | Execution broken: `-n 2` runs 0 tests ("no tests ran"); `--collect-only` collects 2,899 fine | ⚠️ Broken |
| Ruff lint + format | 0 errors; 446 files formatted | ✅ |
| mypy (full pkg) | 1,369 errors / 199 files (advisory by policy) | ⚠️ Noise hides signal |
| mypy (core gate) | Fails w/ 2 unused-`type: ignore` errors when polars/fsspec installed | ⚠️ Environment-fragile |
| Bandit | 0 high · 31 medium (B608 f-string SQL across 14 files) · 132 low | ⚠️ Triagable |
| Radon complexity | Avg A (4.14); **190 blocks ≥ C, 50 ≥ D** | ⚠️ Concentrated |
| Vulture | 17 findings, all protocol-signature false positives | ✅ |
| Coverage | 63.81% full-extras `.venv` (2026-09-18, floor passed); 23.56% base env (2026-08-10) | ⚠️ Two-number problem |
| Dependencies | 131 known vulns in 16 venv packages (re-audit blocked: PyPI unreachable) | ⚠️ Refresh venv |
| Code size | 50,652 LOC lib / 34,745 LOC tests | — |

Worst complexity offenders (grade D): `paimon_row.normalize_schema` (29), `gml.gml_to_geojson` (28), `ical.write_bulk` (27), `shapefile.write` (26), `kml.write` (26), `base.BaseFileIterable.reset` (24), `gml.write` (24), `cef._parse_cef` (21).

---

## 4. P0 — Stabilize and reconcile (week 1, no OpenSpec proposals needed)

Bug fixes and housekeeping; per OpenSpec rules these are done directly.

- [x] **4.1 Fix `XLSXIterable.totals()` shape** — DONE 2026-09-21 (`c709473`): `totals()` returns int with `_total_rows` fallback; totals + xlsx suites green.
- [x] **4.2 Repair pytest-xdist** — DONE 2026-09-21 (`c7b0269` + conftest follow-up): root causes were pytest-benchmark 5.2.3 crashing workers (now `>=5.3`, pytest pinned `<9`) AND `tests/conftest.py` import-time `os.chdir` (moved to `pytest_configure` with absolute-path rewrite for controller and workers). `pytest -n auto --no-cov` runs the full suite green from a relative path; coverage stays serial (63.72%, floor passes).
- [x] **4.3 Archive 23 completed OpenSpec changes** — DONE 2026-09-21 (`04e122a`): all archived with spec updates; 21 new capability specs; `openspec validate --all --strict` 73/73; 10 incomplete changes remain.
- [x] **4.4 Refresh stale status artifacts** — DONE 2026-09-21 (`d8055a9`): `dev/formats.json` regenerated (145), `UNFINISHED_PROPOSALS.md` rewritten, AGENTS.md DuckDB note fixed, `.DS_Store` untracked.
- [x] **4.5 Refresh dev venv** — DONE 2026-09-21: pip/setuptools/wheel/requests/urllib3/authlib/pygments upgraded; pyarrow 19→25 kept with zero test regressions (`pip check` flags formal pypaimon/pyducklake pins); pip-audit 133→97 rows (remaining: anyio, click, cryptography, idna, jaraco-context, lxml, msgpack, nltk, pytest).

*(A previous draft item "add cram docs page" was withdrawn on re-verification: all 145 registry `doc_url` targets resolve on disk — cram points to the shared `genomic-intervals.md`, which exists and covers CRAM.) **Postscript 2026-09-21:** a dedicated `docs/docs/formats/cram.md` was nonetheless added (`9ee98c8`) with sidebar/index/cross-links and the registry `doc_url` retargeted; the Docusaurus production build verifies all links. Revert `9ee98c8` if the shared-page approach is preferred.*

## 5. P1 — Quality gates that tell the truth (weeks 2–4)

Most items here change CI/tooling behavior → create one OpenSpec change `strengthen-quality-gates-2` (or fold into the existing open `strengthen-repository-quality-gates`, 7/20 tasks).

- [x] **5.1 Fix mypy core gate environment sensitivity** — DONE 2026-09-21 (`c7b0269`): polars/fsspec added to `ignore_missing_imports`, obsolete inline `type: ignore` comments dropped; the exact CI core-gate command passes with optional deps installed.
- [x] **5.2 mypy ratchet** — DONE 2026-09-21 (scaffolding): `dev/scripts/mypy_ratchet.py` + committed baseline (1,359 errors); advisory CI step; becomes blocking once the baseline proves stable in CI. Per-package burn-down remains open.
- [x] **5.3 Coverage clarity** — DONE 2026-09-21: CI now prints explicit base-env (advisory) and full-dev-env coverage floor checks; full-extras serial coverage measured at 63.72% (floor 50 passes). Stale `coverage.xml` refreshed by new runs.
- [x] **5.4 Triage B608 ×31** — DONE 2026-09-21 with a better outcome than planned: 5 REAL injection gaps fixed (DuckDB/SQLite datatype identifier quoting incl. file-catalog table names, MDB `]` escaping, mysqldump backticks, ClickHouse backslash literals); remaining sites verified safe and annotated; package-wide bandit 0 medium/high.
- [x] **5.5 Complexity budget** — DONE 2026-09-21: all 9 grade-D functions refactored to ≤C (behavior-preserving, full suite green). Advisory radon gate added in CI. Note: ~45 further D/E/F functions exist outside the §3 list (e.g. `annotatedcsv`, `ilp`, `helpers/detect`, `dxf`) — gate can go blocking once those are addressed.
- [x] **5.6 Governance files** — DONE 2026-09-21: `SECURITY.md`, `CODE_OF_CONDUCT.md` (Contributor Covenant 2.1), `.github/CODEOWNERS`.
- [x] **5.7 Python 3.13 CI leg** — DONE 2026-09-21: matrix is now 3.10–3.13.

## 6. P2 — Finish what's started (next 1–2 releases)

Ten OpenSpec changes are half-finished. **Decision first:** either schedule completion or explicitly scope-down and archive. Recommended order by user-visible value:

1. ~~**`unify-format-capability-metadata`** (6/14)~~ — **DONE 2026-09-21** (`3d3219d`, archived `2026-09-21-…`): all 145 descriptors populated (extras, magic as source of truth, memory profiles, native-bulk, codec/selection/source constraints); stale legacy tables deleted and derived; 18 conformance tests; catalog schema 1.2. Fixed real drift bugs (old tables missed up to 32 ids).
2. ~~**`add-native-batch-conversion`** (10/17)~~ — **DONE 2026-09-21** (`fffd6b4`, archived `2026-09-21-…`): ORC dual backend, projection/predicate pushdown (Parquet + Delta/Iceberg/Lance), table/variable/slice pushdown (NumPy/HDF5/NetCDF), 46 equivalence tests, benchmarks — native path cuts peak memory 16× (2.6 MB vs 42 MB at 50k rows); write-path flush amortization noted as follow-up for `optimize-format-io-hot-paths`.
3. ~~**`optimize-format-io-hot-paths`** (14/17) + **`add-codec-performance-profiles`** (11/16)~~ — **DONE 2026-09-21/22** (`2b43c56`, `0cc0a9c`, both archived `2026-09-22-…`): 75 interleaved cursor conformance tests across all 37 custom bulk readers; perf gate 5/5 with baselines untouched; codec benchmark suite (162 tests) + 121 precedence/round-trip/threshold tests with deterministic fixtures. (The batch write-flush amortization finding remains available as a future optimization; not needed by the archived change.)
4. ~~**Format hardening batch**~~ — **DONE 2026-09-22** (all four archived `2026-09-22-…`): `add-zarr-format` (15/15, `b561d56` — zarr 3.x compat, chunk-bounded selection reads, write mismatch guards, v2/v3 golden fixtures), `add-geoparquet-flatgeobuf-formats` (16/16, `db31a4b` — geo metadata reads, FlatGeobuf magic/writes, fixed silently-broken bbox path), `extend-bioinformatics-formats` (17/17, `5ab9d60` — 47 tests; exposed and fixed 4 real bugs: CRAM error wrapping, GFF3 FASTA-tail crash, BED error locations, BED writer header loss), `add-otlp-format-profiles` (18/18, `b83a37b` — ijson streaming reads, write-time metric validation, conservative detection, official-proto fixtures). Also fixed a latent GeoPackage overwrite bug exposed by the fiona install (`3016a63`). Suite now fully green: 3,023 passed / 0 failed.
5. **`harden-release-artifacts`** (15/17) — one clean-checkout build exercise + one approved release run.
6. **`strengthen-repository-quality-gates`** (12/23) — progressed during P1 (ratchet, radon gate, coverage floors, 3.13 leg checked off); remaining: per-family coverage, per-package mypy burn-down, making advisory gates blocking.

Feature tracks from the June plan (each needs its own OpenSpec proposal when scheduled):

- [x] **6.1 Write support: xlsx, xml, ods** (highest-demand read-only formats; hdf5/netcdf later) — **DONE 2026-09-27** (`add-office-format-writes`, archived `2026-09-27-…`): buffered typed writers for XLSX/ODS, streaming XML writer mirroring reader conventions, validation hooks wired, registry/catalog/docs updated, convert round-trips tested (suite 3351 passed / 0 failed)
- [x] **6.2 Async Phase 2** — **DONE 2026-09-27** (`add-genuine-async-iteration`, archived `2026-09-27-…`): `aopen_iterable()` offloads detection/open via `asyncio.to_thread` (event loop never blocked), false docstring claim fixed, exported from `iterable/__init__.py`, README + `docs/docs/api/async.md` updated, 6 parity/concurrency tests
- [x] **6.3 Ingest parity** — ClickHouse + MSSQL backends; extend pooling beyond postgres — **DONE 2026-09-27** (`add-db-ingest-parity`, archived `2026-09-27-…`): insert-only backends with clear upsert errors, opt-in pooling across 5 drivers, 38 mocked tests + docker-gated integration tests
- [x] **6.4 Validation hooks rollout** — from ~8 to all writable formats (mechanical, registry-driven) — **DONE 2026-09-27** (`add-validation-hooks-rollout`, archived `2026-09-27-…`): 77 formats wired, delegation-aware placement, conformance guard test, annotatedcsv all-skipped crash fix
- [ ] **6.5 Reference plugin package** — publish one example plugin to validate the ecosystem story

## 7. P3 — Opportunistic / backlog

- README async section and 1.0.21 nested-data features (`flatten_nested`, `ai.table_profile`) into `docs/`.
- SMILE/FlexBuffers: backends remain non-installable — either vendor a pure-python fallback or document as permanent ImportError-only.
- Tier-2 science formats absent entirely: FITS, DICOM, safetensors, GGUF (July review).
- CI Node 20 → 22/24 for docs/deploy actions.
- `llms.txt` freshness check in CI (last refreshed 2026-08-19; good candidate for a scheduled job).

---

## 8. Process notes

- **Approval gate:** §5–§6 items that change behavior get OpenSpec proposals before implementation; §4 fixes proceed directly.
- **Sequencing rule of thumb:** never more than two P2 tracks in flight per release; archive-before-new — no new change proposals until the 33-change backlog drops below 10.
- **Success metrics for Q4:** 0 failing tests with `-n auto` working; openspec backlog ≤ 10 active changes; mypy gate green in both CI and full-extras dev envs; 0 grade-D functions; coverage gate enforced against a number CI actually measures.

---

*Audit evidence: feature inventory from `iterable/helpers/format_registry.py`, `pyproject.toml`, package walk; quality numbers from live runs of pytest 9.0.2 / ruff / mypy / bandit 1.8.3 / radon / vulture / pip-audit in `.venv`; consistency findings from OpenSpec CLI (`validate --all --strict` passes 75/75), CHANGELOG through 1.0.23, and docs-tree comparison.*

*Re-verification pass (2026-09-18, second run): every headline claim re-checked by live re-runs — registry counts (145/88/57, maturity 115/26/4, extras 23, magic 0, codec_support 3), OpenSpec backlog (33 active: 23 complete, 10 half-finished), stale artifacts, radon grade-D list, bandit totals, XLSX totals failure, mypy gate fragility, xdist breakage, all 145 `doc_url` targets. Corrections applied: cram docs claim withdrawn (§4), B608 distribution fixed (§5.4), xdist symptom refined (§4.2), fresh test/coverage numbers (§3), async docstring mismatch added (§6.2). pip-audit could not re-run (PyPI unreachable from dev env); the 131-vuln figure stands as prior measurement.*
