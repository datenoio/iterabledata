# Change: Add Apache Paimon Table Support

## Why

IterableData now reads/writes Paimon **file** formats (Row and Mosaic), but users still cannot open a full Paimon **table** (catalog, snapshots, primary-key / append tables, changelog materialization) the way they open Delta, Iceberg, or Hudi. Closing that gap with `pypaimon` makes Paimon a first-class lakehouse table source, not only a pair of file codecs.

## What Changes

- Add experimental `PaimonTableIterable` (canonical id `paimon`) backed by `pypaimon` catalog/table APIs.
- Support warehouse/catalog + database/table selection, `list_tables()`, snapshot/branch options where the SDK exposes them, and bounded row iteration.
- Add optional `paimon-table` extra (`pypaimon`) and extend the convenience `paimon` extra to include table + file format deps.
- Keep existing `paimon_row` / `paimon_mosaic` file iterables unchanged; document when to use files vs tables.
- Add fixtures, tests, and docs for catalog-oriented workflows.

## Impact

- Affected specs: `paimon-table-format` (new)
- Affected code: new datatype module, format registry, extras, tests, docs; may adjust `paimon` convenience extra composition
- New dependency: `pypaimon` (optional)
- Coordinates with completed `add-paimon-row-mosaic-formats` (file-level support remains separate)
- Maturity: **experimental** until catalog round-trips and snapshot reads are covered
