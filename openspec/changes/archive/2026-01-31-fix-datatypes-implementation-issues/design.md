# Design: Fix Datatype Implementation Consistency Issues

## Context
IterableData exposes many datatype implementations in `iterable/datatypes/` that inherit from `BaseFileIterable` and accept filename, stream, or codec. A review found: (1) many modules use the `Row` type in `write()` / `write_bulk()` signatures without importing it, causing mypy/type-checker failures; (2) some formats (e.g. DBF, shapefile, sqlite, mbox, xlsb) only support filename but accept stream/codec in the constructor, leading to opaque failures in `reset()`; (3) incorrect docstrings (e.g. bsonf `read()` labeled "Write"); (4) inconsistent `read_bulk()` exhaustion (some return `[]`, one raises `StopIteration`). This design standardizes behavior and type hygiene without changing the public API.

**Stakeholders**: Library users, maintainers, type-checker and CI users.

**Constraints**: No breaking API changes; preserve backward compatibility for callers that pass filename only.

## Goals / Non-Goals

### Goals
- Resolve all `Row` undefined-name issues in datatype modules so mypy (and similar) pass.
- Ensure filename-only formats fail fast with a clear error when given stream or codec.
- Fix known docstring errors and document the `read_bulk()` exhaustion contract.
- Align DBF (and any other outlier) with the contract: `read_bulk()` returns `[]` when exhausted.

### Non-Goals
- Adding stream/codec support to filename-only formats (out of scope).
- Changing method signatures or return types (only documentation and implementation details).
- Broad refactor of base class or format detection.

## Decisions

### Decision 1: Row Import Strategy
**What**: Add `from ..types import Row` (or `from iterable.types import Row` where appropriate) to every datatype module that uses `Row` or `list[Row]` in method signatures but does not already import it.

**Why**: Type hints are evaluated by mypy/pyright; `Row` must be in scope. With `from __future__ import annotations`, annotations are strings at runtime, so runtime does not fail, but type checkers report "Row" undefined. Adding the import is the minimal fix and matches existing modules (e.g. csv, graphml, dot) that already import `Row`.

**Alternatives considered**:
- Re-export `Row` from `iterable.base`: would couple datatypes to base and duplicate the canonical definition in `types`.
- Use `dict[str, Any]` instead of `Row` in datatypes: loses the shared alias and diverges from `iterable/types.py`.

**Trade-offs**: One extra line per affected file; no API or runtime behavior change.

### Decision 2: Where to Validate Filename-Only Sources
**What**: Validate in `reset()` at the point where the format needs a path: check that `self.filename` is not None (and that we are in file-based source mode, i.e. not stream/codec). If the format was constructed with stream or codec, `self.stype` will be stream or codec and `self.filename` may be None; if constructed with filename, `self.filename` is set by the base. So the check is: when this format requires a path, require `self.stype == ITERABLE_TYPE_FILE` and `self.filename` is not None; otherwise raise a clear error.

**Why**: Base class already enforces "exactly one of filename, stream, codec". So if the user passed stream or codec, `self.filename` is None and `self.stype` is not FILE. Validating at the start of `reset()` (1) fails on first use rather than deep inside the library, (2) keeps `__init__` consistent across all datatypes (no special-case checks in constructor), and (3) reuses existing `ReadError` or `ValueError` with a message like "DBF requires a file path; stream and codec are not supported."

**Alternatives considered**:
- Validate in `__init__`: would require each filename-only format to override `__init__` and inspect source type before calling `super().__init__`; more invasive and duplicates logic.
- Let the underlying library fail: current behavior; poor UX and hard to debug.

**Trade-offs**: One conditional at the top of `reset()` per filename-only format; clearer errors for invalid usage.

### Decision 3: Exception Type for Invalid Source
**What**: Use `ReadError` (from `iterable.exceptions`) when the format requires a path but is given stream/codec, with a message that states the format name and that a file path is required. If `ReadError` is not available or the context is generic, use `ValueError` with the same message.

**Why**: `ReadError` is already used elsewhere (e.g. CDF, Delta) for "cannot read in this configuration." Using it here keeps error handling consistent and allows callers to catch `ReadError` for all read-setup failures.

**Alternatives considered**:
- `ValueError` only: works but less specific than a domain exception.
- New exception type: unnecessary for this scope.

**Trade-offs**: None; aligns with existing code.

### Decision 4: read_bulk() Exhaustion Contract
**What**: Define the contract: when no more records are available, `read_bulk(num)` SHALL return `[]` and SHALL NOT raise `StopIteration`. Document this in `BaseIterable.read_bulk()` docstring. Change DBF (and any other implementation that currently raises `StopIteration` from `read_bulk`) to return `[]` instead.

**Why**: Most datatypes already return `[]`; callers can use `while chunk := it.read_bulk(n): ...`. Raising `StopIteration` from `read_bulk()` is inconsistent and forces callers to use try/except. Standardizing on return `[]` is backward compatible for the common pattern and only changes behavior for code that relied on the exception (rare).

**Alternatives considered**:
- Allow both (document "either [] or StopIteration"): increases complexity for callers and violates principle of least surprise.
- Standardize on raising StopIteration: would break the majority of formats and existing callers.

**Trade-offs**: DBF (and any similar) behavior change from "raise" to "return []" at exhaustion; considered a bug fix, not a breaking change.

### Decision 5: List of Filename-Only Formats to Harden
**What**: Explicitly validate and raise clear errors in at least: DBF, shapefile, sqlite, mbox, xlsb. Any other format that in `reset()` or equivalent uses only `self.filename` (or equivalent path) and never uses `self.fobj` from stream/codec SHALL be audited and, if it cannot support stream/codec, SHALL add the same validation.

**Why**: These five were identified in the review as using `self.filename` in `reset()` without handling stream/codec. A quick audit of other datatypes for the same pattern ensures no format is left with opaque failures.

**Alternatives considered**:
- Only fix DBF: leaves other formats with the same class of bug.
- Add a base-class helper: possible future refactor; for this change, per-format check is sufficient and clear.

**Trade-offs**: Small amount of duplicated validation code per format; acceptable for clarity and locality.

## Risks / Trade-offs

- **Scope creep**: Many files need the Row import. Mitigation: do the import fix in a single pass (e.g. script or batch edit), then run mypy and fix any remaining issues.
- **Missing filename-only formats**: Some format might be missed in the audit. Mitigation: document the rule in the format-implementation SKILL/AGENTS.md so new formats are implemented correctly; add a test that DBF (and optionally one other) raises when given a stream.

## Migration Plan

1. No user migration required: no public API changes. Stricter validation may cause code that incorrectly passed stream/codec to filename-only formats to fail with a clear error instead of a later opaque failure.
2. If any external code relies on `read_bulk()` raising `StopIteration` for DBF: update to check for `[]` instead; this is the recommended pattern.

## Open Questions

- None; implementation can proceed per `tasks.md`.
