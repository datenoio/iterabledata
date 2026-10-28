"""Behavior-pinning tests for iterable.ai.doc.generate (complexity refactor).

These tests pin the observable behavior of ``doc.generate`` before/after the
behavior-preserving decomposition refactor: output formats, caching, provider
interaction, context collection (schema/stats/metadata/semantic/PII) and
error handling. All LLM calls are mocked.
"""

from unittest.mock import MagicMock, patch

import pytest

from iterable.ai import doc, models
from iterable.ai.cache import cache_clear


def _make_provider(text="# Generated Documentation", fields_info=None):
    provider = MagicMock()
    provider.generate.return_value = text
    provider.get_usage_info.return_value = {"total_tokens": 42}
    provider.get_fields_info.return_value = fields_info or {}
    return provider


@pytest.fixture(autouse=True)
def _clear_doc_cache():
    cache_clear()
    yield
    cache_clear()


class TestGenerateBasicPaths:
    def test_markdown_returns_generated_text(self):
        with patch.object(doc, "get_provider") as mock_get:
            provider = _make_provider()
            mock_get.return_value = provider
            result = doc.generate([{"id": 1, "name": "a"}], provider="openai", format="markdown")
        assert result == "# Generated Documentation"
        provider.generate.assert_called_once()

    def test_default_format_is_markdown(self):
        with patch.object(doc, "get_provider") as mock_get:
            mock_get.return_value = _make_provider("plain text body")
            result = doc.generate([{"id": 1}], provider="openai")
        assert result == "plain text body"

    def test_unknown_format_returns_raw_text(self):
        """Any format other than json/html/yaml/text falls through to raw markdown text."""
        with patch.object(doc, "get_provider") as mock_get:
            mock_get.return_value = _make_provider("raw body")
            result = doc.generate([{"id": 1}], provider="openai", format="weird-format")
        assert result == "raw body"

    def test_json_format_structure(self):
        rows = [{"id": 1, "name": "Test"}]
        with patch.object(doc, "get_provider") as mock_get:
            mock_get.return_value = _make_provider()
            result = doc.generate(rows, provider="openai", format="json")
        assert isinstance(result, dict)
        assert result["documentation"] == "# Generated Documentation"
        assert "schema" in result
        assert "samples" in result
        assert result["usage"] == {"total_tokens": 42}

    def test_html_format_wraps_document(self):
        with patch.object(doc, "get_provider") as mock_get:
            mock_get.return_value = _make_provider("# Title\n\nBody")
            result = doc.generate([{"id": 1}], provider="openai", format="html")
        assert isinstance(result, str)
        assert "<!DOCTYPE html>" in result
        assert "Body" in result

    def test_yaml_format_output(self):
        with patch.object(doc, "get_provider") as mock_get:
            mock_get.return_value = _make_provider()
            result = doc.generate([{"id": 1}], provider="openai", format="yaml")
        assert isinstance(result, str)
        assert "documentation" in result

    def test_text_format_strips_headers(self):
        with patch.object(doc, "get_provider") as mock_get:
            mock_get.return_value = _make_provider("# Header\n\nSome **bold** text")
            result = doc.generate([{"id": 1}], provider="openai", format="text")
        assert isinstance(result, str)
        assert "# Header" not in result
        assert "Header" in result


class TestBlocksDelegation:
    def test_blocks_markdown_returns_assembled_document(self):
        fake_result = {"full_document_markdown": "# Blocks Doc", "blocks": {}}
        with patch.object(doc, "generate_blocks", return_value=fake_result) as mock_blocks:
            result = doc.generate([{"id": 1}], blocks=["general"], provider="openai", format="markdown")
        assert result == "# Blocks Doc"
        mock_blocks.assert_called_once()
        assert mock_blocks.call_args.kwargs["blocks"] == ["general"]

    def test_blocks_json_returns_structured_result(self):
        fake_result = {"full_document_markdown": "# Blocks Doc", "blocks": {"general": {}}}
        with patch.object(doc, "generate_blocks", return_value=fake_result):
            result = doc.generate([{"id": 1}], blocks=["general"], provider="openai", format="json")
        assert result is fake_result

    def test_blocks_path_never_touches_provider(self):
        fake_result = {"full_document_markdown": "x", "blocks": {}}
        with (
            patch.object(doc, "generate_blocks", return_value=fake_result),
            patch.object(doc, "get_provider") as mock_get,
        ):
            doc.generate([{"id": 1}], blocks=["general"], provider="openai")
        mock_get.assert_not_called()


