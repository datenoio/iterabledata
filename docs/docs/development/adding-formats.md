# Adding formats and codecs

How to extend IterableData with a new file format or compression codec. For third-party packages that must not patch core, use the [plugin system](/api/plugins) (see the worked plugin example at the end of that page).

## New format (in-tree)

1. Add `iterable/datatypes/<format>.py` inheriting from `BaseFileIterable` (see `iterable/base.py`)
2. Implement `id()`, `fileexts()`, `read()`, and `write()` / `write_bulk()` — or raise `WriteNotSupportedError` for read-only formats
3. Register a `FormatDescriptor` in `iterable/helpers/format_registry.py` (id, module, class, aliases, `writable`, extras, memory/capability fields)
4. Add detection: extensions, magic bytes, and heuristics as needed in `iterable/helpers/detect.py` / content detection
5. If the id does not match the doc filename, map it in `iterable/helpers/format_descriptions.py` (`DOC_FILENAMES`)
6. Add optional extra in `pyproject.toml` when the format needs a third-party library
7. Tests: `tests/test_<format>.py` with fixtures under `tests/fixtures/` (never modify committed fixtures)
8. Docs: a page under `docs/docs/formats/` from `docs/FORMAT_PAGE_TEMPLATE.md`, plus a row in `formats/index.md` and an entry in `docs/sidebars.js`

### Worked example: minimal read-only format

```python
# iterable/datatypes/acme.py
from __future__ import annotations

from typing import Any, IO

from ..base import BaseCodec, BaseFileIterable
from ..exceptions import WriteNotSupportedError
from ..types import Row


class AcmeIterable(BaseFileIterable):
    """One JSON-ish line per record: key=value pairs separated by commas."""

    datamode = "text"

    @staticmethod
    def id() -> str:
        return "acme"

    @staticmethod
    def fileexts() -> list[str]:
        return [".acme"]

    def __init__(
        self,
        filename: str | None = None,
        stream: IO[Any] | None = None,
        codec: BaseCodec | None = None,
        mode: str = "r",
        encoding: str = "utf-8",
        options: dict[str, Any] | None = None,
    ):
        if mode not in ("r", "rb"):
            raise WriteNotSupportedError("acme", "Acme is read-only")
        super().__init__(
            filename,
            stream,
            codec=codec,
            mode=mode,
            encoding=encoding,
            options=options or {},
        )

    def read(self, skip_empty: bool = True) -> Row:
        line = self.fobj.readline()
        if not line:
            raise StopIteration
        line = line.strip()
        if skip_empty and not line:
            return self.read(skip_empty=skip_empty)
        row: Row = {}
        for part in line.split(","):
            if "=" not in part:
                continue
            key, value = part.split("=", 1)
            row[key.strip()] = value.strip()
        return row
```

Register it next to the other descriptors:

```python
# in iterable/helpers/format_registry.py
_fmt(
    "acme",
    "iterable.datatypes.acme",
    "AcmeIterable",
    aliases=(),
    text=True,
    writable=False,
    description="Acme key=value line format",
)
```

User-facing examples must use `open_iterable()` and context managers:

```python
from iterable import open_iterable

with open_iterable("data.acme") as source:
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

## Prefer a plugin when shipping outside core

If the format should live in a separate package (private fork, niche dependency, or community extension), implement the same `BaseFileIterable` subclass and register it via the `iterabledata.formats` entry point. See [Plugin system](/api/plugins#creating-a-format-plugin) for a complete package layout and install flow.
