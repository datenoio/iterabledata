# Adding formats and codecs

How to extend IterableData with a new file format or compression codec. For third-party packages that must not patch core, use the [plugin system](/api/plugins).

## New format

1. Add `iterable/datatypes/<format>.py` inheriting from `BaseFileIterable` (see `iterable/base.py`)
2. Implement `id()`, `read()`, and `write()` / `write_bulk()` or raise `WriteNotSupportedError`
3. Register a `FormatDescriptor` in `iterable/helpers/format_registry.py` (id, module, class, aliases, `writable`, extras, memory/capability fields)
4. Add detection: extensions, magic bytes, and heuristics as needed in `iterable/helpers/detect.py` / content detection
5. If the id does not match the doc filename, map it in `iterable/helpers/format_descriptions.py` (`DOC_FILENAMES`)
6. Add optional extra in `pyproject.toml` when the format needs a third-party library
7. Tests: `tests/test_<format>.py` with fixtures under `tests/fixtures/` (never modify committed fixtures)
8. Docs: a page under `docs/docs/formats/` from `docs/FORMAT_PAGE_TEMPLATE.md`, plus a row in `formats/index.md` and an entry in `docs/sidebars.js`

User-facing examples must use `open_iterable()` and context managers:

```python
from iterable import open_iterable

with open_iterable("data.newformat") as source:
    for row in source:
        print(row)
```

Do not document `iterable.helpers.detect` as the default import.

## New codec

1. Add `iterable/codecs/<name>codec.py` with `open()`, `close()`, and `fileexts()`
2. Register the extension in `CODEC_REGISTRY` in `iterable/helpers/detect.py`
3. Optional extra in `pyproject.toml` (`compression` is the usual bundle)
4. Tests and a row in [Compression codecs](/api/codecs)

## Checks

```bash
ruff check iterable tests
ruff format iterable tests
pytest tests/test_<format>.py -v
```

New capabilities still need an OpenSpec proposal — see [Contributing](contributing.md).
