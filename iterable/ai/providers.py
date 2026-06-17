"""
LLM provider abstraction layer.

Provides unified interface for different LLM providers.
"""

from __future__ import annotations

import json
import os
import re
from abc import ABC, abstractmethod
from typing import Any

from .utils import retry_with_backoff


def _env_api_key(*names: str) -> str | None:
    for name in names:
        value = os.environ.get(name)
        if value:
            return value
    return None


def _fields_info_prompt(fields: list[str], language: str) -> str:
    fields_str = ", ".join(fields)
    return (
        f"Please describe these data fields in {language}: {fields_str}. "
        f"Provide a description for each field explaining what it represents. "
        f"Return your response as a JSON object with field names as keys and descriptions as values."
    )


def _parse_fields_json(content: str, fields: list[str]) -> dict[str, str]:
    try:
        result = json.loads(content)
        return {field: result.get(field, f"Field: {field}") for field in fields}
    except Exception:
        json_match = re.search(r"\{.*\}", content, re.DOTALL)
        if json_match:
            try:
                parsed = json.loads(json_match.group(0))
                return {field: parsed.get(field, f"Field: {field}") for field in fields}
            except Exception:
                pass
    return {field: f"Field: {field}" for field in fields}


class LLMProvider(ABC):
    """Base class for LLM providers."""

    @abstractmethod
    def generate(
        self,
        prompt: str,
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int | None = None,
        **kwargs: Any,
    ) -> str:
        """
        Generate text using the LLM provider.

        Args:
            prompt: Input prompt
            model: Model name (provider-specific)
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            **kwargs: Provider-specific options

        Returns:
            Generated text
        """
        pass

    @abstractmethod
    def get_usage_info(self) -> dict[str, Any] | None:
        """
        Get token usage information if available.

        Returns:
            Dictionary with usage info (tokens, cost, etc.) or None
        """
        pass

    @abstractmethod
    def get_fields_info(
        self,
        fields: list[str],
        language: str = "English",
    ) -> dict[str, str]:
        """
        Get descriptions for a list of field names.

        Args:
            fields: List of field names to describe
            language: Language for descriptions (default: "English")

        Returns:
            Dictionary mapping field names to their descriptions
        """
        pass


class OpenAIProvider(LLMProvider):
    """OpenAI provider implementation."""

    def __init__(self, api_key: str | None = None, base_url: str | None = None):
        try:
            from openai import OpenAI
        except ImportError as err:
            raise ImportError("OpenAI is required. Install with: pip install openai") from err

        self.client = OpenAI(api_key=api_key, base_url=base_url)
        self._usage_info: dict[str, Any] | None = None
        self._default_model = "gpt-4o-mini"

    def generate(
        self,
        prompt: str,
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int | None = None,
        **kwargs: Any,
    ) -> str:
        model = model or self._default_model
        response = self.client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs,
        )
        self._usage_info = {
            "prompt_tokens": response.usage.prompt_tokens if response.usage else None,
            "completion_tokens": response.usage.completion_tokens if response.usage else None,
            "total_tokens": response.usage.total_tokens if response.usage else None,
        }
        return response.choices[0].message.content

    def get_usage_info(self) -> dict[str, Any] | None:
        return self._usage_info

    def get_fields_info(
        self,
        fields: list[str],
        language: str = "English",
    ) -> dict[str, str]:
        """Get field descriptions using OpenAI API."""
        fields_str = ", ".join(fields)
        prompt = (
            f"Please describe these data fields in {language}: {fields_str}. "
            f"Provide a description for each field explaining what it represents. "
            f"Return your response as a JSON object with field names as keys and descriptions as values."
        )

        def _make_request():
            return self.client.chat.completions.create(
                model=self._default_model,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            f"You are a data documentation assistant. "
                            f"Provide clear, concise descriptions of data "
                            f"fields in {language}. Always respond with valid JSON."
                        ),
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.3,
                response_format={"type": "json_object"},
            )

        try:
            response = retry_with_backoff(_make_request)
            content = response.choices[0].message.content
            result = json.loads(content)
            # Ensure all fields are included
            field_descriptions = {}
            for field in fields:
                field_descriptions[field] = result.get(field, f"Field: {field}")
            return field_descriptions
        except Exception:
            # Fallback: return basic descriptions
            return {field: f"Field: {field}" for field in fields}


