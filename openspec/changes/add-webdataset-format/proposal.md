# Change: Add WebDataset Format Support

## Why

WebDataset (`webdataset`, ~1.8k in Dateno stats) is a widely used ML shard format (TAR of samples with co-located extensions like `.jpg`/`.json`/`.cls`). IterableData already has TAR container support; a first-class WebDataset profile should group members into sample dicts for training/ETL pipelines.

## What Changes

- Add a `webdataset` / `wds` format profile that iterates TAR shards as sample records.
- Group consecutive same-key members into one dict (keys = member suffixes).
- Compose with existing TAR handling and codecs where possible; support local shard paths and simple shard patterns as documented.
- Add descriptors, fixtures, tests, and docs (read-first; write optional if low-cost).

## Impact

- Affected specs: `webdataset-format` (new)
- Affected code: new datatype or TAR profile, registry/detection, docs/tests
- Dependencies: prefer stdlib `tarfile` reuse; avoid requiring the `webdataset` package unless necessary
