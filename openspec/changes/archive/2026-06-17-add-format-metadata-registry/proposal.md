# Change: Single source of truth for format metadata

## Why
Format knowledge is duplicated across four hand-maintained structures in
`iterable/helpers/detect.py` — `DATATYPE_REGISTRY` (~160 ext→class entries), `READ_ONLY_FORMATS`
(a set), `TEXT_DATA_TYPES` (a list), and `FLAT_TYPES` (a list) — plus a long if/elif magic-byte
chain in `detect_file_type_from_content()` and the conditional-import `datatypes/__init__.py`.
The lists drift out of sync: `READ_ONLY_FORMATS` is stale (it omits writable/read-only nuances
and must be edited in lockstep with the registry), and every new format requires touching 3–5
places. This is plan item 3.1 and Top-10 action #5.

## What Changes
- Introduce a declarative per-format descriptor (`FormatDescriptor`) capturing: canonical `id`,
  `aliases`, `module`/`cls`, `text` vs binary, `flat`, `writable` (read/write capability),
  optional dependency `extra`, and content-detection `magic` byte prefixes.
- Add an ordered list of descriptors as the single source of truth in a new
  `iterable/helpers/format_registry.py` module.
- **Derive** the existing module-level names from the descriptors so all current importers keep
  working unchanged: `DATATYPE_REGISTRY`, `READ_ONLY_FORMATS`, `TEXT_DATA_TYPES`, `FLAT_TYPES`
  become computed from the descriptor table (re-exported from `detect.py`).
- Drive `detect_file_type_from_content()` magic-byte matching from descriptor `magic` data
  instead of a hand-written if/elif chain (preserving current precedence/confidence behavior).
- Expose a small lookup API (`get_descriptor(id_or_alias)`, `iter_descriptors()`) for
  `capabilities.py`, docs generation (item 7), and the conformance suite (4.2).
- Fixing `READ_ONLY_FORMATS` drift falls out automatically: `writable` lives on each descriptor.

This change is **internal/additive**: the public `open_iterable()` API, detection results, and
all currently-exported names are preserved. No format ids, aliases, or capabilities change
behavior; the descriptor table is seeded to exactly reproduce today's four lists.

## Impact
- Affected specs: `format-registry` (new capability)
- Affected code: new `iterable/helpers/format_registry.py`; `iterable/helpers/detect.py`
  (registry/list definitions + content detection now derive from descriptors);
  `iterable/helpers/capabilities.py` (optional: consume the descriptor lookup);
  `iterable/datatypes/__init__.py` (optional follow-up: generate conditional re-exports).
- Risk: low. Backed by a golden-snapshot test asserting the derived structures equal today's
  literal lists, plus the existing format conformance suite.
