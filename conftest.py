"""Root pytest configuration.

The test session runs with ``--doctest-modules`` (see ``pyproject.toml``), which
makes pytest import every module under the ``iterable`` package to collect
doctests. Format, codec, engine, and database modules import optional
third-party dependencies at module load time; when those dependencies are not
installed the import raises ``ImportError`` and pytest reports a collection
error instead of a clean skip.

To keep a base-environment run free of collection errors, probe each optional
module here and add the ones that cannot be imported to ``collect_ignore`` so
their doctests are skipped. Only ``ImportError`` is treated as "optional
dependency missing"; any other error is left to surface as a real failure.
"""

from __future__ import annotations

import importlib
from pathlib import Path

_ROOT = Path(__file__).parent

# Directories whose modules commonly require optional dependencies.
_OPTIONAL_DIRS = (
    "iterable/datatypes",
    "iterable/codecs",
    "iterable/engines",
    "iterable/db",
)

# This conftest must not itself be collected by --doctest-modules: it would be
# imported as module 'conftest' and clash with tests/conftest.py.
collect_ignore: list[str] = ["conftest.py"]

for _rel_dir in _OPTIONAL_DIRS:
    _dir = _ROOT / _rel_dir
    if not _dir.is_dir():
        continue
    for _path in sorted(_dir.glob("*.py")):
        _module_name = ".".join(_path.relative_to(_ROOT).with_suffix("").parts)
        try:
            importlib.import_module(_module_name)
        except ImportError:
            collect_ignore.append(str(_path))
        except Exception:
            # Non-import errors are real problems; let pytest surface them.
            pass