class OpenRouterProvider(LLMProvider):
    """OpenRouter provider implementation."""

    def __init__(self, api_key: str | None = None):
        try:
            from openai import OpenAI
        except ImportError as err:
            raise ImportError("OpenAI client is required for OpenRouter. Install with: pip install openai") from err

        self.client = OpenAI(
            api_key=api_key,
            base_url="https://openrouter.ai/api/v1",
        )
        self._usage_info: dict[str, Any] | None = None
        self._default_model = "openai/gpt-4o-mini"

    def generate(
        self,
        prompt: str,
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int | None = None,
        **kwargs: Any,
    ) -> str:
        model = model or self._default_model
        response = self.client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs,
        )
        self._usage_info = {
            "prompt_tokens": response.usage.prompt_tokens if response.usage else None,
            "completion_tokens": response.usage.completion_tokens if response.usage else None,
            "total_tokens": response.usage.total_tokens if response.usage else None,
        }
        return response.choices[0].message.content

    def get_usage_info(self) -> dict[str, Any] | None:
        return self._usage_info

    def get_fields_info(
        self,
        fields: list[str],
        language: str = "English",
    ) -> dict[str, str]:
        """Get field descriptions using OpenRouter API."""
        fields_str = ", ".join(fields)
        prompt = (
            f"Please describe these data fields in {language}: {fields_str}. "
            f"Provide a description for each field explaining what it represents. "
            f"Return your response as a JSON object with field names as keys and descriptions as values."
        )

        def _make_request():
            return self.client.chat.completions.create(
                model=self._default_model,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            f"You are a data documentation assistant. "
                            f"Provide clear, concise descriptions of data "
                            f"fields in {language}. Always respond with valid JSON."
                        ),
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.3,
                response_format={"type": "json_object"},
            )

        try:
            response = retry_with_backoff(_make_request)
            content = response.choices[0].message.content
            result = json.loads(content)
            field_descriptions = {}
            for field in fields:
                field_descriptions[field] = result.get(field, f"Field: {field}")
            return field_descriptions
        except Exception:
            return {field: f"Field: {field}" for field in fields}


class OllamaProvider(LLMProvider):
    """Ollama provider implementation (local)."""

    def __init__(self, base_url: str = "http://localhost:11434"):
        import importlib.util

        if importlib.util.find_spec("requests") is None:
            raise ImportError("requests is required for Ollama. Install with: pip install requests")

        self.base_url = base_url
        self._usage_info: dict[str, Any] | None = None
        self._default_model = "llama2"

    def generate(
        self,
        prompt: str,
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int | None = None,
        **kwargs: Any,
    ) -> str:
        import requests

        model = model or self._default_model
        response = requests.post(
            f"{self.base_url}/api/generate",
            json={
                "model": model,
                "prompt": prompt,
                "options": {
                    "temperature": temperature,
                    "num_predict": max_tokens,
                },
                **kwargs,
            },
            timeout=300,
        )
        response.raise_for_status()
        result = response.json()
        self._usage_info = {
            "prompt_tokens": result.get("prompt_eval_count"),
            "completion_tokens": result.get("eval_count"),
            "total_tokens": result.get("prompt_eval_count", 0) + result.get("eval_count", 0),
        }
        return result.get("response", "")

    def get_usage_info(self) -> dict[str, Any] | None:
        return self._usage_info

    def get_fields_info(
        self,
        fields: list[str],
        language: str = "English",
    ) -> dict[str, str]:
        """Get field descriptions using Ollama API."""
        import requests

        fields_str = ", ".join(fields)
        prompt = (
            f"Please describe these data fields in {language}: {fields_str}. "
            f"Provide a description for each field explaining what it represents. "
            f"Return your response as a JSON object with field names as keys and descriptions as values."
        )

        def _make_request():
            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self._default_model,
                    "prompt": prompt,
                    "options": {"temperature": 0.3},
                },
                timeout=300,
            )
            response.raise_for_status()
            return response

        try:
            response = retry_with_backoff(_make_request)
            result = response.json()
            content = result.get("response", "")
            # Try to extract JSON from response
            json_match = re.search(r"\{.*\}", content, re.DOTALL)
            if json_match:
                parsed = json.loads(json_match.group(0))
                field_descriptions = {}
                for field in fields:
                    field_descriptions[field] = parsed.get(field, f"Field: {field}")
                return field_descriptions
            # Fallback if JSON parsing fails
            return {field: f"Field: {field}" for field in fields}
        except Exception:
            return {field: f"Field: {field}" for field in fields}


