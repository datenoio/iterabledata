"""Tests for ai.translate_filter and filter AST."""

import pytest

from iterable.ai.filter import apply_ast, ast_to_filter_expr, translate_filter, validate_filter_ast


class TestTranslateFilterDSL:
    def test_simple_comparison(self):
        result = translate_filter("age > 30")
        assert result["source"] == "dsl"
        assert result["ast"]["op"] == "gt"
        assert result["ast"]["field"] == "age"

    def test_and_expression(self):
        result = translate_filter("age > 30 and country = 'US'")
        assert result["ast"]["op"] == "and"

    def test_reject_sql_injection(self):
        with pytest.raises(ValueError, match="disallowed"):
            translate_filter("id = 1; DROP TABLE users")

    def test_reject_multi_statement(self):
        with pytest.raises(ValueError, match="Multi-statement"):
            translate_filter("a = 1; b = 2")

    def test_apply_ast_filters_rows(self):
        rows = [{"age": 25}, {"age": 40}]
        ast = translate_filter("age > 30")["ast"]
        filtered = list(apply_ast(rows, ast))
        assert len(filtered) == 1
        assert filtered[0]["age"] == 40

    def test_validate_unknown_op(self):
        with pytest.raises(ValueError, match="Unknown filter AST"):
            validate_filter_ast({"op": "sql_raw", "field": "x"})

    def test_ast_to_filter_expr(self):
        ast = {"op": "eq", "field": "status", "value": "active"}
        expr = ast_to_filter_expr(ast)
        assert "status" in expr
        assert "active" in expr
