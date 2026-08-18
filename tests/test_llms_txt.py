"""Tests for llms.txt / llms-full.txt machine indexes."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

LLMS_SECTIONS = [
    "## Entry points",
    "## Optional extras",
    "## Examples",
    "## Agent / contributor docs",
    "## Specifications",
    "## API documentation",
    "## Conventions",
]

LLMS_FULL_MARKERS = [
    "## Read a compressed file",
    "## Write JSONL",
    "## Convert formats",
    "## Open XML",
    "## Inspect an unknown file",
    "iterableargs",
    "from iterable import open_iterable",
    "from iterable.convert import convert",
]


def test_llms_txt_exists():
    assert (ROOT / "llms.txt").is_file()


def test_llms_full_txt_exists():
    assert (ROOT / "llms-full.txt").is_file()


def test_llms_txt_required_sections():
    content = (ROOT / "llms.txt").read_text(encoding="utf-8")
    for section in LLMS_SECTIONS:
        assert section in content, f"Missing section: {section}"


def test_llms_txt_lists_primary_apis():
    content = (ROOT / "llms.txt").read_text(encoding="utf-8")
    assert "from iterable import open_iterable" in content
    assert "from iterable.convert import convert" in content
    assert "iterable.ai" in content or "from iterable.ai import doc" in content
    assert "AGENTS.md" in content
    assert "iterabledata" in content
    assert "import package is `iterable`" in content or "Import: `from iterable import open_iterable`" in content


def test_llms_full_txt_recipes():
    content = (ROOT / "llms-full.txt").read_text(encoding="utf-8")
    for marker in LLMS_FULL_MARKERS:
        assert marker in content, f"Missing recipe marker: {marker}"


def test_docs_static_copies_match_root():
    for name in ("llms.txt", "llms-full.txt"):
        root = (ROOT / name).read_text(encoding="utf-8")
        static = (ROOT / "docs" / "static" / name).read_text(encoding="utf-8")
        assert root == static, f"docs/static/{name} is out of date; run dev/scripts/generate_llms_txt.py"
    well_known = (ROOT / "docs" / "static" / ".well-known" / "llms.txt").read_text(encoding="utf-8")
    assert well_known == (ROOT / "llms.txt").read_text(encoding="utf-8")


def test_robots_txt_allows_machine_indexes():
    robots = (ROOT / "docs" / "static" / "robots.txt").read_text(encoding="utf-8")
    assert "/iterabledata/llms.txt" in robots
    assert "/iterabledata/llms-full.txt" in robots
    assert "/iterabledata/.well-known/llms.txt" in robots


def test_docs_site_advertises_machine_indexes():
    config = (ROOT / "docs" / "docusaurus.config.js").read_text(encoding="utf-8")
    assert "llms.txt" in config
    assert "llms-full.txt" in config
    homepage = (ROOT / "docs" / "src" / "pages" / "index.js").read_text(encoding="utf-8")
    assert "getting-started/cookbook" in homepage
    sidebars = (ROOT / "docs" / "sidebars.js").read_text(encoding="utf-8")
    assert "integrations/BUILDING_AGENTS" in sidebars
    assert "integrations/MCP" in sidebars
    assert "integrations/DISCOVERY" in sidebars