class LMStudioProvider(LLMProvider):
    """LMStudio provider implementation (local)."""

    def __init__(self, base_url: str = "http://localhost:1234/v1"):
        try:
            from openai import OpenAI
        except ImportError as err:
            raise ImportError("OpenAI client is required for LMStudio. Install with: pip install openai") from err

        self.client = OpenAI(base_url=base_url, api_key="not-needed")
        self._usage_info: dict[str, Any] | None = None
        self._default_model = "local-model"

    def generate(
        self,
        prompt: str,
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int | None = None,
        **kwargs: Any,
    ) -> str:
        # LMStudio uses OpenAI-compatible API
        response = self.client.chat.completions.create(
            model=model or self._default_model,
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs,
        )
        self._usage_info = {
            "prompt_tokens": response.usage.prompt_tokens if response.usage else None,
            "completion_tokens": response.usage.completion_tokens if response.usage else None,
            "total_tokens": response.usage.total_tokens if response.usage else None,
        }
        return response.choices[0].message.content

    def get_usage_info(self) -> dict[str, Any] | None:
        return self._usage_info

    def get_fields_info(
        self,
        fields: list[str],
        language: str = "English",
    ) -> dict[str, str]:
        """Get field descriptions using LMStudio API."""
        fields_str = ", ".join(fields)
        prompt = (
            f"Please describe these data fields in {language}: {fields_str}. "
            f"Provide a description for each field explaining what it represents. "
            f"Return your response as a JSON object with field names as keys and descriptions as values."
        )

        def _make_request():
            return self.client.chat.completions.create(
                model=self._default_model,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            f"You are a data documentation assistant. "
                            f"Provide clear, concise descriptions of data "
                            f"fields in {language}. Always respond with valid JSON."
                        ),
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.3,
                response_format={"type": "json_object"},
            )

        try:
            response = retry_with_backoff(_make_request)
            content = response.choices[0].message.content
            result = json.loads(content)
            field_descriptions = {}
            for field in fields:
                field_descriptions[field] = result.get(field, f"Field: {field}")
            return field_descriptions
        except Exception:
            return {field: f"Field: {field}" for field in fields}


class PerplexityProvider(LLMProvider):
    """Perplexity provider implementation."""

    def __init__(self, api_key: str | None = None):
        try:
            from openai import OpenAI
        except ImportError as err:
            raise ImportError("OpenAI client is required for Perplexity. Install with: pip install openai") from err

        self.client = OpenAI(
            api_key=api_key,
            base_url="https://api.perplexity.ai/v2",
        )
        self._usage_info: dict[str, Any] | None = None
        self._default_model = "sonar-pro"

    def generate(
        self,
        prompt: str,
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int | None = None,
        **kwargs: Any,
    ) -> str:
        model = model or self._default_model
        response = self.client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs,
        )
        self._usage_info = {
            "prompt_tokens": response.usage.prompt_tokens if response.usage else None,
            "completion_tokens": response.usage.completion_tokens if response.usage else None,
            "total_tokens": response.usage.total_tokens if response.usage else None,
        }
        return response.choices[0].message.content

    def get_usage_info(self) -> dict[str, Any] | None:
        return self._usage_info

    def get_fields_info(
        self,
        fields: list[str],
        language: str = "English",
    ) -> dict[str, str]:
        """Get field descriptions using Perplexity API."""
        fields_str = ", ".join(fields)
        prompt = (
            f"Please describe these data fields in {language}: {fields_str}. "
            f"Provide a description for each field explaining what it represents. "
            f"Return your response as a JSON object with field names as keys and descriptions as values."
        )

        def _make_request():
            return self.client.chat.completions.create(
                model=self._default_model,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            f"You are a data documentation assistant. "
                            f"Provide clear, concise descriptions of data "
                            f"fields in {language}. Always respond with valid JSON."
                        ),
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.3,
                response_format={"type": "json_object"},
            )

        try:
            response = retry_with_backoff(_make_request)
            content = response.choices[0].message.content
            result = json.loads(content)
            field_descriptions = {}
            for field in fields:
                field_descriptions[field] = result.get(field, f"Field: {field}")
            return field_descriptions
        except Exception:
            return {field: f"Field: {field}" for field in fields}


