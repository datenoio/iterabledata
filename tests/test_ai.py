"""
Tests for AI module.
"""

from unittest.mock import MagicMock, patch

import pytest

from iterable.ai import doc, metadata, semantic


class TestAIDoc:
    def test_generate_mock_openai(self):
        """Test documentation generation with mocked OpenAI provider."""
        # Mock get_provider so we don't need the openai package or API
        with patch.object(doc, "get_provider") as mock_get_provider:
            mock_provider = MagicMock()
            mock_provider.generate.return_value = "# Dataset Documentation\n\nThis is test documentation."
            mock_provider.get_usage_info.return_value = {"total_tokens": 150}
            mock_get_provider.return_value = mock_provider

            result = doc.generate(
                [{"id": 1, "name": "Test"}],
                provider="openai",
                format="markdown",
            )
            assert isinstance(result, str)
            assert "Dataset Documentation" in result
            mock_provider.generate.assert_called_once()

    def test_generate_with_file_path(self):
        """Test generating documentation from file path."""
        # Mock the provider to avoid actual API calls
        with patch.object(doc, "get_provider") as mock_get_provider:
            mock_provider = MagicMock()
            mock_provider.generate.return_value = "# Test Documentation"
            mock_provider.get_usage_info.return_value = {"total_tokens": 100}
            mock_get_provider.return_value = mock_provider

            result = doc.generate(
                "fixtures/2cols6rows.csv",
                provider="openai",
                format="markdown",
            )

            assert isinstance(result, str)
            assert "# Test Documentation" in result
            mock_provider.generate.assert_called_once()

    def test_generate_with_iterable(self):
        """Test generating documentation from iterable."""
        rows = [
            {"id": 1, "name": "John"},
            {"id": 2, "name": "Jane"},
        ]

        with patch.object(doc, "get_provider") as mock_get_provider:
            mock_provider = MagicMock()
            mock_provider.generate.return_value = "# Test Documentation"
            mock_provider.get_usage_info.return_value = {"total_tokens": 100}
            mock_get_provider.return_value = mock_provider

            result = doc.generate(
                rows,
                provider="openai",
                format="markdown",
            )

            assert isinstance(result, str)

    def test_generate_json_format(self):
        """Test generating documentation in JSON format."""
        rows = [{"id": 1, "name": "Test"}]

        with patch.object(doc, "get_provider") as mock_get_provider:
            mock_provider = MagicMock()
            mock_provider.generate.return_value = "# Test Documentation"
            mock_provider.get_usage_info.return_value = {"total_tokens": 100}
            mock_get_provider.return_value = mock_provider

            result = doc.generate(
                rows,
                provider="openai",
                format="json",
            )

            assert isinstance(result, dict)
            assert "documentation" in result
            assert "usage" in result

    def test_generate_html_format(self):
        """Test generating documentation in HTML format."""
        rows = [{"id": 1, "name": "Test"}]

        with patch.object(doc, "get_provider") as mock_get_provider:
            mock_provider = MagicMock()
            mock_provider.generate.return_value = "# Test Documentation"
            mock_provider.get_usage_info.return_value = None
            mock_get_provider.return_value = mock_provider

            result = doc.generate(
                rows,
                provider="openai",
                format="html",
            )

            assert isinstance(result, str)
            assert "<html>" in result.lower() or "<!DOCTYPE" in result

    def test_generate_without_schema(self):
        """Test generating documentation without schema."""
        rows = [{"id": 1, "name": "Test"}]

        with patch.object(doc, "get_provider") as mock_get_provider:
            mock_provider = MagicMock()
            mock_provider.generate.return_value = "# Test Documentation"
            mock_provider.get_usage_info.return_value = None
            mock_get_provider.return_value = mock_provider

            result = doc.generate(
                rows,
                provider="openai",
                include_schema=False,
            )

            assert isinstance(result, str)

    def test_generate_without_samples(self):
        """Test generating documentation without samples."""
        rows = [{"id": 1, "name": "Test"}]

        with patch.object(doc, "get_provider") as mock_get_provider:
            mock_provider = MagicMock()
            mock_provider.generate.return_value = "# Test Documentation"
            mock_provider.get_usage_info.return_value = None
            mock_get_provider.return_value = mock_provider

            result = doc.generate(
                rows,
                provider="openai",
                include_samples=False,
            )

            assert isinstance(result, str)

    def test_generate_unsupported_provider(self):
        """Test handling of unsupported provider."""
        rows = [{"id": 1}]

        with pytest.raises(ValueError, match="Unknown provider"):
            doc.generate(rows, provider="unsupported")

    def test_provider_import_error(self):
        """Test handling of missing provider dependencies."""
        rows = [{"id": 1}]

        # This will raise ImportError if dependencies are missing
        # We test the error message
        try:
            doc.generate(rows, provider="openai")
        except ImportError as e:
            assert "requires additional dependencies" in str(e) or "Install with" in str(e)

    def test_generate_yaml_format(self):
        """Test generating documentation in YAML format."""
        rows = [{"id": 1, "name": "Test"}]

        with patch.object(doc, "get_provider") as mock_get_provider:
            mock_provider = MagicMock()
            mock_provider.generate.return_value = "# Test Documentation"
            mock_provider.get_usage_info.return_value = {"total_tokens": 100}
            mock_get_provider.return_value = mock_provider

            result = doc.generate(
                rows,
                provider="openai",
                format="yaml",
            )

            assert isinstance(result, str)
            # YAML should contain documentation text
            assert "Test Documentation" in result or "documentation" in result.lower()

    def test_generate_text_format(self):
        """Test generating documentation in text format."""
        rows = [{"id": 1, "name": "Test"}]

        with patch.object(doc, "get_provider") as mock_get_provider:
            mock_provider = MagicMock()
            mock_provider.generate.return_value = "# Test Documentation\n\nSome content."
            mock_provider.get_usage_info.return_value = None
            mock_get_provider.return_value = mock_provider

            result = doc.generate(
                rows,
                provider="openai",
                format="text",
            )

            assert isinstance(result, str)
            assert "Test Documentation" in result

    def test_generate_with_metadata_extraction(self):
        """Test generating documentation with metadata extraction."""
        rows = [
            {"country": "USA", "region": "California", "date": "2024-01-01"},
            {"country": "USA", "region": "New York", "date": "2024-01-02"},
        ]

        with patch.object(doc, "get_provider") as mock_get_provider:
            mock_provider = MagicMock()
            mock_provider.generate.return_value = "# Test Documentation"
            mock_provider.get_usage_info.return_value = None
            mock_get_provider.return_value = mock_provider

            result = doc.generate(
                rows,
                provider="openai",
                include_metadata=True,
                format="json",
            )

            assert isinstance(result, dict)
            # Metadata should be included in JSON output
            assert "metadata" in result or "documentation" in result

    def test_generate_with_field_descriptions(self):
        """Test generating documentation with field descriptions."""
        rows = [{"id": 1, "name": "Test"}]

        with patch.object(doc, "get_provider") as mock_get_provider:
            mock_provider = MagicMock()
            mock_provider.generate.return_value = "# Test Documentation"
            mock_provider.get_fields_info.return_value = {"id": "Identifier", "name": "Name"}
            mock_provider.get_usage_info.return_value = None
            mock_get_provider.return_value = mock_provider

            result = doc.generate(
                rows,
                provider="openai",
                include_field_descriptions=True,
            )

            assert isinstance(result, str)
            mock_provider.get_fields_info.assert_called_once()

    def test_generate_with_statistics(self):
        """Test generating documentation with statistics."""
        rows = [{"id": 1, "value": 10}, {"id": 2, "value": 20}]

        with patch.object(doc, "get_provider") as mock_get_provider:
            mock_provider = MagicMock()
            mock_provider.generate.return_value = "# Test Documentation"
            mock_provider.get_usage_info.return_value = None
            mock_get_provider.return_value = mock_provider

            result = doc.generate(
                rows,
                provider="openai",
                include_statistics=True,
                format="json",
            )

            assert isinstance(result, dict)

    def test_generate_without_metadata(self):
        """Test generating documentation without metadata extraction."""
        rows = [{"id": 1, "name": "Test"}]

        with patch.object(doc, "get_provider") as mock_get_provider:
            mock_provider = MagicMock()
            mock_provider.generate.return_value = "# Test Documentation"
            mock_provider.get_usage_info.return_value = None
            mock_get_provider.return_value = mock_provider

            result = doc.generate(
                rows,
                provider="openai",
                include_metadata=False,
            )

            assert isinstance(result, str)

    def test_generate_with_language(self):
        """Test generating documentation with specific language."""
        rows = [{"id": 1, "name": "Test"}]

        with patch.object(doc, "get_provider") as mock_get_provider:
            mock_provider = MagicMock()
            mock_provider.generate.return_value = "# Test Documentation"
            mock_provider.get_usage_info.return_value = None
            mock_get_provider.return_value = mock_provider

            result = doc.generate(
                rows,
                provider="openai",
                language="Spanish",
            )

            assert isinstance(result, str)
            # Check that language was passed to prompt (kwargs or first positional)
            call_args = mock_provider.generate.call_args
            assert call_args is not None
            prompt = (call_args.kwargs.get("prompt", "") if call_args.kwargs else "") or (
                call_args.args[0] if call_args.args else ""
            )
            assert "Spanish" in prompt or "spanish" in (prompt or "").lower()


