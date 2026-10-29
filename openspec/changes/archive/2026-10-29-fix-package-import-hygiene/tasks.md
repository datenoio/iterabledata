## 1. Lazy database drivers

- [x] 1.1 Replace eager registration in `iterable/db/__init__.py` with a `engine name -> "module:Class"` table resolved on first `get_driver()`.
- [x] 1.2 Remove driver imports from `iterable/helpers/detect.py`; keep `PostgresDriver`/`ClickHouseDriver` reachable through module `__getattr__`.
- [x] 1.3 Audit the remaining import chain with `python -X importtime -c "import iterable"`: after the driver and AI changes only stdlib modules and `chardet` (a base dependency) load; 0.42 s / 964 modules -> 0.09 s / 274 modules.

## 2. `iterable.ai` binding

- [x] 2.1 Drop `from .ai import doc as ai` from `iterable/__init__.py`; expose `iterable.ai` lazily as the package.
- [x] 2.2 Keep the public `iterable.ai.doc` names reachable: `iterable/ai/__init__.py` already re-exports `doc`, `generate` and `generate_blocks`; `iterable.ai` stays `None` when the AI extras are missing, as before.
- [x] 2.3 Test: `mock.patch("iterable.ai.providers.get_provider")` patches the object `iterable.ai.doc` uses; `iterable.ai.generate` is callable.

## 3. Package data

- [x] 3.1 Add `ai/prompts/*.txt` to `[tool.setuptools.package-data]` and `*.txt` to `MANIFEST.in`.
- [x] 3.2 `dev/scripts/verify_dist.py` (release workflow) fails when a runtime resource under `iterable/` is missing from a wheel or sdist; the CI `minimal-smoke` job (`pip install .`) loads the prompts through `importlib.resources`.

## 4. Import-time gate

- [x] 4.1 Add `tests/test_import_hygiene.py`: a subprocess imports `iterable` and asserts none of `elasticsearch`, `pymongo`, `pyarrow`, `numpy`, `pandas`, `duckdb`, `httpx`, `rich` is in `sys.modules`.
- [x] 4.2 Add an import-time workload to the performance regression gate and record its baseline.
- [x] 4.3 Run `ruff check iterable tests`, the full suite and the performance gate.
