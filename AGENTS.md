

# OpenSpec Instructions

These instructions are for AI assistants working in this project.

Always open `@/openspec/AGENTS.md` when the request:

- Mentions planning or proposals (words like proposal, spec, change, plan)
- Introduces new capabilities, breaking changes, architecture shifts, or big performance/security work
- Sounds ambiguous and you need the authoritative spec before coding

Use `@/openspec/AGENTS.md` to learn:

- How to create and apply change proposals
- Spec format and conventions
- Project structure and guidelines

Keep this managed block so 'openspec update' can refresh the instructions.



# AGENTS.md

Instructions for AI coding agents working on the IterableData project.

## Setup commands

- Install dependencies: `pip install -e ".[dev]"`
- Run tests: `pytest --verbose` (includes coverage automatically)
- Run tests with parallel execution: `pytest -n auto`
- Run linter: `ruff check iterable tests`
- Format code: `ruff format iterable tests`
- Type check: `mypy iterable`
- Run all checks: `ruff check iterable tests && ruff format --check iterable tests && pytest`

## Security and Quality Tools

- Security scan: `bandit -r iterable -ll`
- Dependency vulnerabilities: `pip-audit --requirement <(pip freeze)`
- Dead code detection: `vulture iterable --min-confidence 80`
- Code complexity: `radon cc iterable --min B`
- Documentation style: `pydocstyle iterable`
- Coverage report: `pytest --cov=iterable --cov-report=html` (opens `htmlcov/index.html`)

## Code style

- Python 3.10+ with type hints where appropriate
- Maximum line length: 120 characters (configured in `pyproject.toml`)
- Use `ruff` for linting and formatting (E, F, I, B, UP rules enabled)
- Use double quotes for strings consistently
- Follow PEP 8 with project-specific exceptions
- Always use context managers (`with` statements) for file operations
- Import organization: standard library, third-party, local imports

## Project structure

- `iterable/` - Main package directory
  - `helpers/` - Utility functions (detect, schema, utils)
  - `datatypes/` - Format-specific implementations (CSV, JSON, Parquet, etc.)
  - `codecs/` - Compression codec implementations
  - `engines/` - Processing engines (DuckDB, internal)
  - `convert/` - Format conversion utilities
  - `pipeline/` - Data pipeline processing
- `tests/` - Test suite (one test file per format/feature)
- `examples/` - Usage examples
- `tests/fixtures/` - Committed test data files (`tests/testdata/` is a symlink to this directory)
- `fixtures/` - Test fixtures

## Testing instructions

- All tests are in the `tests/` directory
- Test files follow pattern: `test_*.py`
- Test classes: `Test*`
- Test functions: `test_*`
- Run specific test: `pytest tests/test_csv.py -v`
- Run specific test function: `pytest tests/test_csv.py::TestCSV::test_read -v`
- Tests should pass for Python 3.10, 3.11, and 3.12
- Always run tests before committing: `pytest --verbose`
- Some format tests may be skipped if optional dependencies are missing (this is expected)
- Performance regression gate: `pytest tests/test_performance_regression.py -m performance --no-cov`
  compares representative workloads against committed baselines in `tests/performance_baselines.json`.
  If a change legitimately alters performance, regenerate baselines intentionally with
  `pytest tests/test_performance_regression.py -m performance --no-cov --update-baselines`
  and commit the updated JSON (note the reference environment in `_meta`).
- `tests/testdata` must be a symlink to `tests/fixtures`. Check out the repo with symlinks enabled (`git config core.symlinks true`); if it materialized as a plain file, restore it with `rm tests/testdata && ln -s fixtures tests/testdata`
- Stress/slow/benchmark/integration tests are excluded from the default run; opt in with e.g. `pytest -m stress`

## Import patterns

- Main entry point: `from iterable import open_iterable`
- Convert: `from iterable.convert import convert`
- Format-specific (advanced): `from iterable.datatypes.csv import CSVIterable`
- Codecs (advanced): `from iterable.codecs.gzipcodec import GZIPCodec`
- Always use `open_iterable()` for user-facing code; direct class usage is for advanced cases
- PyPI package is `iterabledata`; import package is `iterable`. Do not document the internal `iterable.helpers.detect` path as the default import.

## File handling

- Always use context managers: `with open_iterable('file.csv') as source:`
- Never call `.close()` when using `with` statements
- Reset iterators with `.reset()` method when needed
- Handle compression automatically via filename detection or explicit codec

## Error handling

- Format detection failures should provide helpful error messages
- Missing optional dependencies should raise clear ImportError with installation instructions
- Invalid file formats should raise appropriate exceptions (ValueError, TypeError)
- Always handle file I/O errors gracefully

## Adding new formats

