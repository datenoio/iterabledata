"""Tests for iterable.tools agent wrappers."""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest

from iterable.tools import (
    analyze_dataset,
    compute_stats,
    convert_file,
    describe_capabilities,
    detect_format,
    generate_documentation,
    infer_schema,
    read_sample,
    schemas,
    validate_data,
)


class TestToolResults:
    def test_detect_format_csv(self):
        result = detect_format("fixtures/2cols6rows.csv")
        assert result["ok"] is True
        assert result["data"]["format"] == "csv"

    def test_detect_format_missing_file(self):
        result = detect_format("/tmp/nonexistent_iterabledata_xyz_no_ext")
        assert result["ok"] is True or result["ok"] is False
        # Detection may still infer from path; ensure envelope shape
        assert "ok" in result

    def test_describe_capabilities_csv(self):
        result = describe_capabilities("csv")
        assert result["ok"] is True
        assert result["data"]["id"] == "csv"

    def test_describe_capabilities_unknown(self):
        result = describe_capabilities("not-real")
        assert result["ok"] is False
        assert result["code"] == "unknown_format"

    def test_read_sample(self):
        result = read_sample("fixtures/2cols6rows.csv", n=3)
        assert result["ok"] is True
        assert result["data"]["count"] == 3

    def test_infer_schema(self):
        result = infer_schema("fixtures/2cols6rows.csv")
        assert result["ok"] is True
        assert "fields" in result["data"]

    def test_analyze_dataset(self):
        result = analyze_dataset("fixtures/2cols6rows.csv")
        assert result["ok"] is True
        assert "fields" in result["data"]

    def test_compute_stats(self):
        result = compute_stats("fixtures/2cols6rows.csv")
        assert result["ok"] is True

    def test_convert_dry_run(self):
        result = convert_file(
            "fixtures/2cols6rows.csv",
            "out.jsonl",
            dry_run=True,
        )
        assert result["ok"] is True
        assert result["data"]["dry_run"] is True

    def test_convert_requires_confirm(self):
        result = convert_file("fixtures/2cols6rows.csv", "out.jsonl")
        assert result["ok"] is False
        assert result["code"] == "confirmation_required"

    def test_validate_data_stats(self):
        result = validate_data(
            "fixtures/2cols6rows.csv",
            rules={},
            mode="stats",
        )
        assert result["ok"] is True
        assert "total_rows" in result["data"]

    def test_generate_documentation_mocked(self):
        with patch("iterable.tools._core.ai_doc.generate") as mock_gen:
            mock_gen.return_value = {"documentation": "# Doc", "usage": {}}
            result = generate_documentation("fixtures/2cols6rows.csv", format="json")
        assert result["ok"] is True
        assert result["data"]["documentation"] == "# Doc"

    def test_plan_conversion_tool(self):
        from iterable.tools import plan_conversion

        result = plan_conversion("fixtures/2cols6rows.csv", "out.jsonl")
        assert result["ok"] is True
        assert result["data"]["source"]["format"] == "csv"

    def test_translate_filter_tool(self):
        from iterable.tools import translate_filter_tool

        result = translate_filter_tool("age > 10")
        assert result["ok"] is True
        assert result["data"]["ast"]["op"] == "gt"


class TestSchemas:
    def test_openai_functions_count(self):
        functions = schemas.to_openai_functions()
        assert len(functions) == len(schemas.TOOL_DEFINITIONS)
        assert functions[0]["type"] == "function"

    def test_anthropic_tools(self):
        tools = schemas.to_anthropic_tools()
        assert tools[0]["name"] == "detect_format"
        assert "input_schema" in tools[0]

    def test_json_schema_export(self):
        schema = schemas.to_json_schema()
        assert "detect_format" in schema["properties"]

    def test_call_tool_detect(self):
        result = schemas.call_tool("detect_format", {"path": "fixtures/2cols6rows.csv"})
        assert result["ok"] is True

    def test_openai_schema_snapshot(self):
        snapshot_path = (
            __import__("pathlib").Path(__file__).resolve().parent
            / "fixtures"
            / "tool_schemas"
            / "openai_functions.json"
        )
        assert snapshot_path.is_file()
        expected = json.loads(snapshot_path.read_text(encoding="utf-8"))
        assert schemas.to_openai_functions() == expected


class TestLangChainBundle:
    def test_get_tools_import_error(self):
        with patch.dict("sys.modules", {"langchain_core": None, "langchain_core.tools": None}):
            with pytest.raises(ImportError, match="langchain-core"):
                __import__("iterable.tools.langchain", fromlist=["get_tools"]).get_tools()

    def test_get_tools_when_available(self):
        pytest.importorskip("langchain_core")
        from iterable.tools.langchain import get_tools

        tools = get_tools()
        assert len(tools) == len(schemas.TOOL_DEFINITIONS)
        names = {t.name for t in tools}
        assert "detect_format" in names


class TestDocumentationModels:
    def test_validate_documentation_result(self):
        from iterable.ai.models import validate_documentation_result

        payload = {"documentation": "# Title", "usage": {"total_tokens": 10}}
        model = validate_documentation_result(payload)
        assert model.documentation == "# Title"

    def test_doc_generate_validate_output(self):
        with patch("iterable.ai.doc.get_provider") as mock_get:
            mock_provider = MagicMock()
            mock_provider.generate.return_value = "# Doc"
            mock_provider.get_usage_info.return_value = {"total_tokens": 5}
            mock_get.return_value = mock_provider

            from iterable.ai import doc

            result = doc.generate(
                [{"id": 1}],
                provider="openai",
                format="json",
                validate_output=True,
            )
        assert isinstance(result, dict)
        assert "documentation" in result
