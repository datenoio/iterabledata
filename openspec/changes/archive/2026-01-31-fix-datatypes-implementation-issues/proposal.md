# Change: Fix Datatype Implementation Consistency Issues

## Status: Approved
Approved for implementation. Design documented in `design.md`. Proceed with tasks in `tasks.md` in order.

## Why
A review of `iterable/datatypes/` found several consistency and correctness issues: missing type imports (causing mypy/type-checker failures), formats that accept stream/codec in the constructor but only support filename (leading to confusing failures in `reset()`), incorrect docstrings, inconsistent `read_bulk()` exhaustion behavior, and filename-only formats that do not validate or document their source requirements. Fixing these improves type safety, debuggability, and predictable behavior across all format implementations.

## What Changes
- **Row type import**: Add `from ..types import Row` to every datatype module that uses `Row` in `write()` or `write_bulk()` signatures but does not currently import it (many modules use the type hint without the import, breaking type checkers).
- **Filename-only validation**: For formats that require a file path (e.g. DBF, shapefile, sqlite, mbox, xlsb) and cannot use stream or codec, validate in `__init__` or at the start of `reset()` and raise a clear `ValueError` or `ReadError` with a message such as "Format X requires a file path; stream/codec is not supported" instead of failing later with library-specific errors.
- **DBF**: Explicitly validate that a filename is provided when using DBFIterable; raise a clear error if stream or codec is passed.
- **bsonf docstring**: Fix `read()` method docstring in `iterable/datatypes/bsonf.py` from "Write single bson record" to "Read single BSON record".
- **read_bulk exhaustion contract**: Document in the base class (or format implementation guide) that `read_bulk()` SHALL return an empty list `[]` when no more records are available (do not raise `StopIteration`). Align DBF (and any other format that currently raises) to return `[]` for consistency with the majority of formats and easier caller code.
- **Documentation**: Update format implementation guide / AGENTS.md to state that filename-only formats MUST validate source and raise a clear error when stream or codec is used, and that `read_bulk()` MUST return `[]` when exhausted.

## Impact
- **Affected specs**: New spec `datatype-implementation` (consistency and contract requirements for all datatype classes).
- **Affected code**:
  - `iterable/datatypes/*.py` — add Row import where missing (~70 files), fix DBF and bsonf, align read_bulk exhaustion in dbf.py.
  - Filename-only formats: dbf, shapefile, sqlite, mbox, xlsb, and any others that use `self.filename` in `reset()` without supporting stream/codec — add validation and clear errors.
  - `iterable/base.py` — optional: add a sentence in docstring for `read_bulk()` that return value is `[]` when no more data.
  - Documentation: `.cursor/skills/format-implementation/SKILL.md` and/or `AGENTS.md`.
- **User impact**: Type checkers (mypy) will succeed on datatype modules; users get clear errors when passing stream/codec to filename-only formats; consistent bulk-read exhaustion behavior; no breaking API changes (only stricter validation and doc/code fixes).
