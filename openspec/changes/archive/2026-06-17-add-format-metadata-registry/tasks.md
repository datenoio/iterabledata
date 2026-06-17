## 1. Descriptor model
- [x] 1.1 Create `iterable/helpers/format_registry.py` with a frozen `FormatDescriptor` dataclass
- [x] 1.2 Seed the full descriptor table to reproduce the current `DATATYPE_REGISTRY`, `READ_ONLY_FORMATS`, `TEXT_DATA_TYPES`, and `FLAT_TYPES` exactly
- [x] 1.3 Add derivation helpers and a lookup API (`get_descriptor`, `iter_descriptors`, builders for the four legacy structures)

## 2. Golden snapshot (regression guard, added before wiring)
- [x] 2.1 Capture today's literal `DATATYPE_REGISTRY`/`READ_ONLY_FORMATS`/`TEXT_DATA_TYPES`/`FLAT_TYPES` as fixtures
- [x] 2.2 Add `tests/test_format_registry.py` asserting the derived structures equal the snapshots (sets and, where relevant, order)

## 3. Wire derivation into detect.py
- [x] 3.1 Replace the literal `DATATYPE_REGISTRY`, `READ_ONLY_FORMATS`, `TEXT_DATA_TYPES`, `FLAT_TYPES` with values derived from the descriptor table (same names, types, contents)
- [x] 3.2 Drive the magic-prefix branches of `detect_file_type_from_content()` from descriptor `magic` data, preserving precedence/confidence/method
- [x] 3.3 (Optional) Point `capabilities.py` at the descriptor lookup instead of importing `READ_ONLY_FORMATS`

## 4. Verification
- [x] 4.1 `pytest tests/test_format_registry.py tests/test_detect.py tests/test_capabilities.py tests/test_format_conformance.py -v`
- [x] 4.2 `ruff check iterable tests && ruff format --check iterable tests`
- [x] 4.3 Full suite `pytest -m "not stress"` shows no detection/capability regressions (1959 passed, 339 skipped)
- [x] 4.4 `openspec validate add-format-metadata-registry --strict`
