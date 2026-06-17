"""Tests for llms.txt machine index."""

from pathlib import Path

REQUIRED_SECTIONS = [
    "## Entry points",
    "## Optional extras",
    "## Examples",
    "## Agent / contributor docs",
    "## Specifications",
    "## API documentation",
    "## Conventions",
]


def test_llms_txt_exists():
    path = Path(__file__).resolve().parents[1] / "llms.txt"
    assert path.is_file()


def test_llms_txt_required_sections():
    path = Path(__file__).resolve().parents[1] / "llms.txt"
    content = path.read_text(encoding="utf-8")
    for section in REQUIRED_SECTIONS:
        assert section in content, f"Missing section: {section}"


def test_llms_txt_lists_primary_apis():
    path = Path(__file__).resolve().parents[1] / "llms.txt"
    content = path.read_text(encoding="utf-8")
    assert "open_iterable" in content
    assert "iterable.ai" in content or "from iterable.ai import doc" in content
    assert "AGENTS.md" in content
