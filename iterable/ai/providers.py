"""
LLM provider abstraction layer.

Provides unified interface for different LLM providers.
"""

from __future__ import annotations

import json
import re
from abc import ABC, abstractmethod
from typing import Any

from .utils import retry_with_backoff


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


def get_provider(
    provider: str,
    api_key: str | None = None,
    base_url: str | None = None,
) -> LLMProvider:
    """
    Get LLM provider instance.

    Args:
        provider: Provider name - "openai", "openrouter", "ollama", "lmstudio", "perplexity"
        api_key: API key (if required)
        base_url: Base URL (for local providers)

    Returns:
        LLMProvider instance
    """
    if provider == "openai":
        return OpenAIProvider(api_key=api_key, base_url=base_url)
    elif provider == "openrouter":
        return OpenRouterProvider(api_key=api_key)
    elif provider == "ollama":
        return OllamaProvider(base_url=base_url or "http://localhost:11434")
    elif provider == "lmstudio":
        return LMStudioProvider(base_url=base_url or "http://localhost:1234/v1")
    elif provider == "perplexity":
        return PerplexityProvider(api_key=api_key)
    else:
        raise ValueError(f"Unknown provider: {provider}")
