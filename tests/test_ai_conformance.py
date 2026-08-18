"""
OpenSpec conformance tests for the ai capability.

Maps key scenarios from openspec/specs/ai/spec.md to automated tests (mocked providers).
"""

from unittest.mock import MagicMock, patch

import pytest

from iterable.ai import doc
from iterable.ops import inspect


@pytest.mark.ai
class TestAIDocConformance:
    def test_generate_markdown_with_mock_openai(self):
        """Scenario: Generate markdown documentation."""
        with patch.object(doc, "get_provider") as mock_get_provider:
            mock_provider = MagicMock()
            mock_provider.generate.return_value = "# Dataset Documentation\n\nOverview."
            mock_provider.get_usage_info.return_value = {"total_tokens": 100}
            mock_get_provider.return_value = mock_provider

            result = doc.generate([{"id": 1}], provider="openai", format="markdown")

        assert isinstance(result, str)
        assert "Dataset Documentation" in result
        mock_provider.generate.assert_called_once()

    def test_generate_json_format(self):
        """Scenario: Generate JSON documentation."""
        with patch.object(doc, "get_provider") as mock_get_provider:
            mock_provider = MagicMock()
            mock_provider.generate.return_value = "# Docs"
            mock_provider.get_usage_info.return_value = {"total_tokens": 50}
            mock_get_provider.return_value = mock_provider

            result = doc.generate([{"id": 1}], provider="openai", format="json")

        assert isinstance(result, dict)
        assert "documentation" in result
        assert "usage" in result

    def test_missing_provider_dependency(self):
        """Scenario: Handle missing dependencies."""
        with patch.object(doc, "get_provider", side_effect=ImportError("pip install openai")):
            with pytest.raises(ImportError, match="pip install openai"):
                doc.generate([{"id": 1}], provider="openai")


@pytest.mark.ai
class TestAutodocConformance:
    def test_autodoc_in_analyze(self):
        """Scenario: Autodoc in analyze function."""
        with patch.object(doc, "generate") as mock_generate:
            mock_generate.return_value = {
                "documentation": "# Doc",
                "usage": {"total_tokens": 10},
            }
            result = inspect.analyze("fixtures/2cols6rows.csv", autodoc=True)

        assert "documentation" in result
        assert "documentation_meta" in result
        mock_generate.assert_called_once()

    def test_autodoc_missing_dependencies(self):
        """Scenario: Autodoc missing dependencies."""
        with patch.object(doc, "generate", side_effect=ImportError("install iterabledata[ai]")):
            with pytest.raises(ImportError):
                inspect.analyze("fixtures/2cols6rows.csv", autodoc=True)