class AnthropicProvider(LLMProvider):
    """Anthropic Claude provider implementation."""

    def __init__(self, api_key: str | None = None):
        try:
            from anthropic import Anthropic
        except ImportError as err:
            raise ImportError("Anthropic is required. Install with: pip install iterabledata[anthropic]") from err

        resolved_key = api_key or _env_api_key("ANTHROPIC_API_KEY")
        self.client = Anthropic(api_key=resolved_key)
        self._usage_info: dict[str, Any] | None = None
        self._default_model = "claude-3-5-haiku-latest"

    def generate(
        self,
        prompt: str,
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int | None = None,
        **kwargs: Any,
    ) -> str:
        model = model or self._default_model
        response = self.client.messages.create(
            model=model,
            max_tokens=max_tokens or 4096,
            temperature=temperature,
            messages=[{"role": "user", "content": prompt}],
            **kwargs,
        )
        self._usage_info = {
            "prompt_tokens": response.usage.input_tokens if response.usage else None,
            "completion_tokens": response.usage.output_tokens if response.usage else None,
            "total_tokens": (
                (response.usage.input_tokens or 0) + (response.usage.output_tokens or 0) if response.usage else None
            ),
        }
        text_blocks = [block.text for block in response.content if getattr(block, "type", None) == "text"]
        return "".join(text_blocks) if text_blocks else str(response.content[0])

    def get_usage_info(self) -> dict[str, Any] | None:
        return self._usage_info

    def get_fields_info(self, fields: list[str], language: str = "English") -> dict[str, str]:
        prompt = _fields_info_prompt(fields, language)

        def _make_request():
            return self.client.messages.create(
                model=self._default_model,
                max_tokens=2048,
                temperature=0.3,
                system=(
                    f"You are a data documentation assistant. Provide clear, concise field descriptions "
                    f"in {language}. Always respond with valid JSON only."
                ),
                messages=[{"role": "user", "content": prompt}],
            )

        try:
            response = retry_with_backoff(_make_request)
            text_blocks = [block.text for block in response.content if getattr(block, "type", None) == "text"]
            content = "".join(text_blocks)
            return _parse_fields_json(content, fields)
        except Exception:
            return {field: f"Field: {field}" for field in fields}


class GeminiProvider(LLMProvider):
    """Google Gemini provider implementation."""

    def __init__(self, api_key: str | None = None):
        try:
            from google import genai
        except ImportError as err:
            raise ImportError("google-genai is required. Install with: pip install iterabledata[google-genai]") from err

        resolved_key = api_key or _env_api_key("GOOGLE_API_KEY", "GEMINI_API_KEY")
        self._client_module = genai
        self.client = genai.Client(api_key=resolved_key)
        self._usage_info: dict[str, Any] | None = None
        self._default_model = "gemini-2.0-flash"

    def generate(
        self,
        prompt: str,
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int | None = None,
        **kwargs: Any,
    ) -> str:
        model = model or self._default_model
        config: dict[str, Any] = {"temperature": temperature}
        if max_tokens is not None:
            config["max_output_tokens"] = max_tokens
        config.update(kwargs)
        response = self.client.models.generate_content(model=model, contents=prompt, config=config)
        self._usage_info = None
        usage = getattr(response, "usage_metadata", None)
        if usage is not None:
            prompt_tokens = getattr(usage, "prompt_token_count", None)
            completion_tokens = getattr(usage, "candidates_token_count", None)
            self._usage_info = {
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "total_tokens": (prompt_tokens or 0) + (completion_tokens or 0),
            }
        return response.text or ""

    def get_usage_info(self) -> dict[str, Any] | None:
        return self._usage_info

    def get_fields_info(self, fields: list[str], language: str = "English") -> dict[str, str]:
        prompt = _fields_info_prompt(fields, language)
        try:
            response = self.client.models.generate_content(
                model=self._default_model,
                contents=(f"You are a data documentation assistant. Respond with valid JSON only.\n\n{prompt}"),
                config={"temperature": 0.3},
            )
            return _parse_fields_json(response.text or "", fields)
        except Exception:
            return {field: f"Field: {field}" for field in fields}


