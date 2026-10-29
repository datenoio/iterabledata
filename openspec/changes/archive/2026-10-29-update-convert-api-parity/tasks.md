## 1. Convert parameters

- [x] 1.1 Add `codecargs`/`tocodecargs` to `convert()` and pass them to the reader and writer `open_iterable()` calls.
- [x] 1.2 Add `codecargs`, `tocodecargs`, `use_native_batch`, `selection`, `strict_native` to `bulk_convert()` and forward them, including in parallel mode.
- [x] 1.3 Tests (`tests/test_convert_codec_args.py`): gzip level 1 vs 9 through `convert()` (size and gzip header XFL); `bulk_convert()` forwards `tocodecargs`, `selection` and `strict_native` in sequential and parallel mode.

## 2. Public helper names

- [x] 2.1 Add `list_codecs()`, `assemble_markdown()`, `ordered_block_keys()`, `run_metacrafter_scan()`, `parse_metacrafter_matches()` with docstrings; keep private aliases. undatum also calls `iterable.ai.blocks._render_general_md`/`_render_schema_md`, so `render_general_md()`/`render_schema_md()` are public too.
- [x] 2.2 Document the registries as read-only and reference the public alternatives in `docs/docs/api/` (`codecs.md`, `ai.md`, `convert.md`).

## 3. Downstream contract

- [x] 3.1 Add `tests/test_downstream_contract.py` importing and smoke-calling every iterabledata name undatum uses (list taken from `git grep "from iterable" undatum/`).
- [x] 3.2 Note in `AGENTS.md` that this module guards downstream compatibility.
- [x] 3.3 Run `ruff check iterable tests` and the full suite.
