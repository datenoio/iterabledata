"""Optional live LLM integration tests (skipped without API keys)."""

from __future__ import annotations

import os

import pytest

from iterable.ai import doc


@pytest.mark.integration
@pytest.mark.ai
def test_openai_doc_generate_live():
    if not os.environ.get("OPENAI_API_KEY"):
        pytest.skip("OPENAI_API_KEY not set")
    result = doc.generate(
        "fixtures/2cols6rows.csv",
        provider="openai",
        model="gpt-4o-mini",
        format="markdown",
        include_schema=False,
        include_statistics=False,
        sample_size=2,
    )
    assert isinstance(result, str)
    assert len(result) > 20


@pytest.mark.integration
@pytest.mark.ai
def test_anthropic_doc_generate_live():
    if not os.environ.get("ANTHROPIC_API_KEY"):
        pytest.skip("ANTHROPIC_API_KEY not set")
    pytest.importorskip("anthropic")
    result = doc.generate(
        "fixtures/2cols6rows.csv",
        provider="anthropic",
        format="markdown",
        include_schema=False,
        include_statistics=False,
        sample_size=2,
    )
    assert isinstance(result, str)
