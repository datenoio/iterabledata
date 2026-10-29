# Change: Close the convert API gaps and publish the helpers undatum imports privately

## Why

undatum is the main downstream consumer. Its code shows where the public API is not enough:

- **`codecargs` cannot reach `convert()`.** `open_iterable()` accepts `codecargs` (compression level,
  codec profile), but `convert()` and `bulk_convert()` do not. undatum monkeypatches
  `iterable.convert.core.open_iterable` inside a context manager to inject them.
- **`bulk_convert()` lags `convert()`.** It does not accept `use_native_batch`, `selection` or
  `strict_native`; undatum filters its kwargs by `inspect.signature` to stay compatible.
- **Private names are load-bearing.** undatum imports `iterable.helpers.open_iterable._get_codec_registry`,
  `iterable.ai.doc._assemble_markdown`, `iterable.ai.doc._ordered_block_keys`,
  `iterable.ai.semantic._run_metacrafter_scan` and `_parse_metacrafter_matches`, plus the mutable
  `CODEC_REGISTRY`, `DATATYPE_REGISTRY` and `TEXT_DATA_TYPES` globals. Any refactor here breaks it.

## What Changes

- `convert()` gains `codecargs` (reader) and `tocodecargs` (writer); `bulk_convert()` gains the same
  plus `use_native_batch`, `selection` and `strict_native`, forwarded to `convert()`.
- Add public, documented functions: `iterable.helpers.detect.list_codecs()` (ids and extensions),
  `iterable.ai.doc.assemble_markdown()` / `ordered_block_keys()`,
  `iterable.ai.semantic.run_metacrafter_scan()` / `parse_metacrafter_matches()`. Keep the private
  names as aliases for one minor release.
- Document `CODEC_REGISTRY`, `DATATYPE_REGISTRY` and `TEXT_DATA_TYPES` as read-only views and point
  to `iterable.catalog` / `list_codecs()` instead.
- Add a downstream contract test module that exercises every name undatum imports, so a rename
  fails in this repository first.

## Impact

- Affected specs: `convert`, `open-iterable-structure`
- Affected code: `iterable/convert/core.py`, `iterable/helpers/detect.py`, `iterable/ai/doc.py`,
  `iterable/ai/semantic.py`
- Affected tests: convert codec tests; new `tests/test_downstream_contract.py`
- Downstream: undatum removes `_with_codecargs`, `_filter_bulk_convert_kwargs` and private imports
