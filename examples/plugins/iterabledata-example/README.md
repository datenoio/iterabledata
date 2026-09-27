# iterabledata-example

Reference plugin for [IterableData](https://pypi.org/project/iterabledata/):
a minimal `.journal` format where each line is one record of `key=value`
pairs separated by `;`:

```text
level=info;msg=started;pid=4242
level=warn;msg=slow query;elapsed_ms=812
```

It exists to prove the plugin contract end-to-end: packaging metadata,
entry-point discovery, and use through the public `open_iterable()` API
with **no changes to the core library**.

## Layout

```
pyproject.toml                     # packaging + entry point metadata
src/iterabledata_example/
  __init__.py
  journal.py                       # JournalIterable (read + write)
```

The entry point registers the format under the id `journal`:

```toml
[project.entry-points."iterabledata.formats"]
journal = "iterabledata_example.journal:JournalIterable"
```

## Install and use

```bash
pip install iterabledata            # the core library
pip install ./examples/plugins/iterabledata-example   # this plugin (local path)
```

```python
from iterable import open_iterable

with open_iterable("app.journal", mode="w") as target:
    target.write({"level": "info", "msg": "started"})

with open_iterable("app.journal") as source:
    for row in source:
        print(row)  # {'level': 'info', 'msg': 'started'}
```

Discovery is lazy: the first `open_iterable()` call scans installed
distributions for the `iterabledata.formats` entry-point group.

## Publishing your own plugin

Copy this layout, rename the package and format id, and publish with
`python -m build` + `twine upload` (or your preferred tooling). Keep the
entry-point group names exactly as shown — they are the discovery contract.