1. Create new file in `iterable/datatypes/` (e.g., `newformat.py`)
2. Implement class inheriting from `BaseIterable` in `iterable/base.py`
3. Implement required methods: `read()`, `write()`, `read_bulk()`, `write_bulk()`, etc.
4. Add format detection logic in `iterable/helpers/detect.py`
5. Create comprehensive tests in `tests/test_newformat.py`
6. Update `detect_file_type()` to recognize the format
7. Add optional dependency to `pyproject.toml` if needed
8. Update documentation

## Adding new codecs

1. Create new file in `iterable/codecs/` (e.g., `newcodec.py`)
2. Implement class with `read()`, `write()`, `close()` methods
3. Update `iterable/helpers/detect.py` to detect the codec
4. Add compression format detection logic
5. Create tests in `tests/test_newcodec.py` or relevant test file
6. Add optional dependency to `pyproject.toml`

## Code conventions

- Use `open_iterable()` for automatic format detection
- Use format-specific classes only when needed
- Always close files or use context managers
- Prefer bulk operations (`read_bulk`, `write_bulk`) for performance
- Use DuckDB engine when appropriate (CSV, JSONL files)
- Handle encoding automatically via `chardet` or user specification

## Linting and formatting

- Run `ruff check iterable tests` before committing
- Run `ruff format iterable tests` to auto-format
- Fix all linting errors; warnings are treated as errors
- Type hints are encouraged but not strictly required (mypy runs but failures are allowed)
- Pre-commit hooks will automatically run security scans, code quality checks, and formatting on commit
- Install pre-commit hooks: `pre-commit install`

## Commit guidelines

- Write clear, descriptive commit messages
- Test your changes: `pytest --verbose`
- Run linter: `ruff check iterable tests`
- Ensure code follows project style
- Update tests if adding new functionality
- Update documentation if changing public APIs

## PR guidelines

- All tests must pass
- Linter must pass: `ruff check iterable tests`
- Code should be formatted: `ruff format --check iterable tests`
- Include tests for new features
- Update relevant documentation
- Describe changes clearly in PR description

## Development tips

- Use `open_iterable()` for most use cases (`from iterable import open_iterable`)
- Check existing format implementations for patterns
- Look at `tests/test_*.py` files for usage examples
- Test with compressed files (`.gz`, `.bz2`, `.xz`, `.zst`, etc.)
- Test with various encodings for text formats
- Handle edge cases: empty files, malformed data, missing dependencies

## Scope constraints

- **Do not add a CLI to this package.** The command-line interface is already provided
  through the project's distribution metadata (a separate console entry point), not from this
  repository. Do not create `iterable/cli.py`, do not add a `[project.scripts]` entry point in
  `pyproject.toml`, and do not propose a CLI as an improvement. This package is a library only;
  expose functionality through the Python API (`open_iterable`, the `ops`/`convert`/`validate`
  layers), not new console commands.

## Known issues

- Some formats require optional dependencies (see `pyproject.toml` for optional-dependencies)
- DuckDB engine only supports certain formats (CSV, JSONL, JSON) and codecs (GZIP, ZStandard)
- Large files should use streaming (iterator interface) to avoid memory issues
- XML parsing requires specifying tag names via `iterableargs={'tagname': 'item'}`

## Cursor Skills

This project includes Cursor Skills (`.cursor/skills/`) that provide specialized guidance for common tasks:

- **iterabledata-development** - Core development workflows and conventions
- **openspec-workflows** - OpenSpec proposal and implementation workflows
- **format-implementation** - Guide for implementing new data formats
- **testing-patterns** - Testing conventions and best practices
- **database-engine-implementation** - Guide for implementing database engines
- **ai-integration** - AI/LLM features, catalog, tools, and agent patterns

Skills are automatically applied by Cursor AI when relevant. See `.cursor/skills/README.md` for details.

## AI and LLM development

- Install AI extras: `pip install -e ".[dev,ai]"`
- Native providers: `openai`, `anthropic`, `gemini`, `azure` via `iterable.ai.doc.generate(provider=...)`
- Agent tools: `from iterable.tools import detect_format, read_sample, ...` (see `docs/docs/api/tools.md`)
- MCP server (optional): `pip install iterabledata[mcp]` then `iterable-mcp` (stdio)
- Mock LLM calls in tests: `patch("iterable.ai.doc.get_provider")` or `patch("iterable.ai.doc.generate")`
- Mark AI tests: `@pytest.mark.ai`; live API tests: `@pytest.mark.integration` (see `tests/test_ai_integration.py`)
- Default CI excludes integration tests; workflow `.github/workflows/ai-integration.yml` runs them on schedule when secrets are set
- Never commit API keys; use heuristic `redact_for_llm()` before cloud provider calls

## Resources

- Main documentation: See `README.md` and `docs/` directory
- API reference: `docs/docs/api/`
- Format documentation: `docs/docs/formats/`
- Examples: `examples/` and `examples/cookbook/`
- Portable usage skill: `skills/iterabledata/SKILL.md`
- AI Integration guides: `docs/integrations/` directory

