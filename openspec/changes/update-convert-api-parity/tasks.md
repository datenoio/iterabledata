## 1. Convert parameters

- [ ] 1.1 Add `codecargs`/`tocodecargs` to `convert()` and pass them to the reader and writer `open_iterable()` calls.
- [ ] 1.2 Add `codecargs`, `tocodecargs`, `use_native_batch`, `selection`, `strict_native` to `bulk_convert()` and forward them, including in parallel mode.
- [ ] 1.3 Tests: gzip level 1 vs 9 output sizes differ through `convert()`; `bulk_convert(selection=...)` applies the selection.

## 2. Public helper names

- [ ] 2.1 Add `list_codecs()`, `assemble_markdown()`, `ordered_block_keys()`, `run_metacrafter_scan()`, `parse_metacrafter_matches()` with docstrings; keep private aliases.
- [ ] 2.2 Document the registries as read-only and reference the public alternatives in `docs/docs/api/`.

## 3. Downstream contract

- [ ] 3.1 Add `tests/test_downstream_contract.py` importing and smoke-calling every iterabledata name undatum uses (list taken from `git grep "from iterable" undatum/`).
- [ ] 3.2 Note in `AGENTS.md` that this module guards downstream compatibility.
- [ ] 3.3 Run `ruff check iterable tests` and the full suite.
