---
name: iterabledata-development
description: Core development workflows, patterns, and conventions for IterableData. Use when implementing features, fixing bugs, or working with the codebase structure.
---

# IterableData Development

## Quick Setup

```bash
pip install -e ".[dev]"
pytest --verbose
ruff check iterable tests
ruff format iterable tests
```

## Code Style

- Python 3.10+ with type hints where appropriate
- Max line length: 120 characters
- Use `ruff` for linting and formatting
- Double quotes for strings consistently
- Always use context managers for file operations
- Import order: standard library, third-party, local imports

## Project Structure

- `iterable/helpers/` - Utility functions (detect, schema, utils)
- `iterable/datatypes/` - Format-specific implementations
- `iterable/codecs/` - Compression codec implementations
- `iterable/engines/` - Processing engines (DuckDB, internal)
- `iterable/convert/` - Format conversion utilities
- `iterable/pipeline/` - Data pipeline processing
- `tests/` - Test suite (one test file per format/feature)

## Import Patterns

- Main entry: `from iterable import open_iterable`
- Convert: `from iterable.convert import convert`
- Format-specific (advanced): `from iterable.datatypes.csv import CSVIterable`
- Codecs (advanced): `from iterable.codecs.gzipcodec import GZIPCodec`
- Always use `open_iterable()` for user-facing examples; do not teach `iterable.helpers.detect` as the default import

## File Handling

- Always use context managers: `with open_iterable('file.csv') as source:`
- Never call `.close()` when using `with` statements
- Reset iterators with `.reset()` method when needed
- Handle compression automatically via filename detection

## Error Handling

- Format detection failures: provide helpful error messages
- Missing optional dependencies: raise clear ImportError with installation instructions
- Invalid file formats: raise appropriate exceptions (ValueError, TypeError)
- Always handle file I/O errors gracefully

## Code Conventions

- Use `open_iterable()` for automatic format detection
- Prefer bulk operations (`read_bulk`, `write_bulk`) for performance
- Use DuckDB engine when appropriate (CSV, JSONL files)
- Handle encoding automatically via `chardet` or user specification

## Pre-Commit Checks

Before committing:
1. Run tests: `pytest --verbose`
2. Run linter: `ruff check iterable tests`
3. Format code: `ruff format iterable tests`
4. Type check: `mypy iterable` (warnings allowed)

## Quality Tools

- Security: `bandit -r iterable -ll`
- Dead code: `vulture iterable --min-confidence 80`
- Complexity: `radon cc iterable --min B`
- Coverage: `pytest --cov=iterable --cov-report=html`

## Known Constraints

- DuckDB engine supports: CSV, JSONL, JSON formats and GZIP, ZStandard codecs
- Large files: use streaming (iterator interface) to avoid memory issues
- XML parsing: requires `iterableargs={'tagname': 'item'}`
- Some formats require optional dependencies (see `pyproject.toml`)