class TestMetadataExtraction:
    """Tests for metadata extraction utilities."""

    def test_extract_keywords(self):
        """Test keyword extraction from field names."""
        field_names = ["user_id", "user_name", "email_address"]
        keywords = metadata.extract_keywords(field_names)
        assert isinstance(keywords, list)
        assert len(keywords) > 0

    def test_extract_keywords_with_samples(self):
        """Test keyword extraction with sample data."""
        field_names = ["name", "description"]
        samples = [
            {"name": "Product A", "description": "High quality product"},
            {"name": "Product B", "description": "Premium item"},
        ]
        keywords = metadata.extract_keywords(field_names, samples)
        assert isinstance(keywords, list)

    def test_extract_geographic_coverage(self):
        """Test geographic coverage extraction."""
        samples = [
            {"country": "USA", "region": "California"},
            {"country": "USA", "region": "New York"},
        ]
        field_names = ["country", "region"]
        coverage = metadata.extract_geographic_coverage(samples, field_names)
        assert isinstance(coverage, dict)
        assert "countries" in coverage
        assert "regions" in coverage

    def test_extract_temporal_coverage(self):
        """Test temporal coverage extraction."""
        samples = [
            {"date": "2024-01-01"},
            {"date": "2024-12-31"},
        ]
        field_names = ["date"]
        # This may return None if pandas is not available
        coverage = metadata.extract_temporal_coverage(samples, field_names)
        # Should return dict or None
        assert coverage is None or isinstance(coverage, dict)

    def test_detect_languages(self):
        """Test language detection."""
        samples = [
            {"text": "This is a test in English language"},
            {"text": "Another sample text for language detection"},
        ]
        field_names = ["text"]
        # This may return empty list if langdetect is not available
        languages = metadata.detect_languages(samples, field_names)
        assert isinstance(languages, list)

    def test_classify_data_theme(self):
        """Test data theme classification."""
        field_names = ["health", "patient", "medical"]
        keywords = ["health", "medical", "hospital"]
        theme = metadata.classify_data_theme(field_names, keywords)
        # Should return dict with label and uri, or None
        assert theme is None or isinstance(theme, dict)


class TestSemanticDetection:
    """Tests for semantic type and PII detection."""

    def test_detect_semantic_types_no_file(self):
        """Test semantic type detection without file."""
        # Should return empty dict when no file provided
        result = semantic.detect_semantic_types("nonexistent.txt", ["field1"])
        assert isinstance(result, dict)
        # Should have empty lists for fields
        assert all(types == [] for types in result.values())

    def test_detect_pii_no_file(self):
        """Test PII detection without file."""
        # Should return empty list when no file provided
        result = semantic.detect_pii("nonexistent.txt", ["field1"])
        assert isinstance(result, list)

    def test_mask_pii_samples(self):
        """Test PII masking in samples."""
        samples = [
            {"email": "test@example.com", "name": "John"},
            {"email": "user@example.com", "name": "Jane"},
        ]
        field_names = ["email", "name"]
        pii_fields = [{"field": "email", "type": "email"}]
        masked = semantic.mask_pii_samples(samples, field_names, pii_fields)
        assert len(masked) == len(samples)
        # Email should be masked
        assert masked[0]["email"] == "***"
        # Name should remain
        assert masked[0]["name"] == "John"
