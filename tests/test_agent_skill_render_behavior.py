"""Behavior-pinning tests for _render_agent_skill_md (complexity refactor).

Pins the exact markdown produced by
``iterable.ai.blocks._render_agent_skill_md`` before/after the
behavior-preserving decomposition: YAML frontmatter quoting, section order and
presence rules, empty/blank list filtering, ``record_count: 0`` handling, and
localized section headings.
"""

from iterable.ai.blocks import _render_agent_skill_md

FULL_DATA = {
    "name": "sales-dataset-skill",
    "description": "Use this skill when analyzing sales.csv.",
    "when_to_use": "Load when the user asks about sales trends.",
    "file_name": "sales.csv",
    "format": "csv",
    "record_count": 1200,
    "fields": ["id", "amount", "sold_at"],
    "dataset_caveats": ["Amounts are in USD cents.", "", "  ", None],
    "workflow_steps": ["Load the file.", "Group by sold_at."],
    "safety_constraints": ["Read-only analysis only."],
    "example_steps": ["Compute total revenue."],
}

FULL_EXPECTED = (
    "---\n"
    "name: sales-dataset-skill\n"
    "description: Use this skill when analyzing sales.csv.\n"
    "---\n"
    "\n"
    "# sales-dataset-skill\n"
    "\n"
    "## When to use\n"
    "\n"
    "Load when the user asks about sales trends.\n"
    "\n"
    "## Dataset facts\n"
    "\n"
    "- **File name:** `sales.csv`\n"
    "- **Format:** `csv`\n"
    "- **Records:** 1200\n"
    "- **Fields:** `id`, `amount`, `sold_at`\n"
    "\n"
    "## Dataset caveats\n"
    "\n"
    "- Amounts are in USD cents.\n"
    "\n"
    "## Workflow\n"
    "\n"
    "1. Load the file.\n"
    "2. Group by sold_at.\n"
    "\n"
    "## Safety constraints\n"
    "\n"
    "- Read-only analysis only.\n"
    "\n"
    "## Example analysis steps\n"
    "\n"
    "1. Compute total revenue.\n"
)


class TestFullDocument:
    def test_full_document_exact(self):
        assert _render_agent_skill_md(FULL_DATA) == FULL_EXPECTED

    def test_output_ends_with_single_newline(self):
        result = _render_agent_skill_md(FULL_DATA)
        assert result.endswith("\n")
        assert not result.endswith("\n\n")


class TestMinimalDocuments:
    def test_empty_data(self):
        """Defaults: name falls back to 'dataset-skill', description quoted empty."""
        expected = '---\nname: dataset-skill\ndescription: ""\n---\n\n# dataset-skill\n\n## Dataset facts\n'
        assert _render_agent_skill_md({}) == expected

    def test_record_count_zero_is_rendered(self):
        """``record_count: 0`` is not None, so the Records line appears."""
        result = _render_agent_skill_md({"name": "x", "record_count": 0})
        assert "- **Records:** 0\n" in result

    def test_missing_record_count_omitted(self):
        result = _render_agent_skill_md({"name": "x"})
        assert "Records" not in result

    def test_empty_fields_omitted(self):
        result = _render_agent_skill_md({"name": "x", "fields": []})
        assert "Fields" not in result

    def test_sections_with_only_blank_items_omitted(self):
        """Lists containing only blank/non-string items produce no section."""
        result = _render_agent_skill_md({"name": "x", "dataset_caveats": ["", "  ", None]})
        assert "caveats" not in result.lower()

    def test_when_to_use_absent_by_default(self):
        result = _render_agent_skill_md({"name": "x"})
        assert "When to use" not in result


class TestFrontmatterQuoting:
    def test_special_chars_quoted(self):
        result = _render_agent_skill_md({"name": 'weird: "name"', "description": "has: colon"})
        assert result.startswith('---\nname: "weird: \\"name\\""\ndescription: "has: colon"\n---\n')

    def test_heading_uses_raw_name(self):
        result = _render_agent_skill_md({"name": 'weird: "name"'})
        assert '\n# weird: "name"\n' in result


class TestLocalization:
    def test_russian_headings(self):
        result = _render_agent_skill_md({"name": "x", "workflow_steps": ["Шаг один."]}, language="ru")
        assert "## Факты о наборе данных" in result
        assert "## Рабочий процесс" in result
        assert "1. Шаг один.\n" in result

    def test_unknown_language_falls_back_to_english(self):
        result = _render_agent_skill_md({"name": "x", "workflow_steps": ["Step."]}, language="klingon")
        assert "## Dataset facts" in result
        assert "## Workflow" in result
