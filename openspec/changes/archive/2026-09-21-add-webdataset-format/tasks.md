## 1. Design and registry

- [x] 1.1 Finalize sample grouping rules and decoder options.
- [x] 1.2 Add `webdataset`/`wds` descriptor and detection behavior.
- [x] 1.3 Document relationship to the existing TAR iterable.

## 2. Implementation

- [x] 2.1 Implement WebDataset sample iterable over TAR shards.
- [x] 2.2 Support codec-composed shards (e.g. `.tar.gz`).
- [x] 2.3 Handle partial trailing groups with documented behavior.
- [x] 2.4 Optional write path if low-cost; otherwise mark read-only.

## 3. Tests and docs

- [x] 3.1 Add shard fixtures with multi-suffix samples.
- [x] 3.2 Add grouping, codec, malformed, and streaming tests.
- [x] 3.3 Document format, decoding options, and examples.
- [x] 3.4 Run `openspec validate add-webdataset-format --strict`.
