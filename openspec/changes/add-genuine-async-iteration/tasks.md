# Tasks

## 1. Genuine async wrapper

- [x] 1.1 Rework `aopen_iterable()` so detection and iteration offload to a thread pool (`asyncio.to_thread`); fix the docstring to describe actual behavior.
- [x] 1.2 Ensure `AsyncBaseFileIterable` iteration yields control between rows/bulks (no long blocking stretches on the event loop).

## 2. Public API and docs

- [x] 2.1 Export `aopen_iterable` from `iterable/__init__.py` with `__all__` entry.
- [x] 2.2 Add an async section to README and a docs page with examples and the blocking-operations caveat.

## 3. Tests and verification

- [x] 3.1 Async equivalence tests for csv/jsonl (and parquet when pyarrow is installed): async results == sync results.
- [x] 3.2 Concurrency test: two async reads interleave (proves event loop is not blocked).
- [x] 3.3 Full serial suite green; ruff/mypy blocking gates stay green; CHANGELOG updated.
