"""Tests for ai.plan_conversion."""

from iterable.ai.plan import plan_conversion


class TestPlanConversion:
    def test_plan_csv_to_jsonl(self):
        plan = plan_conversion("fixtures/2cols6rows.csv", "out.jsonl")
        assert plan["source"]["format"] == "csv"
        assert "steps" in plan
        assert isinstance(plan["warnings"], list)

    def test_plan_readonly_target_warning(self):
        # `.xls` is a read-only format; converting *to* it should warn.
        plan = plan_conversion("fixtures/2cols6rows.csv", "out.xls")
        assert any("read-only" in w.lower() for w in plan["warnings"])

    def test_plan_with_llm_mocked(self):
        from unittest.mock import MagicMock, patch

        with patch("iterable.ai.plan.get_provider") as mock_get:
            mock_provider = MagicMock()
            mock_provider.generate.return_value = '{"steps": [{"action": "llm", "detail": "ok"}]}'
            mock_get.return_value = mock_provider
            plan = plan_conversion(
                "fixtures/2cols6rows.csv",
                "out.jsonl",
                use_llm=True,
                provider="openai",
            )
        assert "llm_notes" in plan
