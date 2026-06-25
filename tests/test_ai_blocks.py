"""Tests for block-based AI documentation generation and supporting modules."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from iterable.ai import doc, fileinfo, sampling
from iterable.ai.models import block_json_schema, block_model_for
from iterable.ai.progress import ProgressReporter, Stage, StageTimer
from iterable.ops import stats

CSV_FIXTURE = "fixtures/2cols6rows.csv"


class FakeProvider:
    """Provider supporting structured output, used to avoid live API calls."""

    def __init__(self):
        self.calls: list[str] = []

    def generate(self, prompt, model=None, temperature=0.7, max_tokens=None, **kwargs):
        return "# Generated text"

    def get_usage_info(self):
        return {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15}

    def get_fields_info(self, fields, language="English"):
        return {f: f"desc {f}" for f in fields}

    def generate_structured(
        self, prompt, json_schema, model=None, temperature=0.2, max_tokens=None, schema_name="result", **kwargs
    ):
        self.calls.append(schema_name)
        if "general" in schema_name:
            return {"title": "Mock DS", "description": "A mock dataset", "topic": "testing"}
        if "schema" in schema_name:
            return {"fields": [{"name": "col1", "type": "string", "description": "first", "nullable": False}]}
        if "quality" in schema_name:
            return {"overall": "High", "rationale": "looks fine", "observations": []}
        if "examples" in schema_name:
            return {"examples": [{"tool": "DuckDB", "language": "sql", "code": "SELECT 1", "description": "q"}]}
        if "codebook" in schema_name:
            return {"entries": []}
        return {}


@pytest.fixture
def fake_provider():
    return FakeProvider()


# ---------------------------------------------------------------------------
# Sampling
# ---------------------------------------------------------------------------


class TestSampling:
    def test_small_tier(self):
        plan = sampling.choose_plan(500)
        assert plan.tier == "small"
        assert plan.include_rows is True
        assert plan.random_rows == 0

    def test_medium_tier(self):
        plan = sampling.choose_plan(5 * 1024 * 1024)
        assert plan.tier == "medium"
        assert plan.head_rows > 0
        assert plan.random_rows > 0

    def test_large_tier_no_rows(self):
        plan = sampling.choose_plan(50 * 1024 * 1024)
        assert plan.tier == "large"
        assert plan.include_rows is False

    def test_max_rows_env(self, monkeypatch):
        monkeypatch.setenv("MAX_ROWS_SAMPLING", "7")
        assert sampling.default_max_rows() == 7
        plan = sampling.choose_plan(100)
        assert plan.head_rows == 7

    def test_sample_rows_head(self):
        rows = [{"i": i} for i in range(100)]
        plan = sampling.choose_plan(100, max_rows=5)
        sampled = sampling.sample_rows(rows, plan)
        assert sampled == rows[:5]

    def test_sample_rows_large_returns_empty(self):
        rows = [{"i": i} for i in range(10)]
        plan = sampling.choose_plan(50 * 1024 * 1024)
        assert sampling.sample_rows(rows, plan) == []

    def test_sample_rows_medium_includes_random(self):
        rows = [{"i": i} for i in range(1000)]
        plan = sampling.choose_plan(5 * 1024 * 1024, max_rows=10)
        sampled = sampling.sample_rows(rows, plan, seed=42)
        assert len(sampled) == plan.head_rows + plan.random_rows
        assert sampled[: plan.head_rows] == rows[: plan.head_rows]


# ---------------------------------------------------------------------------
# Stats enrichment
# ---------------------------------------------------------------------------


class TestStatsEnrichment:
    def test_null_fraction_and_dictionary(self):
        rows = [{"cat": "a"}, {"cat": "a"}, {"cat": "b"}, {"cat": None}]
        result = stats.compute(rows, include_top_values=True, dict_threshold=0.9)
        s = result["cat"]
        assert s["null_count"] == 1
        assert abs(s["null_fraction"] - 0.25) < 1e-9
        assert s["is_dictionary"] is True
        assert "top_values" in s
        top = {entry["value"]: entry["count"] for entry in s["top_values"]}
        assert top["a"] == 2

    def test_not_dictionary_when_high_cardinality(self):
        rows = [{"id": i} for i in range(20)]
        result = stats.compute(rows, dict_threshold=0.1)
        assert result["id"]["is_dictionary"] is False

    def test_dict_threshold_env(self, monkeypatch):
        monkeypatch.setenv("DICT_THRESHOLD", "0.5")
        assert stats.default_dict_threshold() == 0.5


# ---------------------------------------------------------------------------
# File metadata
# ---------------------------------------------------------------------------


class TestFileInfo:
    def test_file_metadata(self):
        meta = fileinfo.file_metadata(CSV_FIXTURE)
        assert meta["file_name"] == "2cols6rows.csv"
        assert meta["format"] == "csv"
        assert meta["file_size"] > 0
        assert meta["file_hash"] and len(meta["file_hash"]) == 64

    def test_detect_format_with_codec(self):
        assert fileinfo.detect_format("data.csv.gz") == "csv"
        assert fileinfo.detect_format("data.parquet") == "parquet"

    def test_count_records(self):
        assert fileinfo.count_records(CSV_FIXTURE) == 6


# ---------------------------------------------------------------------------
# Progress
# ---------------------------------------------------------------------------


class TestProgress:
    def test_reporter_emits_events(self):
        events = []
        reporter = ProgressReporter(events.append)
        reporter.emit(Stage.PARSING, 10, "x")
        assert events[0].stage == Stage.PARSING
        assert events[0].progress == 10
        assert events[0].job_id == reporter.job_id

    def test_callback_errors_swallowed(self):
        def bad(_event):
            raise RuntimeError("boom")

        reporter = ProgressReporter(bad)
        # Should not raise.
        reporter.emit(Stage.PARSING, 10)

    def test_stage_timer_reports_failure(self):
        events = []
        reporter = ProgressReporter(events.append)
        with pytest.raises(ValueError):
            with StageTimer(reporter, Stage.PARSING):
                raise ValueError("x")
        assert any(e.stage == Stage.FAILED for e in events)


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------


class TestBlockModels:
    def test_block_schema_available(self):
        for name in ("general", "schema", "quality", "examples", "codebook"):
            assert block_json_schema(name) is not None
            assert block_model_for(name) is not None

    def test_statistics_has_no_llm_schema(self):
        # statistics is computed, not LLM-modeled.
        assert block_json_schema("statistics") is None


# ---------------------------------------------------------------------------
# generate_blocks
# ---------------------------------------------------------------------------


class TestGenerateBlocks:
    def test_default_blocks(self, fake_provider):
        with patch("iterable.ai.doc.get_provider", return_value=fake_provider):
            result = doc.generate_blocks(CSV_FIXTURE)
        assert set(["general", "schema", "quality", "examples", "statistics"]).issubset(result["blocks"].keys())
        assert "full_document_markdown" in result
        assert result["source"]["format"] == "csv"
        assert result["source"]["sha256"]

    def test_block_structure(self, fake_provider):
        with patch("iterable.ai.doc.get_provider", return_value=fake_provider):
            result = doc.generate_blocks(CSV_FIXTURE, blocks=["general", "schema"])
        for name in ("general", "schema"):
            assert "markdown" in result["blocks"][name]
            assert "data" in result["blocks"][name]

    def test_unknown_block_raises(self):
        with pytest.raises(ValueError):
            doc.generate_blocks(CSV_FIXTURE, blocks=["does_not_exist"])

    def test_deferred_block(self, fake_provider):
        with patch("iterable.ai.doc.get_provider", return_value=fake_provider):
            result = doc.generate_blocks(CSV_FIXTURE, blocks=["geo_coverage", "lineage"])
        assert result["blocks"]["geo_coverage"]["data"]["status"] == "not_implemented"
        assert result["blocks"]["lineage"]["data"]["status"] == "not_implemented"

    def test_statistics_block_no_llm(self):
        # statistics-only generation must not require a provider.
        with patch("iterable.ai.doc.get_provider", side_effect=AssertionError("should not be called")):
            result = doc.generate_blocks(CSV_FIXTURE, blocks=["statistics"])
        assert "statistics" in result["blocks"]
        assert result["blocks"]["statistics"]["data"]["fields"]

    def test_context_threaded(self, fake_provider):
        ctx = {"title": "Population", "territory": "Russia", "tags": ["demography"]}
        with patch("iterable.ai.doc.get_provider", return_value=fake_provider):
            result = doc.generate_blocks(CSV_FIXTURE, blocks=["general"], context=ctx)
        data = result["blocks"]["general"]["data"]
        assert data["title"] == "Population"
        assert data["territory"] == "Russia"

    def test_progress_callback(self, fake_provider):
        events = []
        with patch("iterable.ai.doc.get_provider", return_value=fake_provider):
            doc.generate_blocks(CSV_FIXTURE, blocks=["general"], progress=lambda e: events.append(e.stage))
        assert Stage.COMPLETED in events
        assert Stage.GENERATING in events

    def test_iterable_input(self, fake_provider):
        rows = [{"a": 1, "b": "x"}, {"a": 2, "b": "y"}]
        with patch("iterable.ai.doc.get_provider", return_value=fake_provider):
            result = doc.generate_blocks(rows, blocks=["schema", "statistics"])
        assert result["source"]["type"] == "iterable"
        assert result["blocks"]["statistics"]["data"]["fields"]

    def test_language_localizes_static_labels(self, fake_provider):
        with patch("iterable.ai.doc.get_provider", return_value=fake_provider):
            result = doc.generate_blocks(
                CSV_FIXTURE,
                blocks=["general", "schema", "quality", "statistics"],
                language="Russian",
            )
        md = result["full_document_markdown"]
        # Section headings and labels must be localized, not English.
        assert "## Качество данных" in md
        assert "## Data Quality" not in md
        assert "## Схема данных" in md
        assert "Общая оценка качества" in md
        assert "## Содержание" in md

    def test_quality_rating_localized(self, fake_provider):
        # FakeProvider returns canonical "High"; it must be displayed localized.
        with patch("iterable.ai.doc.get_provider", return_value=fake_provider):
            result = doc.generate_blocks(CSV_FIXTURE, blocks=["quality"], language="Russian")
        md = result["blocks"]["quality"]["markdown"]
        assert "Высокое" in md
        # The structured data keeps the canonical English token.
        assert result["blocks"]["quality"]["data"]["overall"] == "High"

    def test_unknown_language_falls_back_to_english(self, fake_provider):
        with patch("iterable.ai.doc.get_provider", return_value=fake_provider):
            result = doc.generate_blocks(CSV_FIXTURE, blocks=["quality"], language="Klingon")
        assert "## Data Quality" in result["blocks"]["quality"]["markdown"]

    def test_wide_schema_batched(self, fake_provider):
        # 120 columns -> schema generation should batch (>1 structured call for schema).
        rows = [{f"c{i}": i for i in range(120)}]
        with patch("iterable.ai.doc.get_provider", return_value=fake_provider):
            doc.generate_blocks(rows, blocks=["schema"])
        schema_calls = [c for c in fake_provider.calls if "schema" in c]
        assert len(schema_calls) >= 2

    def test_all_columns_described_even_when_model_omits(self):
        """Every column must appear in the schema block, with descriptions, even when
        the provider returns only a subset per request (batching + retry + fill)."""
        import json as _json

        cols = [f"col_{i:02d}" for i in range(54)]
        rows = [{c: i for i, c in enumerate(cols)} for _ in range(3)]
        marker = "inferred types:\n"

        class PartialProvider:
            def generate(self, *a, **k):
                return "x"

            def get_usage_info(self):
                return None

            def get_fields_info(self, fields, language="English"):
                return {f: "d" for f in fields}

            def generate_structured(self, prompt, schema, schema_name="result", **k):
                if "schema" not in schema_name:
                    return {}
                idx = prompt.find(marker)
                obj, _ = _json.JSONDecoder().raw_decode(prompt[idx + len(marker) :])
                names = list(obj.keys())
                # Main batches (>13 cols) omit half; small retry batches return all.
                subset = names if len(names) <= 13 else names[: len(names) // 2]
                return {
                    "fields": [
                        {"name": n, "type": "string", "description": f"desc {n}", "example": "e", "nullable": True}
                        for n in subset
                    ]
                }

        with patch("iterable.ai.doc.get_provider", return_value=PartialProvider()):
            result = doc.generate_blocks(rows, blocks=["schema"])
        fields = result["blocks"]["schema"]["data"]["fields"]
        names = [f["name"] for f in fields]
        assert names == cols  # all present, in order, no duplicates
        assert all(f.get("description") for f in fields)


# ---------------------------------------------------------------------------
# Backward-compatible generate() delegation
# ---------------------------------------------------------------------------


class TestGenerateDelegation:
    def test_generate_with_blocks_markdown(self, fake_provider):
        with patch("iterable.ai.doc.get_provider", return_value=fake_provider):
            result = doc.generate(CSV_FIXTURE, blocks=["general"], format="markdown")
        assert isinstance(result, str)
        assert "Documentation" in result

    def test_generate_with_blocks_json(self, fake_provider):
        with patch("iterable.ai.doc.get_provider", return_value=fake_provider):
            result = doc.generate(CSV_FIXTURE, blocks=["general"], format="json")
        assert isinstance(result, dict)
        assert "blocks" in result

    def test_generate_legacy_unchanged(self):
        with patch("iterable.ai.doc.get_provider") as mock_get_provider:
            from unittest.mock import MagicMock

            provider = MagicMock()
            provider.generate.return_value = "# Legacy doc"
            provider.get_usage_info.return_value = {"total_tokens": 10}
            mock_get_provider.return_value = provider
            result = doc.generate([{"a": 1}], format="markdown")
        assert result == "# Legacy doc"


# ---------------------------------------------------------------------------
# Provider configuration
# ---------------------------------------------------------------------------


class TestProviderConfig:
    def test_resolve_default_provider_env(self, monkeypatch):
        from iterable.ai.providers import resolve_default_provider

        monkeypatch.setenv("LLM_PROVIDER", "openrouter")
        assert resolve_default_provider() == "openrouter"

    def test_resolve_default_provider_default(self, monkeypatch):
        from iterable.ai.providers import resolve_default_provider

        monkeypatch.delenv("LLM_PROVIDER", raising=False)
        assert resolve_default_provider() == "openai"

    def test_openai_compatible_requires_base_url(self, monkeypatch):
        from iterable.ai.providers import OpenAICompatibleProvider

        monkeypatch.delenv("LLM_BASE_URL", raising=False)
        with pytest.raises((ValueError, ImportError)):
            OpenAICompatibleProvider()


class TestStructuredOutputFallback:
    def test_base_generate_structured_parses_json(self):
        from iterable.ai.providers import LLMProvider

        class TextProvider(LLMProvider):
            def generate(self, prompt, model=None, temperature=0.7, max_tokens=None, **kwargs):
                return 'Here is the result: {"title": "X", "topic": "Y"} thanks'

            def get_usage_info(self):
                return None

            def get_fields_info(self, fields, language="English"):
                return {}

        provider = TextProvider()
        result = provider.generate_structured("prompt", {"type": "object"})
        assert result == {"title": "X", "topic": "Y"}
