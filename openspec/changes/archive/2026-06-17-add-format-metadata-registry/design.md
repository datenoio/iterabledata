## Context
`iterable/helpers/detect.py` (1,362 lines) holds four parallel, hand-maintained views of the
same format knowledge:

- `DATATYPE_REGISTRY: dict[str, tuple[str, str]]` — ext/id → (module, class), ~160 keys incl. aliases.
- `READ_ONLY_FORMATS: set[str]` — ids/aliases that do not support write.
- `TEXT_DATA_TYPES: list[str]` — ids/aliases that are text (vs binary).
- `FLAT_TYPES: list[str]` — ids/aliases that are flat/tabular.

Plus `detect_file_type_from_content()` is a long if/elif chain matching magic bytes. The only
in-repo consumers of the three lists are `detect.py` itself and `helpers/capabilities.py`
(`from .detect import READ_ONLY_FORMATS`). External code and plugins may import these names, so
they MUST keep existing as module-level objects with identical contents.

## Goals / Non-Goals
- Goals:
  - One declarative table from which all four structures + content detection are derived.
  - Zero behavior change: derived structures are byte-for-byte equal to today's literals.
  - Backward-compatible: `DATATYPE_REGISTRY`, `READ_ONLY_FORMATS`, `TEXT_DATA_TYPES`,
    `FLAT_TYPES` remain importable from `detect.py` with the same types and contents.
  - Adding a new format becomes a single descriptor entry.
- Non-Goals:
  - Changing detection precedence, confidence scores, or any format id/alias.
  - Refactoring `datatypes/__init__.py` conditional imports (tracked as a follow-up).
  - Splitting `detect.py` into multiple modules (that is plan item 3.4).
  - Touching the plugin registry merge logic (`_get_format_registry`).

## Decisions
- Decision: A frozen dataclass descriptor in a new `iterable/helpers/format_registry.py`:
  ```python
  @dataclass(frozen=True)
  class FormatDescriptor:
      id: str                          # canonical id, e.g. "csv"
      module: str                      # "iterable.datatypes.csv"
      cls: str                         # "CSVIterable"
      aliases: tuple[str, ...] = ()    # extra ext/ids resolving to the same class
      text: bool = False               # text (vs binary) content
      flat: bool = False               # flat/tabular shape
      writable: bool = True            # supports write()
      extra: str | None = None         # optional-dependency extra (pyproject)
      magic: tuple[bytes, ...] = ()    # leading-byte signatures for content detection
  ```
  - Aliases map to the *same* (module, class). Distinct classes (e.g. `psv`→PSVIterable,
    `ssv`→SSVIterable) are separate descriptors, never aliases.
- Decision: Derivation helpers build the legacy structures:
  - `DATATYPE_REGISTRY` = `{id: (module, cls)} ∪ {alias: (module, cls) for each alias}`.
  - `READ_ONLY_FORMATS` = all ids+aliases where `not writable`.
  - `TEXT_DATA_TYPES` / `FLAT_TYPES` = ids+aliases where `text` / `flat` (order preserved by
    descriptor order then alias order to match current lists where it matters).
- Decision: New module is the source; `detect.py` imports the descriptor list and assigns the
  derived structures to the existing module-level names (keeping `CODEC_REGISTRY` as-is for now).
- Decision: Content detection iterates descriptors with `magic` set, longest-prefix / declared
  precedence first, returning `(id, confidence, "magic_number")` exactly as today. Cases that are
  not pure leading-byte matches (e.g. structural sniffing, docx/zip disambiguation) stay as
  bespoke code paths; only the straightforward magic-prefix branches move to data.
- Alternatives considered:
  - Class attributes on each Iterable (e.g. `IS_TEXT`, `SUPPORTS_WRITE`): rejected for now —
    would force importing every (optional-dependency) module just to build the tables, defeating
    lazy loading. Descriptors keep metadata import-free.
  - A plugin-style entry-point table: unnecessary; the plugin registry already merges external
    formats at runtime via `_get_format_registry`.

## Risks / Trade-offs
- Risk: subtle ordering/content drift between derived and literal lists → Mitigation: a
  golden-snapshot test that pins the literal sets/lists captured pre-change and asserts equality
  with the derived values; CI fails on any divergence.
- Risk: external importers rely on list *order* of `TEXT_DATA_TYPES`/`FLAT_TYPES` → Mitigation:
  preserve order deterministically from descriptor + alias order, validated by the snapshot test.
- Trade-off: one extra module + a build step at import; negligible (built once at import time).

## Migration Plan
1. Add `format_registry.py` with the descriptor dataclass + the full descriptor table seeded to
   reproduce the current four lists exactly.
2. Add a golden-snapshot test capturing the current literals BEFORE wiring derivation in.
3. Replace the literal definitions in `detect.py` with derivations from the descriptor table,
   keeping the same names/types. Wire content detection's magic-prefix branches to descriptors.
4. (Optional, same change) Point `capabilities.py` at the descriptor lookup instead of importing
   `READ_ONLY_FORMATS`, keeping behavior identical.
5. Run conformance suite + full test suite; confirm no detection/capability changes.

Rollback: revert to the literal definitions; no persisted state or public API changed.

## Open Questions
- Should `CODEC_REGISTRY` gain descriptors too? Deferred — codecs have fewer metadata dimensions;
  out of scope for this change but the model extends naturally later.
