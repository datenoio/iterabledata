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
| 6.1 Write support for read-only formats | Partial | Avro/Delta/Iceberg writable; xlsx, xml, ods, hdf5, netcdf still read-only |
| 6.2 Async Phase 2 | Not done | `aopen_iterable()` still a sync wrapper, not exported, absent from README |
| 6.3 DB parity | Partial | 8 read drivers vs 6 ingest backends; pooling only used by postgres |
| 6.4 Validation hooks everywhere | Partial | Hooks on ~8 formats of ~88 writable |
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

- [ ] **4.1 Fix `XLSXIterable.totals()` shape** — `tests/test_totals.py::test_totals_match_record_count[...xlsx...]` fails: `totals()` returns a dict where the contract expects an int. Align return shape or fix normalization.
- [ ] **4.2 Repair pytest-xdist** — pin pytest <9 or upgrade xdist; test *execution* under `-n` currently runs 0 items ("no tests ran" in 0.35 s) even though `--collect-only` collects 2,899 tests, silently defeating the documented parallel workflow in `AGENTS.md`.
- [ ] **4.3 Archive 23 completed OpenSpec changes** — run `openspec archive <id> --yes` for each completed change; this also creates the missing capability specs for Zarr, GeoParquet, OTLP, Paimon, DuckLake, and the open-data pack.
- [ ] **4.4 Refresh stale status artifacts** — regenerate `dev/formats.json` from the registry (145 ids), update or delete `UNFINISHED_PROPOSALS.md`, correct the `AGENTS.md` DuckDB note (parquet is supported), untrack `.DS_Store`.
- [ ] **4.5 Refresh dev venv** — upgrade pip, authlib, pyarrow, requests, urllib3, setuptools, wheel, pytest (131 known vulns; all dev-side; re-audit once PyPI is reachable).

*(A previous draft item "add cram docs page" was withdrawn on re-verification: all 145 registry `doc_url` targets resolve on disk — cram points to the shared `genomic-intervals.md`, which exists and covers CRAM.)*

## 5. P1 — Quality gates that tell the truth (weeks 2–4)

Most items here change CI/tooling behavior → create one OpenSpec change `strengthen-quality-gates-2` (or fold into the existing open `strengthen-repository-quality-gates`, 7/20 tasks).

- [ ] **5.1 Fix mypy core gate environment sensitivity** — gate currently passes in CI (`pip install .[dev]`) but fails in dev envs where polars/fsspec exist (unused `type: ignore` at `dataframe_adapters.py:44`, `open_iterable.py:167`). Make the gate hermetic: pin the check environment or use per-module overrides.
- [ ] **5.2 mypy ratchet** — adopt the ratchet task already scoped in `strengthen-repository-quality-gates`: baseline current error count, forbid growth, burn down per package.
- [ ] **5.3 Coverage clarity** — publish two numbers: base-env floor (keep `fail_under = 50` honest) and full-extras coverage in CI/codecov; current committed `coverage.xml` (23.56%) is stale and misleading.
- [ ] **5.4 Triage B608 ×31** — spread across 14 files: 6 each in `datatypes/sqlite.py` and `datatypes/duckdb.py`, 4 in `engines/duckdb.py`, remainder in `db/*` (7) and `ingest/*` (6). All are f-string SQL with quoted identifiers. Either switch to the `identifiers.py` helper everywhere or annotate verified-safe lines with `nosec` + justification.
- [ ] **5.5 Complexity budget** — refactor the 9 grade-D functions listed in §3 (geospatial/calendar writers + `BaseFileIterable.reset`); add a radon gate at grade D to prevent regression.
- [ ] **5.6 Governance files** — add `SECURITY.md`, `CODE_OF_CONDUCT.md`, `CODEOWNERS` (July review finding, still open).
- [ ] **5.7 Python 3.13 CI leg** — dev env already runs 3.13.7 green; add it to the matrix (and watch 3.14).

## 6. P2 — Finish what's started (next 1–2 releases)

Ten OpenSpec changes are half-finished. **Decision first:** either schedule completion or explicitly scope-down and archive. Recommended order by user-visible value:

1. **`unify-format-capability-metadata`** (6/14) — populate `extras` (23/145 today) and decide whether `magic` bytes move into the registry (0/145) or stay in `content_detection.py`; derive `codec_support` for the 142 formats lacking it. This is the metadata backbone for catalog/detect quality.
2. **`add-native-batch-conversion`** (10/17) — ORC/lakehouse/scientific adapters + pushdown; biggest performance lever left.
3. **`optimize-format-io-hot-paths`** (14/17) + **`add-codec-performance-profiles`** (11/16) — finish conformance tests, baselines, codec benchmark thresholds; small remaining scope.
4. **Format hardening batch** — `add-zarr-format`, `add-geoparquet-flatgeobuf-formats`, `extend-bioinformatics-formats`, `add-otlp-format-profiles`: mostly golden fixtures and edge-case tests; promote 26 experimental formats toward stable.
5. **`harden-release-artifacts`** (15/17) — one clean-checkout build exercise + one approved release run.

Feature tracks from the June plan (each needs its own OpenSpec proposal when scheduled):

- [ ] **6.1 Write support: xlsx, xml, ods** (highest-demand read-only formats; hdf5/netcdf later)
- [ ] **6.2 Async Phase 2** — make `aopen_iterable()` genuinely async (today it calls sync `open_iterable()` inline in `iterable/helpers/async_detect.py`, and its docstring falsely claims a thread-pool executor — fix both), export from `iterable/__init__.py`, document in README
- [ ] **6.3 Ingest parity** — ClickHouse + MSSQL backends; extend pooling beyond postgres
- [ ] **6.4 Validation hooks rollout** — from ~8 to all writable formats (mechanical, registry-driven)
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