class TestCaching:
    def test_cache_hit_skips_provider(self):
        with patch.object(doc, "get_provider") as mock_get:
            mock_get.return_value = _make_provider()
            rows = [{"id": 1}]
            first = doc.generate(rows, provider="openai", cache=True)
            second = doc.generate(rows, provider="openai", cache=True)
        assert first == second == "# Generated Documentation"
        # Provider resolved and invoked only once thanks to the cache hit.
        assert mock_get.call_count == 1

    def test_cache_disabled_by_default(self):
        with patch.object(doc, "get_provider") as mock_get:
            mock_get.return_value = _make_provider()
            rows = [{"id": 1}]
            doc.generate(rows, provider="openai")
            doc.generate(rows, provider="openai")
        assert mock_get.call_count == 2


class TestProviderInteraction:
    def test_import_error_is_wrapped_with_provider_name(self):
        with patch.object(doc, "get_provider", side_effect=ImportError("No module named 'openai'")):
            with pytest.raises(ImportError) as excinfo:
                doc.generate([{"id": 1}], provider="openai")
        assert "openai" in str(excinfo.value)
        assert "pip install" in str(excinfo.value)

    def test_other_provider_errors_propagate(self):
        provider = _make_provider()
        provider.generate.side_effect = RuntimeError("boom")
        with patch.object(doc, "get_provider", return_value=provider):
            with pytest.raises(RuntimeError):
                doc.generate([{"id": 1}], provider="openai")

    def test_extra_kwargs_forwarded_to_provider(self):
        with patch.object(doc, "get_provider") as mock_get:
            provider = _make_provider()
            mock_get.return_value = provider
            doc.generate([{"id": 1}], provider="openai", custom_option="yes")
        assert provider.generate.call_args.kwargs["custom_option"] == "yes"

    def test_doc_params_not_forwarded_to_provider(self):
        """generate()'s own parameters must be filtered out of provider kwargs."""
        with patch.object(doc, "get_provider") as mock_get:
            provider = _make_provider()
            mock_get.return_value = provider
            doc.generate([{"id": 1}], provider="openai", include_schema=True, sample_size=3)
        sent = provider.generate.call_args.kwargs
        for name in ("include_schema", "sample_size", "provider", "format", "language"):
            assert name not in sent

    def test_model_temperature_max_tokens_forwarded(self):
        with patch.object(doc, "get_provider") as mock_get:
            provider = _make_provider()
            mock_get.return_value = provider
            doc.generate([{"id": 1}], provider="openai", model="gpt-x", temperature=0.1, max_tokens=99)
        sent = provider.generate.call_args.kwargs
        assert sent["model"] == "gpt-x"
        assert sent["temperature"] == 0.1
        assert sent["max_tokens"] == 99


