# Change: Add TAR as a multi-file container

## Why

The review flagged TAR-as-container as the highest-leverage archive gap: `.tar`, `.tar.gz`, and `.tar.zst` are ubiquitous packaging for datasets, but the library currently treats compression codecs and single-member ZIP/7z wrappers as the only archive handling. Users cannot iterate the data files inside a tarball. TAR is stdlib-only (`tarfile`), so the cost is low.

## What Changes

- Add a `tar` container that iterates the members of a TAR archive, detecting each member's format (via the existing detection logic) and yielding its records, tagged with the member name.
- Support compressed tarballs (`.tar.gz`, `.tgz`, `.tar.bz2`, `.tar.xz`) via stdlib `tarfile` transparent modes, and `.tar.zst` by layering the existing zstd codec.
- Provide member selection: an `iterableargs` option to pick a specific member or a glob, defaulting to iterating all data members in archive order.
- Stream member by member; within a member, delegate to that format's streaming reader. Read-only.
- Guard against path traversal / absolute member names (no extraction to disk; members are read in memory).

## Impact

- Affected specs: `tar-container` (new capability)
- Affected code: `iterable/datatypes/tar.py` (new), `iterable/helpers/format_registry.py`, `iterable/helpers/detect.py`, `docs/docs/formats/tar.md`, `tests/test_tar.py`
- No new dependency for plain/gz/bz2/xz TAR; `.tar.zst` reuses the existing `[compression]` zstd extra.
