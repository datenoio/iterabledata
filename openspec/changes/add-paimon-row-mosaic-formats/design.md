## Context

Apache Paimon documents multiple first-party file formats. Two of interest here:

1. **Row (`.row`)** — row-oriented blocks with ZSTD Level 1 compression, delta/ZigZag/varint block index, and a fixed 32-byte footer ending in magic `0x524F5753` (`ROWS`). Optimized for O(1) access by global row number (deletion vectors, changelog materialization). The binary layout is fully specified; schema is **not** embedded in the file.
2. **Mosaic** — columnar-bucket hybrid format for wide tables (10k+ columns). Footer magic `MOSA` (`0x4D4F5341`). Official Python bindings are on PyPI as `paimon-mosaic` and expose PyArrow `RecordBatch` / `Table` I/O with bucket-level projection.

IterableData already supports related lakehouse/columnar formats (Delta, Iceberg, Hudi, Lance, Vortex) and converts Arrow batches to dict rows.

## Goals / Non-Goals

- Goals:
  - Stream Paimon Row and Mosaic files through `open_iterable()` as dictionary rows.
  - Detect by extension and, for seekable sources, by footer magic.
  - Support read and write with clear optional-dependency install hints.
  - Keep peak memory bounded by block/row-group/batch size where the backend allows.
  - Prefer maintained upstream libraries over reimplementing codecs.
- Non-Goals:
  - Full Paimon catalog / table / snapshot / merge-engine semantics (that remains `pypaimon`'s job).
  - Implementing Mosaic's Rust core in pure Python.
  - Guaranteeing every Paimon nested type (VARIANT, deep ROW) in the first experimental cut.
  - Changing existing Delta/Iceberg/Hudi/Lance/Vortex behavior.

## Decisions

### Format identities

| Format | Canonical id | Aliases | Extension(s) | Footer magic |
|--------|--------------|---------|--------------|--------------|
| Paimon Row | `paimon_row` | `row` (only when extension/magic disambiguate) | `.row` | `ROWS` |
| Paimon Mosaic | `paimon_mosaic` | `mosaic` | `.mosaic` | `MOSA` |

Alias `row` MUST NOT claim arbitrary paths named without `.row` or `ROWS` footer validation, to avoid colliding with generic “row” wording.

### Dependencies

- **Mosaic**: optional extra `paimon-mosaic` → `paimon-mosaic>=0.2.0` (imports as `mosaic`, requires `pyarrow`).
- **Row**: optional extra `paimon-row` → `pypaimon` at a version that includes `FormatRowReader` / row file writers (target ≥ current stable with ROW support). Prefer calling pypaimon's file-format primitives for interoperability; if public standalone file APIs are insufficient, implement a thin reader/writer against the published `.row` spec using `zstandard`, still declaring the `paimon-row` extra for the supported path.
- Convenience extra `paimon` installs both. Do **not** fold these into the existing `lakehouse` extra without an explicit follow-up (keeps install weight opt-in).

### Schema for Row files

Because `.row` files do not store schema in the footer, reads SHALL require an explicit schema via `iterableargs` (e.g. Arrow schema, list of `(name, type)` pairs, or a documented Paimon field list). Writes SHALL infer schema from the first batch when possible, or accept an explicit schema. Missing schema on read fails with a clear error naming the required argument.

### Detection

Current content detection matches **leading** magic only. Both Paimon formats put magic in a **trailing** 32-byte footer. Therefore:

1. Extension detection (`.row`, `.mosaic`) is the primary path.
2. For seekable file objects/paths, add footer sniffing (read last 32 bytes, validate magic and reserved fields) analogous to TAR's non-prefix magic handling.
3. Non-seekable streams without an explicit `format=` argument remain unsupported for automatic detection.

### Row iteration model

- **Mosaic**: iterate row groups via `MosaicReader.read_row_group()`, convert each `RecordBatch` to dict rows (reuse existing Arrow→dict helpers). Honor `project`/`columns` by calling `reader.project(...)` before reading so only relevant buckets decompress.
- **Row**: iterate blocks (or use library iterators); yield one dict per decoded row. Optional `row_numbers` / selection bitmaps map to selection pushdown when the backend supports it; otherwise document as unsupported in v1.
- `totals()` for both formats SHOULD use footer/`totalRowCount` / row-group metadata without a full scan when available.
- Writers buffer at most one configured block / row group / batch before flush; declare `write_memory` accurately in capability metadata.

### Maturity and interoperability

Both formats start as **experimental**. Stabilize after:

- Round-trip fixtures produced by IterableData.
- At least one golden fixture produced by Java Paimon and/or `pypaimon` / `paimon-mosaic` tooling that IterableData can read.

## Risks / Trade-offs

- **Schema-less `.row` files** → Mitigation: require explicit schema; document sidecar/schema JSON pattern.
- **`pypaimon` is catalog-oriented** → Mitigation: prefer file-format modules; fall back to published binary spec for primitives; keep nested types scoped.
- **Platform wheels for `paimon-mosaic`** → Mitigation: clear ImportError; CI matrices cover available wheels; skip tests when wheels absent.
- **Footer magic vs leading-byte detector** → Mitigation: extension-first + dedicated footer sniffer; do not overload `match_magic_prefix`.
- **Wide Mosaic tables** → Mitigation: default to projection when `columns` is set; avoid `read_all()` on the hot path.

## Migration Plan

1. Land experimental descriptors, detection, Mosaic read (row-group streaming), then Mosaic write.
2. Land Row read with required schema, then Row write with block flush.
3. Add golden cross-tool fixtures and mark maturity stable only after those pass.
4. No breaking changes to existing formats.

## Open Questions

- Should alias id `row` be registered globally, or only resolved when the path ends with `.row` / footer validates (preferred)?
- Exact minimum `pypaimon` version that exposes stable standalone ROW file APIs on PyPI.
- Whether Mosaic should also accept extension-less Paimon data-file naming conventions used inside warehouses, or require `.mosaic` / explicit `format=`.