class TestContextCollection:
    def test_sample_size_limits_samples(self):
        rows = [{"id": i} for i in range(10)]
        with patch.object(doc, "get_provider") as mock_get:
            provider = _make_provider()
            mock_get.return_value = provider
            doc.generate(rows, provider="openai", sample_size=3, format="json")
        prompt = provider.generate.call_args.kwargs["prompt"]
        assert '"id": 3' not in prompt  # 4th row excluded (0-indexed ids 0..2 kept)
        assert '"id": 2' in prompt

    def test_samples_disabled_means_no_samples_in_json(self):
        with patch.object(doc, "get_provider") as mock_get:
            mock_get.return_value = _make_provider()
            result = doc.generate([{"id": 1}], provider="openai", format="json", include_samples=False)
        assert result["samples"] is None

    def test_schema_in_json_result(self):
        with patch.object(doc, "get_provider") as mock_get:
            mock_get.return_value = _make_provider()
            result = doc.generate([{"id": 1, "name": "x"}], provider="openai", format="json")
        assert "id" in result["schema"]["fields"]
        assert "name" in result["schema"]["fields"]

    def test_schema_failure_is_tolerated(self):
        with (
            patch.object(doc, "get_provider") as mock_get,
            patch.object(doc.schema, "infer", side_effect=RuntimeError("schema boom")),
        ):
            mock_get.return_value = _make_provider()
            result = doc.generate([{"id": 1}], provider="openai", format="json")
        assert result["schema"] is None
        assert result["documentation"] == "# Generated Documentation"

    def test_sample_failure_is_tolerated(self):
        def _broken_iterable():
            raise RuntimeError("read boom")
            yield

        with patch.object(doc, "get_provider") as mock_get:
            mock_get.return_value = _make_provider()
            result = doc.generate(_broken_iterable(), provider="openai")
        assert result == "# Generated Documentation"

    def test_statistics_in_json_result(self):
        with patch.object(doc, "get_provider") as mock_get:
            mock_get.return_value = _make_provider()
            result = doc.generate([{"n": 1}, {"n": 2}], provider="openai", format="json")
        assert result["statistics"]["n"]["count"] == 2

    def test_statistics_disabled(self):
        with patch.object(doc, "get_provider") as mock_get:
            mock_get.return_value = _make_provider()
            result = doc.generate([{"n": 1}], provider="openai", format="json", include_statistics=False)
        assert "statistics" not in result

    def test_list_rows_produce_empty_field_names(self):
        """List-shaped samples cannot yield field names but still generate docs."""
        with patch.object(doc, "get_provider") as mock_get:
            provider = _make_provider()
            mock_get.return_value = provider
            result = doc.generate([[1, 2], [3, 4]], provider="openai", format="json")
        assert result["documentation"] == "# Generated Documentation"

    def test_user_context_in_prompt(self):
        with patch.object(doc, "get_provider") as mock_get:
            provider = _make_provider()
            mock_get.return_value = provider
            doc.generate([{"id": 1}], provider="openai", context={"title": "My Dataset"})
        prompt = provider.generate.call_args.kwargs["prompt"]
        assert "User-provided context" in prompt
        assert "My Dataset" in prompt

    def test_field_descriptions_requested(self):
        with patch.object(doc, "get_provider") as mock_get:
            provider = _make_provider(fields_info={"id": "identifier"})
            mock_get.return_value = provider
            result = doc.generate([{"id": 1}], provider="openai", format="json", include_field_descriptions=True)
        provider.get_fields_info.assert_called_once()
        assert result["field_descriptions"] == {"id": "identifier"}
        prompt = provider.generate.call_args.kwargs["prompt"]
        assert "identifier" in prompt

    def test_field_descriptions_failure_tolerated(self):
        with patch.object(doc, "get_provider") as mock_get:
            provider = _make_provider()
            provider.get_fields_info.side_effect = RuntimeError("fields boom")
            mock_get.return_value = provider
            result = doc.generate([{"id": 1}], provider="openai", include_field_descriptions=True)
        assert result == "# Generated Documentation"


class TestFilePathInputs:
    def test_filename_guidance_in_prompt(self):
        with patch.object(doc, "get_provider") as mock_get:
            provider = _make_provider()
            mock_get.return_value = provider
            doc.generate("fixtures/2cols6rows.csv", provider="openai")
        prompt = provider.generate.call_args.kwargs["prompt"]
        assert "fixtures/2cols6rows.csv" in prompt
        assert "`dataset`" in prompt

    def test_missing_file_path_is_tolerated(self):
        """A non-existent path string fails sampling/schema but still generates."""
        with patch.object(doc, "get_provider") as mock_get:
            mock_get.return_value = _make_provider()
            result = doc.generate("fixtures/does-not-exist-xyz.csv", provider="openai")
        assert result == "# Generated Documentation"

    def test_semantic_types_from_file(self, tmp_path):
        csv_file = tmp_path / "sample.csv"
        csv_file.write_text("id,name\n1,Alice\n")
        with (
            patch.object(doc, "get_provider") as mock_get,
            patch.object(
                doc.semantic, "detect_semantic_types", return_value={"name": [{"type": "person"}]}
            ) as mock_detect,
        ):
            mock_get.return_value = _make_provider()
            result = doc.generate(str(csv_file), provider="openai", format="json", semantic_types=True)
        mock_detect.assert_called_once()
        assert result["semantic_types"] == {"name": [{"type": "person"}]}

    def test_semantic_types_failure_tolerated(self, tmp_path):
        csv_file = tmp_path / "sample.csv"
        csv_file.write_text("id\n1\n")
        with (
            patch.object(doc, "get_provider") as mock_get,
            patch.object(doc.semantic, "detect_semantic_types", side_effect=RuntimeError("sem boom")),
        ):
            mock_get.return_value = _make_provider()
            result = doc.generate(str(csv_file), provider="openai", semantic_types=True)
        assert result == "# Generated Documentation"

    def test_pii_detect_and_mask(self, tmp_path):
        csv_file = tmp_path / "pii.csv"
        csv_file.write_text("name,email\nAlice,alice@example.com\n")
        pii = [{"field": "email", "type": "email"}]
        masked = [{"name": "Alice", "email": "***"}]
        with (
            patch.object(doc, "get_provider") as mock_get,
            patch.object(doc.semantic, "detect_pii", return_value=pii),
            patch.object(doc.semantic, "mask_pii_samples", return_value=masked) as mock_mask,
        ):
            mock_get.return_value = _make_provider()
            result = doc.generate(
                str(csv_file), provider="openai", format="json", pii_detect=True, pii_mask_samples=True
            )
        mock_mask.assert_called_once()
        assert result["pii_fields"] == pii
        assert result["samples"] == masked

    def test_pii_mask_skipped_without_detection(self, tmp_path):
        """pii_mask_samples with no detected PII leaves samples unchanged."""
        csv_file = tmp_path / "pii.csv"
        csv_file.write_text("name\nAlice\n")
        with (
            patch.object(doc, "get_provider") as mock_get,
            patch.object(doc.semantic, "detect_pii", return_value=[]),
            patch.object(doc.semantic, "mask_pii_samples") as mock_mask,
            patch.object(doc, "redact_for_llm") as mock_redact,
        ):
            mock_get.return_value = _make_provider()
            result = doc.generate(str(csv_file), provider="openai", format="json", pii_mask_samples=True)
        mock_mask.assert_not_called()
        mock_redact.assert_not_called()
        assert result["samples"] == [{"name": "Alice"}]


