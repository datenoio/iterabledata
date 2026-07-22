# Change: Add Apache Paimon Row Format and Mosaic Support

## Why

Apache Paimon now defines two specialized file formats that IterableData does not yet cover: the [Row format](https://paimon.apache.org/docs/master/concepts/spec/rowformat/) (`.row`) for O(1) row-number lookups, and [Mosaic](https://paimon.apache.org/docs/mosaic/) for wide-table columnar-bucket storage with projection pushdown. Supporting both as first-class iterables closes a lakehouse gap beside existing Delta, Iceberg, Hudi, Lance, and Vortex formats and lets users stream Paimon data files through the same `open_iterable()` API.

## What Changes

- Add experimental `PaimonRowIterable` for Paimon `.row` files (read/write, footer magic `ROWS`).
- Add experimental `PaimonMosaicIterable` for Mosaic files (read/write, footer magic `MOSA`).
- Register both formats in the format descriptor/registry with extension and seekable footer-magic detection.
- Add optional dependency extras: `paimon-row` (`pypaimon`) and `paimon-mosaic` (`paimon-mosaic`), plus a convenience `paimon` extra that installs both.
- Convert Arrow / pypaimon batches to dictionary rows consistent with other columnar formats.
- Add golden fixtures, round-trip tests, missing-dependency errors, docs, and capability metadata.

## Impact

- Affected specs: `paimon-row-format` (new), `paimon-mosaic-format` (new)
- Affected code: new datatype modules, format registry/detection, optional extras in `pyproject.toml`, tests, fixtures, format docs, README lakehouse list
- New dependencies (optional): `pypaimon` for Row; `paimon-mosaic` (+ `pyarrow`) for Mosaic
- Maturity: both formats ship as **experimental** until interoperability fixtures against Java/PyPaimon-produced files pass
