# Change: Genuine Async open_iterable (Async Phase 2)

## Why

`aopen_iterable()` exists in `iterable/helpers/async_detect.py` but is a thin
sync wrapper: it calls the blocking `open_iterable()` inline on the event loop,
is not exported from `iterable/__init__.py`, and is absent from the README.
Async users get no concurrency benefit today (plan 2026-09 §6.2).

## What Changes

- Make `aopen_iterable()` genuinely non-blocking: detection and iteration run
  in a thread-pool executor (`asyncio.to_thread` / `loop.run_in_executor`),
  with the docstring matching actual behavior.
- Export `aopen_iterable` from `iterable/__init__.py`.
- Document the async API in README and docs, with an explicit note about which
  operations remain blocking (codec open, network-free local file I/O).
- Add async tests: concurrent reads of two files interleave, and async
  iteration matches sync results for csv/jsonl/parquet.

## Impact

- Affected specs: new `async-iteration` capability.
- Affected code: `iterable/helpers/async_detect.py`, `iterable/async_base.py`,
  `iterable/__init__.py`, tests, README, docs.
- No new dependencies (stdlib asyncio only).

## Non-goals

- Async writes to database drivers; native async I/O for local files
  (aiofiles) — thread-pool offload is the supported model.