class TestCloudRedactionHeuristic:
    def test_cloud_provider_samples_redacted(self):
        with (
            patch.object(doc, "get_provider") as mock_get,
            patch.object(doc, "redact_for_llm", return_value=[{"id": "REDACTED"}]) as mock_redact,
        ):
            mock_get.return_value = _make_provider()
            result = doc.generate([{"id": 1}], provider="openai", format="json")
        mock_redact.assert_called_once()
        assert result["samples"] == [{"id": "REDACTED"}]

    def test_local_provider_samples_not_redacted(self):
        with (
            patch.object(doc, "get_provider") as mock_get,
            patch.object(doc, "redact_for_llm") as mock_redact,
        ):
            mock_get.return_value = _make_provider()
            result = doc.generate([{"id": 1}], provider="ollama", format="json")
        mock_redact.assert_not_called()
        assert result["samples"] == [{"id": 1}]

    def test_redaction_skipped_when_masking_enabled(self, tmp_path):
        """Metacrafter masking takes precedence over heuristic redaction."""
        csv_file = tmp_path / "pii.csv"
        csv_file.write_text("name\nAlice\n")
        with (
            patch.object(doc, "get_provider") as mock_get,
            patch.object(doc.semantic, "detect_pii", return_value=[{"field": "name"}]),
            patch.object(doc.semantic, "mask_pii_samples", return_value=[{"name": "***"}]),
            patch.object(doc, "redact_for_llm") as mock_redact,
        ):
            mock_get.return_value = _make_provider()
            doc.generate(str(csv_file), provider="openai", pii_detect=True, pii_mask_samples=True)
        mock_redact.assert_not_called()


class TestValidation:
    def test_validate_output_json_valid(self):
        with patch.object(doc, "get_provider") as mock_get:
            mock_get.return_value = _make_provider()
            result = doc.generate([{"id": 1}], provider="openai", format="json", validate_output=True)
        assert result["documentation"] == "# Generated Documentation"

    def test_validate_output_failure_only_warns(self):
        with (
            patch.object(doc, "get_provider") as mock_get,
            # patch.object, not a dotted string: ``iterable.ai`` is rebound to the
            # ``doc`` module in ``iterable/__init__.py``, which Python 3.10's
            # attribute-walking ``mock.patch`` target lookup trips over.
            patch.object(models, "validate_documentation_result", side_effect=ValueError("bad doc")),
        ):
            mock_get.return_value = _make_provider()
            result = doc.generate([{"id": 1}], provider="openai", format="json", validate_output=True)
        assert result["documentation"] == "# Generated Documentation"

    def test_validate_output_ignored_for_markdown(self):
        with (
            patch.object(doc, "get_provider") as mock_get,
            patch.object(models, "validate_documentation_result") as mock_validate,
        ):
            mock_get.return_value = _make_provider()
            doc.generate([{"id": 1}], provider="openai", format="markdown", validate_output=True)
        mock_validate.assert_not_called()
