"""Heuristic prompt coverage over the public LLM generation corpus.

No network and no paid APIs: concatenate skill + llms-full + cookbook and
assert that common user prompts still retrieve canonical IterableData snippets.
"""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

CORPUS_PATHS = [
    ROOT / "llms-full.txt",
    ROOT / "skills" / "iterabledata" / "SKILL.md",
    ROOT / "docs" / "docs" / "getting-started" / "cookbook.md",
    ROOT / "docs" / "docs" / "getting-started" / "when-to-use.md",
    *sorted((ROOT / "examples" / "cookbook").glob("*.py")),
]

# Prompt -> substrings that must appear somewhere in the public corpus.
PROMPTS: list[tuple[str, tuple[str, ...]]] = [
    ("read this CSV", ("from iterable import open_iterable", "with open_iterable(")),
    ("convert XML to JSONL", ("from iterable.convert import convert", "convert(")),
    ("stream a large file without pandas", ("from iterable import open_iterable", "open_iterable(")),
    ("write records to jsonl", ('mode="w"', "from iterable import open_iterable")),
    ("read this XML file as records", ("iterableargs", "tagname")),
    ("infer schema", ("schema", "from iterable.ops import")),
    ("pip install iterabledata", ("pip install iterabledata", "from iterable import open_iterable")),
]


def _corpus() -> str:
    return "\n".join(path.read_text(encoding="utf-8") for path in CORPUS_PATHS)


def test_prompt_eval_corpus_uses_canonical_imports():
    text = _corpus()
    assert "from iterable.helpers.detect import open_iterable" not in text
    assert "from iterable.convert.core import convert" not in text
    assert "from iterable import open_iterable" in text
    assert "from iterable.convert import convert" in text


def test_prompt_eval_covers_common_generation_prompts():
    text = _corpus()
    missing: list[str] = []
    for prompt, needles in PROMPTS:
        if any(needle not in text for needle in needles):
            missing.append(f"{prompt}: {needles}")
    assert not missing, "Public corpus no longer answers prompts:\n" + "\n".join(missing)
