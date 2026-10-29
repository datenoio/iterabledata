# Change: Honor CSV dialect options, TSV defaults and codecs with an explicit format

## Why

undatum carries three workarounds for iterabledata reader/writer defects, all reproduced on 1.0.23:

1. **CSV dialect options are dropped.** `open_iterable()` passes `iterableargs` to `CSVIterable` as
   `options=`. `BaseIterable._apply_options()` sets `self.delimiter`, but `CSVIterable.__init__` then
   overwrites it with `","` because its own `delimiter=` argument is `None`. The same happens to
   `quotechar`, `keys` and `autodetect`. `open_iterable("a.csv", iterableargs={"delimiter": ";"})`
   returns `[{"a;b": "1;2"}]`, and writing with `{"delimiter": "\t"}` writes commas. undatum
   monkeypatches `iterable.convert.core.open_iterable` to re-apply the delimiter.
2. **`.tsv` is read and written as comma-separated.** The registry maps `tsv` to `CSVIterable` as a
   plain alias, so `open_iterable("t.tsv")` splits on commas and writing `out.tsv` emits commas.
3. **An explicit format drops the codec.** `_apply_explicit_format()` sets `result["codec"] = None`,
   so `open_iterable("x.csv.gz", iterableargs={"format": "csv"})` parses gzip bytes as text and
   `data.zip` with `format="jsonl"` fails with `UnicodeDecodeError`. undatum works around this by
   creating a temporary symlink named `data.<format>.<codec>`.

Also found during this review: `CSVIterable.totals()` counts newlines, so it includes the header
and every newline inside quoted fields (`totals()` returned 4 for a 2-row file).

## What Changes

- `CSVIterable` reads `delimiter`, `quotechar`, `escapechar`, `doublequote`, `keys`, `autodetect`
  and `encoding` from `options` when the constructor argument is not given. Precedence: constructor
  argument, then `options`, then the extension default, then autodetection.
- Default to a tab delimiter for `.tsv` names (also `.tsv.gz` etc.) and `format="tsv"`, for reads
  and writes; keep `psv`/`ssv` as is.
- An explicit `format` keeps the codec detected from the last extension (`.gz`, `.zst`, `.zip`, ...).
  Accept an explicit `codec` hint in `iterableargs` for names without a codec extension.
- `CSVIterable.totals()` excludes the header row and counts an unterminated last line; the docs
  say it is an estimate when quoted fields contain line breaks.

## Impact

- Affected specs: `datatype-implementation`, `open-iterable-structure`
- Affected code: `iterable/datatypes/{csv,psv}.py`, `iterable/helpers/open_iterable.py`,
  `iterable/helpers/utils.py` (`rowincount(include_unterminated=...)`)
- Affected tests: `tests/test_csv.py`, `tests/test_openiterable.py`, codec detection tests
- Downstream: undatum can remove `_with_csv_options`, `apply_iterable_csv_delimiter` and
  `_codec_safe_source`
