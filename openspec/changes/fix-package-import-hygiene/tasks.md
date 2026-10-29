## 1. Lazy database drivers

- [ ] 1.1 Replace eager registration in `iterable/db/__init__.py` with a `engine name -> "module:Class"` table resolved on first `get_driver()`.
- [ ] 1.2 Remove driver imports from `iterable/helpers/detect.py`; keep `PostgresDriver`/`ClickHouseDriver` reachable through module `__getattr__`.
- [ ] 1.3 Audit the remaining import chain (`ingest`, `validate`, `ops`, `helpers.capabilities`) with `python -X importtime -c "import iterable"` and defer any other optional backend.

## 2. `iterable.ai` binding

- [ ] 2.1 Drop `from .ai import doc as ai` from `iterable/__init__.py`; expose `iterable.ai` lazily as the package.
- [ ] 2.2 Re-export the public `iterable.ai.doc` names from `iterable/ai/__init__.py` via `__getattr__`.
- [ ] 2.3 Test: `mock.patch("iterable.ai.providers.get_provider")` patches the object `iterable.ai.doc` uses; `iterable.ai.generate` is callable.

## 3. Package data

- [ ] 3.1 Add `ai/prompts/*.txt` to `[tool.setuptools.package-data]` and `*.txt` to `MANIFEST.in`.
- [ ] 3.2 Extend the wheel smoke test (`harden-release-artifacts` tooling) to load every prompt through `importlib.resources` from the installed wheel.

## 4. Import-time gate

- [ ] 4.1 Add `tests/test_import_hygiene.py`: a subprocess imports `iterable` and asserts none of `elasticsearch`, `pymongo`, `pyarrow`, `numpy`, `pandas`, `duckdb`, `httpx`, `rich` is in `sys.modules`.
- [ ] 4.2 Add an import-time workload to the performance regression gate and record its baseline.
- [ ] 4.3 Run `ruff check iterable tests`, the full suite and the performance gate.
