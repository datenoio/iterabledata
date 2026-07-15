## 1. Implementation

- [x] 1.1 Create `iterable/datatypes/tar.py` with a `TARIterable(BaseFileIterable)` that iterates archive members
- [x] 1.2 For each data member, detect its format and delegate to that format's streaming reader
- [x] 1.3 Tag yielded records with the source member name (configurable key)
- [x] 1.4 Support compressed tarballs (`.tar.gz`/`.tgz`/`.tar.bz2`/`.tar.xz`) and `.tar.zst` via the zstd codec
- [x] 1.5 Add member-selection `iterableargs` (single member or glob), default all members

## 2. Detection and safety

- [x] 2.1 Register `tar` descriptor and extensions in `format_registry.py`
- [x] 2.2 Detect TAR by magic/`tarfile.is_tarfile`
- [x] 2.3 Reject/skip members with absolute paths or `..` traversal; never extract to disk

## 3. Tests and docs

- [x] 3.1 Fixture tarballs containing CSV + JSONL members (plain and `.tar.gz`)
- [x] 3.2 Tests: iterate all members, select one member, member-name tagging, traversal guard
- [x] 3.3 Write `docs/docs/formats/tar.md`
- [x] 3.4 Run suite and lint
