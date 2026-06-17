"""Tests for iterable.ai.context utilities."""

from __future__ import annotations

from iterable.ai.context import redact_for_llm, sample_for_llm


class TestSampleForLLM:
    def test_head_sample(self):
        rows = [{"a": i} for i in range(20)]
        sample = sample_for_llm(rows, max_rows=5, strategy="head")
        assert len(sample) == 5
        assert sample[0]["a"] == 0

    def test_stratified_sample(self):
        rows = [{"a": i} for i in range(100)]
        sample = sample_for_llm(rows, max_rows=10, strategy="stratified")
        assert len(sample) == 10

    def test_char_budget(self):
        rows = [{"data": "x" * 1000} for _ in range(10)]
        sample = sample_for_llm(rows, max_rows=10, max_tokens=50, strategy="head")
        assert len(sample) < 10

    def test_sample_from_file(self):
        sample = sample_for_llm("fixtures/2cols6rows.csv", max_rows=3)
        assert len(sample) == 3

    def test_empty_max_rows(self):
        assert sample_for_llm([{"a": 1}], max_rows=0) == []


class TestRedactForLLM:
    def test_redact_email_column(self):
        rows = [{"email": "user@example.com", "id": 1}]
        redacted = redact_for_llm(rows)
        assert redacted[0]["email"] == "***"
        assert redacted[0]["id"] == 1

    def test_redact_explicit_fields(self):
        rows = [{"custom": "secret", "id": 1}]
        redacted = redact_for_llm(rows, pii_fields=["custom"])
        assert redacted[0]["custom"] == "***"

    def test_redact_preserves_non_dict_rows(self):
        rows = ["plain"]
        assert redact_for_llm(rows) == ["plain"]
