## 1. CSV dialect options

- [x] 1.1 Resolve `delimiter`, `quotechar`, `escapechar`, `doublequote`, `keys`, `autodetect` from `options` in `CSVIterable.__init__` with the documented precedence.
- [x] 1.2 Pass the resolved dialect to both `DictReader` and `DictWriter`.
- [x] 1.3 Tests: read and write with `iterableargs={"delimiter": ";"}`, `{"delimiter": "\t"}`, `{"quotechar": "'"}` through `open_iterable()` and through `convert(..., toiterableargs=...)`.

## 2. TSV defaults

- [x] 2.1 Default to a tab delimiter in `CSVIterable` when the file name ends in `.tsv` (optionally followed by a codec extension) or `format="tsv"` is given; the registry alias is unchanged.
- [x] 2.2 Tests: `open_iterable("t.tsv")` splits on tabs; writing `out.tsv` and `out.tsv.gz` emits tabs; an explicit `delimiter` still wins.

## 3. Explicit format keeps the codec

- [x] 3.1 In `_apply_explicit_format()`, keep the detected codec when the last extension is a registered codec.
- [x] 3.2 Accept `iterableargs["codec"]` as an explicit codec hint.
- [x] 3.3 Tests: `x.csv.gz` + `format="csv"`, `data.zip` + `format="jsonl"`, `data.bin` + `format="jsonl"`, `codec="gz"`.

## 4. CSV totals

- [x] 4.1 Exclude the header row from `CSVIterable.totals()` when `keys` were not supplied.
- [x] 4.2 Document that CSV totals are a line-based estimate when quoted fields contain newlines; add a test for both cases.

## 5. Verification

- [x] 5.1 Update `CHANGELOG.md` and `docs/docs/formats/csv.md` (TSV defaults, option precedence).
- [x] 5.2 Run `ruff check iterable tests`, focused tests and the full suite.
