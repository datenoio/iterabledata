"""Tests for native LLM providers (Anthropic, Gemini, Azure)."""

from unittest.mock import MagicMock, patch

import pytest

from iterable.ai import providers as providers_mod
from iterable.ai.providers import get_provider


@pytest.mark.ai
class TestNativeProviders:
    def test_get_anthropic_provider(self):
        with patch.object(providers_mod, "AnthropicProvider") as mock_cls:
            mock_cls.return_value = MagicMock()
            get_provider("anthropic", api_key="test-key")
            mock_cls.assert_called_once_with(api_key="test-key")

    def test_get_gemini_provider(self):
        with patch.object(providers_mod, "GeminiProvider") as mock_cls:
            mock_cls.return_value = MagicMock()
            get_provider("gemini", api_key="test-key")
            mock_cls.assert_called_once_with(api_key="test-key")

    def test_get_azure_provider(self):
        with patch.object(providers_mod, "AzureOpenAIProvider") as mock_cls:
            mock_cls.return_value = MagicMock()
            get_provider("azure", api_key="test-key")
            mock_cls.assert_called_once_with(api_key="test-key", base_url=None)

    def test_anthropic_import_error(self):
        with patch.dict("sys.modules", {"anthropic": None}):
            with pytest.raises(ImportError, match="Anthropic"):
                from iterable.ai.providers import AnthropicProvider

                AnthropicProvider(api_key="x")

    def test_anthropic_generate_mocked(self):
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.content = [MagicMock(type="text", text="Generated doc")]
        mock_response.usage = MagicMock(input_tokens=10, output_tokens=5)
        mock_client.messages.create.return_value = mock_response

        mock_anthropic_cls = MagicMock(return_value=mock_client)
        mock_anthropic_module = MagicMock(Anthropic=mock_anthropic_cls)

        with patch.dict("sys.modules", {"anthropic": mock_anthropic_module}):
            from iterable.ai.providers import AnthropicProvider

            provider = AnthropicProvider(api_key="test")
            text = provider.generate("prompt", model="claude-3-5-sonnet-20241022")
            assert "Generated" in text
