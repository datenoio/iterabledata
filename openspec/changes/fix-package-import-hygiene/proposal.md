# Change: Make `import iterable` light, stop shadowing `iterable.ai`, ship AI prompt files

## Why

Three packaging/import defects surfaced in undatum sessions; all still present on 1.0.23:

1. **Heavy import.** `import iterable` takes ~0.42 s here (undatum measured ~1 s on its machine)
   and loads 964 modules, including `elasticsearch`, `pymongo`, `pyarrow`, `numpy`, `httpx` and
   `rich`. The chain is `iterable` -> `iterable.ingest` -> `iterable.helpers.detect` ->
   `iterable.db`, whose `__init__` imports every installed database driver to register it
   (`iterable.db.elasticsearch` alone costs 0.25 s). undatum had to add lazy wrappers around
   `detect_file_type` and module constants to keep CLI start-up under 0.5 s.
2. **`iterable.ai` is shadowed.** `iterable/__init__.py` runs `from .ai import doc as ai`, so after
   import the attribute `iterable.ai` is the `iterable.ai.doc` module, not the package.
   `mock.patch("iterable.ai.providers.get_provider")` and similar string paths resolve against the
   wrong object (undatum had to rewrite its tests).
3. **AI prompt files are not in the wheel.** `iterable/ai/prompts/*.txt` are loaded at runtime by
   `load_prompt()`, but `[tool.setuptools.package-data]` lists only `py.typed` and `MANIFEST.in`
   includes only `*.py`. The installed 1.0.21 wheel has `iterable/ai/prompts/__init__.py` and no
   `.txt` files, so `iterable.ai.filter`, `plan` and `suggest` fail after `pip install`.

## What Changes

- Register database drivers by module path (`"postgres": "iterable.db.postgres:PostgresDriver"`)
  and import a driver on first `get_driver()` call. `is_database_engine()` uses the static table.
- Remove eager driver imports from `iterable/helpers/detect.py`; keep the names importable through
  module `__getattr__` for compatibility.
- Keep `iterable.ai` bound to the package. Re-export the former `iterable.ai.doc` public names
  (`generate`, ...) lazily from `iterable/ai/__init__.py` so `iterable.ai.generate(...)` keeps
  working.
- Add `"ai/prompts/*.txt"` to package data and `recursive-include iterable *.txt` to `MANIFEST.in`;
  add a wheel-content check to the release smoke test that loads every prompt via
  `importlib.resources`.
- Add an import-time gate: `import iterable` loads none of a deny-list of optional heavy modules
  and stays under a committed budget in `tests/performance_baselines.json`.

## Impact

- Affected specs: `performance-regression`, `repository-quality`
- Affected code: `iterable/__init__.py`, `iterable/ai/__init__.py`, `iterable/db/__init__.py`,
  `iterable/helpers/detect.py`, `pyproject.toml`, `MANIFEST.in`
- Affected tests: new `tests/test_import_hygiene.py`; release wheel smoke test
- Downstream: undatum can drop its lazy-import shims and the `iterable.ai` mock workaround