class AzureOpenAIProvider(LLMProvider):
    """Azure OpenAI provider implementation."""

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        api_version: str | None = None,
        azure_deployment: str | None = None,
    ):
        try:
            from openai import AzureOpenAI
        except ImportError as err:
            raise ImportError("OpenAI is required for Azure. Install with: pip install openai") from err

        resolved_key = api_key or _env_api_key("AZURE_OPENAI_API_KEY")
        endpoint = base_url or os.environ.get("AZURE_OPENAI_ENDPOINT")
        version = api_version or os.environ.get("AZURE_OPENAI_API_VERSION", "2024-02-15-preview")
        self.client = AzureOpenAI(api_key=resolved_key, azure_endpoint=endpoint, api_version=version)
        self._usage_info: dict[str, Any] | None = None
        self._default_model = azure_deployment or os.environ.get("AZURE_OPENAI_DEPLOYMENT", "gpt-4o-mini")

    def generate(
        self,
        prompt: str,
        model: str | None = None,
        temperature: float = 0.7,
        max_tokens: int | None = None,
        **kwargs: Any,
    ) -> str:
        model = model or self._default_model
        response = self.client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs,
        )
        self._usage_info = {
            "prompt_tokens": response.usage.prompt_tokens if response.usage else None,
            "completion_tokens": response.usage.completion_tokens if response.usage else None,
            "total_tokens": response.usage.total_tokens if response.usage else None,
        }
        return response.choices[0].message.content or ""

    def get_usage_info(self) -> dict[str, Any] | None:
        return self._usage_info

    def get_fields_info(self, fields: list[str], language: str = "English") -> dict[str, str]:
        prompt = _fields_info_prompt(fields, language)

        def _make_request():
            return self.client.chat.completions.create(
                model=self._default_model,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            f"You are a data documentation assistant. Provide clear, concise descriptions "
                            f"in {language}. Always respond with valid JSON."
                        ),
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.3,
                response_format={"type": "json_object"},
            )

        try:
            response = retry_with_backoff(_make_request)
            content = response.choices[0].message.content or ""
            return _parse_fields_json(content, fields)
        except Exception:
            return {field: f"Field: {field}" for field in fields}


def get_provider(
    provider: str,
    api_key: str | None = None,
    base_url: str | None = None,
) -> LLMProvider:
    """
    Get LLM provider instance.

    Args:
        provider: Provider name - "openai", "anthropic", "gemini", "azure", "openrouter",
            "ollama", "lmstudio", "perplexity"
        api_key: API key (if required; falls back to provider env vars)
        base_url: Base URL (for local providers or Azure endpoint override)

    Returns:
        LLMProvider instance
    """
    provider = provider.lower()
    if provider == "openai":
        return OpenAIProvider(api_key=api_key or _env_api_key("OPENAI_API_KEY"), base_url=base_url)
    elif provider == "anthropic":
        return AnthropicProvider(api_key=api_key)
    elif provider in ("gemini", "google"):
        return GeminiProvider(api_key=api_key)
    elif provider == "azure":
        return AzureOpenAIProvider(api_key=api_key, base_url=base_url)
    elif provider == "openrouter":
        return OpenRouterProvider(api_key=api_key or _env_api_key("OPENROUTER_API_KEY"))
    elif provider == "ollama":
        return OllamaProvider(base_url=base_url or "http://localhost:11434")
    elif provider == "lmstudio":
        return LMStudioProvider(base_url=base_url or "http://localhost:1234/v1")
    elif provider == "perplexity":
        return PerplexityProvider(api_key=api_key or _env_api_key("PERPLEXITY_API_KEY"))
    else:
        raise ValueError(f"Unknown provider: {provider}")
