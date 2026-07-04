"""Import regressions for optional dependencies."""

import subprocess
import sys
import textwrap
from pathlib import Path


def test_import_iterable_without_bson_or_pydantic():
    repo_root = Path(__file__).resolve().parents[1]
    script = textwrap.dedent(
        """
        import importlib.abc
        import sys


        class OptionalDependencyBlocker(importlib.abc.MetaPathFinder):
            blocked = ("bson", "pydantic")

            def find_spec(self, fullname, path=None, target=None):
                if fullname in self.blocked or fullname.startswith(tuple(name + "." for name in self.blocked)):
                    raise ModuleNotFoundError(f"No module named {fullname!r}")
                return None


        sys.meta_path.insert(0, OptionalDependencyBlocker())
        for module_name in list(sys.modules):
            if module_name == "iterable" or module_name.startswith("iterable."):
                del sys.modules[module_name]
            if module_name in OptionalDependencyBlocker.blocked:
                del sys.modules[module_name]
            if module_name.startswith(tuple(name + "." for name in OptionalDependencyBlocker.blocked)):
                del sys.modules[module_name]

        import iterable
        from iterable.helpers.schema import get_schema

        schema = get_schema({"id": 1, "name": "Alice"})
        assert iterable.__version__
        assert schema["id"]["type"] == "integer"
        assert schema["name"]["type"] == "string"
        print(iterable.__version__)
        """
    )

    result = subprocess.run(
        [sys.executable, "-c", script],
        cwd=repo_root,
        check=True,
        capture_output=True,
        text=True,
    )

    assert result.stdout.strip()
