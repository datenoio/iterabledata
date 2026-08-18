"""Guardrails so user-facing copy teaches the canonical public API."""

from __future__ import annotations

import ast
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

FORBIDDEN_OPEN = "from iterable.helpers.detect import open_iterable"
FORBIDDEN_CONVERT = "from iterable.convert.core import convert"

USER_FACING_PATHS = [
    ROOT / "README.md",
    ROOT / "AGENTS.md",
    ROOT / "llms.txt",
    ROOT / "llms-full.txt",
    ROOT / "docs" / "docs" / "getting-started",
    ROOT / "docs" / "docs" / "use-cases",
    ROOT / "docs" / "integrations",
    ROOT / "examples",
    ROOT / "skills" / "iterabledata",
    ROOT / ".cursor" / "skills" / "iterabledata-development" / "SKILL.md",
]

TEXT_SUFFIXES = {".md", ".py", ".txt"}


def _iter_user_facing_files():
    for path in USER_FACING_PATHS:
        if path.is_file():
            yield path
            continue
        for child in path.rglob("*"):
            if child.is_file() and child.suffix in TEXT_SUFFIXES:
                yield child


def _load_cookbook(name: str):
    path = ROOT / "examples" / "cookbook" / f"{name}.py"
    spec = importlib.util.spec_from_file_location(f"cookbook_{name}", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_user_facing_copy_uses_public_open_iterable_import():
    offenders = []
    for path in _iter_user_facing_files():
        text = path.read_text(encoding="utf-8")
        if FORBIDDEN_OPEN in text:
            offenders.append(str(path.relative_to(ROOT)))
    assert not offenders, "Internal open_iterable import in user-facing copy:\n" + "\n".join(offenders)


def test_user_facing_copy_uses_public_convert_import():
    offenders = []
    for path in _iter_user_facing_files():
        text = path.read_text(encoding="utf-8")
        if FORBIDDEN_CONVERT in text:
            offenders.append(str(path.relative_to(ROOT)))
    assert not offenders, "Internal convert import in user-facing copy:\n" + "\n".join(offenders)


def test_quick_start_uses_context_manager():
    text = (ROOT / "docs" / "docs" / "getting-started" / "quick-start.md").read_text(encoding="utf-8")
    assert "from iterable import open_iterable" in text
    assert "with open_iterable(" in text
    assert "source.close()" not in text


def test_portable_usage_skill_present():
    skill = ROOT / "skills" / "iterabledata" / "SKILL.md"
    text = skill.read_text(encoding="utf-8")
    assert skill.is_file()
    assert "pip install iterabledata" in text
    assert "from iterable import open_iterable" in text
    assert "pandas" in text.lower()


def test_cookbook_scripts_use_public_imports():
    cookbook = ROOT / "examples" / "cookbook"
    py_files = list(cookbook.glob("*.py"))
    assert py_files, "expected cookbook Python scripts"
    for path in py_files:
        tree = ast.parse(path.read_text(encoding="utf-8"))
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                for alias in node.names:
                    imports.append(f"from {node.module} import {alias.name}")
        joined = "\n".join(imports)
        assert FORBIDDEN_OPEN not in joined
        assert any(
            item in joined
            for item in (
                "from iterable import open_iterable",
                "from iterable.convert import convert",
                "from iterable.ops import inspect",
                "from iterable.ops import schema",
                "from iterable.tools import detect_format",
                "from iterable.tools import read_sample",
            )
        ), f"{path.name} missing canonical import"


def test_cookbook_read_and_inspect_against_fixture():
    fixture = ROOT / "tests" / "fixtures" / "2cols6rows.csv"
    rows = _load_cookbook("read_file").main(str(fixture), limit=3)
    assert len(rows) == 3
    assert isinstance(rows[0], dict)

    result = _load_cookbook("inspect_file").main(str(fixture))
    assert "analysis" in result
    assert result["analysis"].get("fields")


def test_cookbook_gzip_read_against_fixture():
    fixture = ROOT / "tests" / "fixtures" / "2cols6rows_test.csv.gz"
    rows = _load_cookbook("read_gzip").main(str(fixture), limit=2)
    assert len(rows) == 2
    assert isinstance(rows[0], dict)


def test_cookbook_write_jsonl(tmp_path):
    dest = tmp_path / "out.jsonl"
    _load_cookbook("write_jsonl").main(str(dest))
    lines = [line for line in dest.read_text(encoding="utf-8").splitlines() if line.strip()]
    assert len(lines) >= 1
    assert "{" in lines[0]


def test_cookbook_sample_file_against_fixture():
    fixture = ROOT / "tests" / "fixtures" / "2cols6rows.csv"
    result = _load_cookbook("sample_file").main(str(fixture), n=3)
    sample = result["sample"]
    assert sample.get("ok") is True
    rows = (sample.get("data") or {}).get("rows")
    assert isinstance(rows, list)
    assert len(rows) >= 1


def test_cookbook_convert_against_fixture(tmp_path):
    src = ROOT / "tests" / "fixtures" / "2cols6rows.csv"
    dest = tmp_path / "out.jsonl"
    _load_cookbook("convert_formats").main(str(src), str(dest))
    assert dest.is_file()
    assert dest.read_text(encoding="utf-8").strip()
